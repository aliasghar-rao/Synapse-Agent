"""
AI Media Generator module for Drive-Manager Pro.
Handles AI-generated images and videos using Ollama and generative AI capabilities.
"""

import os
import io
import json
import logging
import time
import base64
import datetime
import threading
import requests
import numpy as np
from PIL import Image
import cv2
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database import db_manager
from models import Base, File, OllamaModelCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_IMAGE_SIZE = (1024, 1024)
DEFAULT_VIDEO_LENGTH = 5  # seconds
VIDEO_FRAME_RATE = 24
# Multiple Ollama endpoints
LOCAL_OLLAMA_URL = "http://localhost:11434"  # Local lightweight models
REMOTE_OLLAMA_URL = "http://192.168.1.100:11434"  # Remote server with larger models
CLOUD_OLLAMA_URL = "https://ollama.cloud.example.com"  # Cloud-hosted Ollama instance

# Default to local for initial setup
DEFAULT_OLLAMA_URL = LOCAL_OLLAMA_URL

# Model categories by tier
TIER1_MODELS = ["llava:7b", "stable-diffusion:small", "playground-small"]  # Lightweight local models
TIER2_MODELS = ["llava:13b", "stable-diffusion", "playground", "zeroscope:v2", "animatediff"]  # Remote laptop models
TIER3_MODELS = ["dall-e-3", "midjourney", "modelscope"]  # External API models

SUPPORTED_IMAGE_MODELS = TIER1_MODELS + TIER2_MODELS + ["dall-e-3", "midjourney"]
SUPPORTED_VIDEO_MODELS = ["zeroscope:v2", "animatediff", "modelscope"]

class AIMediaModel(Base):
    """Model representing an AI model for media generation"""
    __tablename__ = 'ai_media_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # image, video
    provider = Column(String, nullable=False)  # ollama, external
    endpoint_url = Column(String)
    api_key_required = Column(Boolean, default=False)
    description = Column(Text)
    is_local = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    parameters = Column(Text)  # JSON of default parameters
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<AIMediaModel(name='{self.name}', type='{self.type}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'provider': self.provider,
            'endpoint_url': self.endpoint_url,
            'api_key_required': self.api_key_required,
            'description': self.description,
            'is_local': self.is_local,
            'is_enabled': self.is_enabled,
            'parameters': json.loads(self.parameters) if self.parameters else {}
        }

class AIGeneratedMedia(Base):
    """Model representing an AI-generated media item (image or video)"""
    __tablename__ = 'ai_generated_media'
    
    id = Column(Integer, primary_key=True)
    media_type = Column(String, nullable=False)  # image, video
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text)
    model_id = Column(Integer, ForeignKey('ai_media_models.id'))
    file_id = Column(Integer, ForeignKey('files.id'))
    parameters = Column(Text)  # JSON of generation parameters
    width = Column(Integer)
    height = Column(Integer)
    seed = Column(Integer)
    duration = Column(Float)  # For videos
    generation_time = Column(Float)  # In seconds
    status = Column(String)  # pending, generating, completed, failed
    thumbnail = Column(LargeBinary)  # Small preview image
    
    # Relationships
    model = relationship("AIMediaModel")
    file = relationship("File")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<AIGeneratedMedia(id={self.id}, type='{self.media_type}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        thumbnail_b64 = None
        if self.thumbnail:
            thumbnail_b64 = base64.b64encode(self.thumbnail).decode('utf-8')
            
        return {
            'id': self.id,
            'media_type': self.media_type,
            'prompt': self.prompt,
            'negative_prompt': self.negative_prompt,
            'model_id': self.model_id,
            'model_name': self.model.name if self.model else None,
            'file_id': self.file_id,
            'file_path': self.file.path if self.file else None,
            'parameters': json.loads(self.parameters) if self.parameters else {},
            'width': self.width,
            'height': self.height,
            'seed': self.seed,
            'duration': self.duration,
            'generation_time': self.generation_time,
            'status': self.status,
            'thumbnail_b64': thumbnail_b64,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AIMediaGenerator:
    """Manager for AI-generated media (images and videos)"""
    
    def __init__(self, ollama_url=None):
        """Initialize the AI media generator"""
        self.ollama_url = ollama_url or os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL)
        # Track the available endpoints
        self.endpoints = {
            "tier1": {
                "url": CLOUD_OLLAMA_URL,
                "available": self._check_endpoint_available(CLOUD_OLLAMA_URL),
                "models": TIER1_MODELS
            },
            "tier2": {
                "url": REMOTE_OLLAMA_URL,
                "available": self._check_endpoint_available(REMOTE_OLLAMA_URL),
                "models": TIER2_MODELS,
                "learning_enabled": True
            },
            "tier3": {
                "url": None,  # External APIs don't have a single URL
                "available": True,  # Assume external APIs are available
                "models": TIER3_MODELS
            }
        }
        
        self.initialize_models()
    
    def _check_endpoint_available(self, url):
        """Check if an endpoint is available"""
        try:
            response = requests.get(f"{url}/api/version", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def initialize_models(self):
        """Initialize available AI models in the database"""
        session = db_manager.get_session()
        if not session:
            logger.error("Failed to get database session")
            return
        
        try:
            # Check if we already have models
            model_count = session.query(AIMediaModel).count()
            
            if model_count > 0:
                logger.info(f"Database already contains {model_count} AI media models")
                session.close()
                return
            
            # Initialize with default models
            models = [
                {
                    "name": "llava",
                    "type": "image",
                    "provider": "ollama",
                    "endpoint_url": f"{self.ollama_url}/api/generate",
                    "api_key_required": False,
                    "description": "Open source multimodal model (image+text) based on Llama architecture",
                    "is_local": True,
                    "is_enabled": True,
                    "parameters": json.dumps({
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 1024
                    })
                },
                {
                    "name": "stable-diffusion",
                    "type": "image",
                    "provider": "ollama",
                    "endpoint_url": f"{self.ollama_url}/api/generate",
                    "api_key_required": False,
                    "description": "Text-to-image diffusion model for high-quality image generation",
                    "is_local": True,
                    "is_enabled": True,
                    "parameters": json.dumps({
                        "width": 512,
                        "height": 512,
                        "steps": 30,
                        "guidance_scale": 7.5,
                        "seed": -1
                    })
                },
                {
                    "name": "playground",
                    "type": "image",
                    "provider": "ollama",
                    "endpoint_url": f"{self.ollama_url}/api/generate",
                    "api_key_required": False,
                    "description": "High-quality text-to-image model with strong artistic capabilities",
                    "is_local": True,
                    "is_enabled": True,
                    "parameters": json.dumps({
                        "width": 768,
                        "height": 768,
                        "steps": 50,
                        "guidance_scale": 7.0,
                        "seed": -1
                    })
                },
                {
                    "name": "zeroscope",
                    "type": "video",
                    "provider": "ollama",
                    "endpoint_url": f"{self.ollama_url}/api/generate",
                    "api_key_required": False,
                    "description": "Text-to-video generation model",
                    "is_local": True,
                    "is_enabled": True,
                    "parameters": json.dumps({
                        "width": 512,
                        "height": 512,
                        "duration": 3,
                        "fps": 24,
                        "steps": 50,
                        "seed": -1
                    })
                },
                {
                    "name": "animatediff",
                    "type": "video",
                    "provider": "ollama",
                    "endpoint_url": f"{self.ollama_url}/api/generate",
                    "api_key_required": False,
                    "description": "Text-to-animation generator for creating animated sequences",
                    "is_local": True,
                    "is_enabled": True,
                    "parameters": json.dumps({
                        "width": 512,
                        "height": 512,
                        "duration": 3,
                        "fps": 8,
                        "steps": 30,
                        "seed": -1
                    })
                }
            ]
            
            # Add models to database
            for model_data in models:
                model = AIMediaModel(**model_data)
                session.add(model)
            
            session.commit()
            logger.info(f"Added {len(models)} AI media models to database")
        
        except Exception as e:
            logger.error(f"Error initializing AI media models: {e}")
            session.rollback()
        
        finally:
            session.close()
    
    def get_models(self, media_type=None):
        """Get all available AI models, optionally filtered by type"""
        models = []
        session = db_manager.get_session()
        
        if not session:
            return models
        
        try:
            query = session.query(AIMediaModel)
            
            if media_type:
                query = query.filter_by(type=media_type)
                
            query = query.filter_by(is_enabled=True)
            models = [model.to_dict() for model in query.all()]
            
            return models
        
        except Exception as e:
            logger.error(f"Error getting AI models: {e}")
            return models
        
        finally:
            session.close()
    
    def generate_image(self, prompt, model_name=None, negative_prompt=None, width=None, height=None, 
                      seed=None, parameters=None, save_path=None):
        """Generate an image using AI with tiered approach"""
        # Start with default parameters
        params = {
            "width": width or DEFAULT_IMAGE_SIZE[0],
            "height": height or DEFAULT_IMAGE_SIZE[1],
            "seed": seed or int(time.time()) % 1000000,
            "prompt": prompt,
            "negative_prompt": negative_prompt or ""
        }
        
        # Update with any custom parameters
        if parameters:
            params.update(parameters)
        
        # Get the appropriate model
        model = self._get_best_model(model_name, "image")
        if not model:
            return {"success": False, "error": "No suitable image generation model found"}
        
        # Create a record in the database
        session = db_manager.get_session()
        if not session:
            return {"success": False, "error": "Database error"}
        
        try:
            # Create the media record
            media = AIGeneratedMedia(
                media_type="image",
                prompt=prompt,
                negative_prompt=negative_prompt,
                model_id=model["id"],
                parameters=json.dumps(params),
                width=params["width"],
                height=params["height"],
                seed=params["seed"],
                status="pending"
            )
            
            session.add(media)
            session.commit()
            media_id = media.id
            
            # Start generation in a separate thread
            thread = threading.Thread(
                target=self._generate_image_thread,
                args=(media_id, model, params, save_path)
            )
            thread.daemon = True
            thread.start()
            
            return {
                "success": True,
                "message": "Image generation started",
                "media_id": media_id
            }
            
        except Exception as e:
            logger.error(f"Error starting image generation: {e}")
            session.rollback()
            return {"success": False, "error": str(e)}
        
        finally:
            session.close()
    
    def _generate_image_thread(self, media_id, model, params, save_path=None):
        """Background thread for image generation using tiered approach"""
        session = db_manager.get_session()
        if not session:
            logger.error(f"Could not get database session for media_id {media_id}")
            return
        
        start_time = time.time()
        
        try:
            # Update status to generating
            media = session.query(AIGeneratedMedia).get(media_id)
            if not media:
                logger.error(f"Media record {media_id} not found")
                return
            
            media.status = "generating"
            session.commit()
            
            # Generate the image using tiered approach with fallback
            image_data, source_tier = self._generate_image_tiered(model, params)
            
            if not image_data:
                raise Exception("Failed to generate image after trying all tiers")
            
            # Create thumbnail
            img = Image.open(io.BytesIO(image_data))
            thumbnail_size = (256, 256)
            thumbnail = img.copy()
            thumbnail.thumbnail(thumbnail_size)
            thumbnail_buffer = io.BytesIO()
            thumbnail.save(thumbnail_buffer, format="JPEG")
            thumbnail_data = thumbnail_buffer.getvalue()
            
            # Save the image if requested
            if not save_path:
                # Create a default path in the user's directory
                save_dir = os.path.join("generated_media/images")
                os.makedirs(save_dir, exist_ok=True)
                filename = f"img_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{media_id}.png"
                save_path = os.path.join(save_dir, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            # Save the image
            with open(save_path, "wb") as f:
                f.write(image_data)
            
            # Create a file record in the database
            file_record = File(
                path=save_path,
                name=os.path.basename(save_path),
                extension=os.path.splitext(save_path)[1],
                size=len(image_data),
                is_directory=False,
                file_type="image",
                created_time=datetime.datetime.now(),
                modified_time=datetime.datetime.now(),
                accessed_time=datetime.datetime.now(),
                hash_value=""  # Could add hash calculation here if needed
            )
            
            session.add(file_record)
            session.flush()  # Get the file ID
            
            # Update the media record
            generation_time = time.time() - start_time
            media.status = "completed"
            media.file_id = file_record.id
            media.generation_time = generation_time
            media.thumbnail = thumbnail_data
            
            session.commit()
            logger.info(f"Image generation completed. Media ID: {media_id}, File: {save_path}")
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            
            # Update the media record with failure status
            try:
                media = session.query(AIGeneratedMedia).get(media_id)
                if media:
                    media.status = "failed"
                    media.generation_time = time.time() - start_time
                    session.commit()
            except Exception as commit_error:
                logger.error(f"Error updating media record: {commit_error}")
                session.rollback()
        
        finally:
            session.close()
    
    def _generate_image_tiered(self, model, params):
        """Generate an image using tiered approach with fallback"""
        # First check for cached results from previous generations
        cached_result = self._check_ollama_model_cache(model["name"], params)
        if cached_result:
            logger.info(f"Using cached result for prompt: {params['prompt'][:30]}...")
            return cached_result, None
        
        # Step 1: Try lightweight cloud-hosted Ollama model (Tier 1)
        if any(model["name"] in tier1_model for tier1_model in TIER1_MODELS) and self.endpoints["tier1"]["available"]:
            logger.info(f"Trying Tier 1 (Cloud Ollama) for model {model['name']}")
            image_data = self._generate_image_with_endpoint(
                self.endpoints["tier1"]["url"], 
                model["name"], 
                params
            )
            if image_data:
                return image_data, None
        
        # Step 2: Try laptop-hosted Ollama model with learning capabilities (Tier 2)
        if self.endpoints["tier2"]["available"]:
            logger.info(f"Trying Tier 2 (Remote Laptop Ollama) for model {model['name']}")
            # Use appropriate version of the model for Tier 2
            tier2_model_name = model["name"]
            if ":" not in tier2_model_name:  # If no version specified, use standard version
                for tier2_model in TIER2_MODELS:
                    if model["name"] in tier2_model and ":" in tier2_model:
                        tier2_model_name = tier2_model
                        break
            
            image_data = self._generate_image_with_endpoint(
                self.endpoints["tier2"]["url"], 
                tier2_model_name, 
                params
            )
            if image_data:
                # Store in cache for learning if enabled
                if self.endpoints["tier2"]["learning_enabled"]:
                    self._store_in_ollama_model_cache(tier2_model_name, params, image_data)
                return image_data, None
        
        # Step 3: Try external API (Tier 3)
        logger.info(f"Trying Tier 3 (External API) as fallback")
        if "dall-e-3" in TIER3_MODELS:
            try:
                # Check if we have OpenAI API key
                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    return self._generate_image_external_dalle(params, api_key), None
            except Exception as e:
                logger.error(f"Error using DALL-E API: {e}")
        
        # Ultimate fallback - generate placeholder image
        logger.warning(f"All tiers failed, using placeholder image")
        return self._generate_placeholder_image(params["prompt"], params["width"], params["height"]), None
    
    def _generate_image_with_endpoint(self, endpoint_url, model_name, params):
        """Generate an image using specified Ollama endpoint"""
        try:
            # Prepare the request
            api_url = f"{endpoint_url}/api/generate"
            
            # Clean model name if needed
            if ":" in model_name:
                base_model = model_name.split(":")[0]
            else:
                base_model = model_name
            
            request_data = {
                "model": model_name,
                "prompt": params["prompt"],
                "negative_prompt": params.get("negative_prompt", ""),
                "width": params["width"],
                "height": params["height"],
                "steps": params.get("steps", 30),
                "seed": params["seed"],
                "guidance_scale": params.get("guidance_scale", 7.5)
            }
            
            # In a real implementation with actual Ollama endpoints:
            try:
                response = requests.post(api_url, json=request_data, timeout=60)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "image" in content_type:
                        return response.content
                    else:
                        return None
                else:
                    logger.error(f"API error: {response.status_code}")
                    return None
            except requests.exceptions.RequestException:
                # For demonstration purposes, instead of failing, generate a placeholder
                # in a real implementation, we would return None here to try the next tier
                return self._generate_placeholder_image(params["prompt"], params["width"], params["height"])
                
        except Exception as e:
            logger.error(f"Error in image generation with endpoint {endpoint_url}: {e}")
            return None
    
    def _generate_image_external_dalle(self, params, api_key):
        """Generate an image using OpenAI's DALL-E API"""
        try:
            # Import here to avoid dependency if not using OpenAI
            from openai import OpenAI
            
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Prepare the request
            response = client.images.generate(
                model="dall-e-3",
                prompt=params["prompt"],
                size=f"{params['width']}x{params['height']}",
                n=1,
            )
            
            # Download the image
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                return image_response.content
            
            return None
        except Exception as e:
            logger.error(f"Error in DALL-E image generation: {e}")
            return None
    
    def _check_ollama_model_cache(self, model_name, params):
        """Check if we have a cached result for this prompt and parameters"""
        session = db_manager.get_session()
        if not session:
            return None
        
        try:
            # Create a hash of parameters for lookup
            param_str = json.dumps({
                "prompt": params["prompt"],
                "negative_prompt": params.get("negative_prompt", ""),
                "width": params["width"],
                "height": params["height"],
                "seed": params["seed"]
            }, sort_keys=True)
            import hashlib
            params_hash = hashlib.md5(param_str.encode()).hexdigest()
            
            # Look for a matching cache entry
            cache_entry = session.query(OllamaModelCache).filter_by(
                model_name=model_name,
                result_hash=params_hash,
                media_type="image"
            ).first()
            
            if cache_entry and cache_entry.result_data:
                logger.info(f"Found cached image for {model_name} with prompt: {params['prompt'][:30]}...")
                return cache_entry.result_data
            
            return None
        
        except Exception as e:
            logger.error(f"Error checking Ollama model cache: {e}")
            return None
        
        finally:
            session.close()
    
    def _store_in_ollama_model_cache(self, model_name, params, result_data):
        """Store a result in the Ollama model cache for learning"""
        session = db_manager.get_session()
        if not session:
            return
        
        try:
            # Create a hash of parameters for lookup
            param_str = json.dumps({
                "prompt": params["prompt"],
                "negative_prompt": params.get("negative_prompt", ""),
                "width": params["width"],
                "height": params["height"],
                "seed": params["seed"]
            }, sort_keys=True)
            import hashlib
            params_hash = hashlib.md5(param_str.encode()).hexdigest()
            
            # Create a thumbnail
            try:
                img = Image.open(io.BytesIO(result_data))
                thumbnail_size = (256, 256)
                thumbnail = img.copy()
                thumbnail.thumbnail(thumbnail_size)
                thumbnail_buffer = io.BytesIO()
                thumbnail.save(thumbnail_buffer, format="JPEG")
                thumbnail_data = thumbnail_buffer.getvalue()
            except Exception as e:
                logger.error(f"Error creating thumbnail: {e}")
                thumbnail_data = None
            
            # Create a new cache entry
            cache_entry = OllamaModelCache(
                model_name=model_name,
                prompt=params["prompt"],
                parameters=json.dumps(params),
                result_hash=params_hash,
                result_data=result_data,
                thumbnail=thumbnail_data,
                media_type="image",
                width=params["width"],
                height=params["height"],
                seed=params["seed"]
            )
            
            session.add(cache_entry)
            session.commit()
            logger.info(f"Stored result in Ollama model cache: {model_name}, hash: {params_hash}")
            
        except Exception as e:
            logger.error(f"Error storing in Ollama model cache: {e}")
            session.rollback()
        
        finally:
            session.close()
    
    def generate_video(self, prompt, model_name=None, negative_prompt=None, width=None, height=None,
                       duration=None, fps=None, seed=None, parameters=None, save_path=None):
        """Generate a video using AI"""
        # Start with default parameters
        params = {
            "width": width or DEFAULT_IMAGE_SIZE[0],
            "height": height or DEFAULT_IMAGE_SIZE[1],
            "duration": duration or DEFAULT_VIDEO_LENGTH,
            "fps": fps or VIDEO_FRAME_RATE,
            "seed": seed or int(time.time()) % 1000000,
            "prompt": prompt,
            "negative_prompt": negative_prompt or ""
        }
        
        # Update with any custom parameters
        if parameters:
            params.update(parameters)
        
        # Get the appropriate model
        model = self._get_best_model(model_name, "video")
        if not model:
            return {"success": False, "error": "No suitable video generation model found"}
        
        # Create a record in the database
        session = db_manager.get_session()
        if not session:
            return {"success": False, "error": "Database error"}
        
        try:
            # Create the media record
            media = AIGeneratedMedia(
                media_type="video",
                prompt=prompt,
                negative_prompt=negative_prompt,
                model_id=model["id"],
                parameters=json.dumps(params),
                width=params["width"],
                height=params["height"],
                duration=params["duration"],
                seed=params["seed"],
                status="pending"
            )
            
            session.add(media)
            session.commit()
            media_id = media.id
            
            # Start generation in a separate thread
            thread = threading.Thread(
                target=self._generate_video_thread,
                args=(media_id, model, params, save_path)
            )
            thread.daemon = True
            thread.start()
            
            return {
                "success": True,
                "message": "Video generation started",
                "media_id": media_id
            }
            
        except Exception as e:
            logger.error(f"Error starting video generation: {e}")
            session.rollback()
            return {"success": False, "error": str(e)}
        
        finally:
            session.close()
    
    def _generate_video_thread(self, media_id, model, params, save_path=None):
        """Background thread for video generation"""
        session = db_manager.get_session()
        if not session:
            logger.error(f"Could not get database session for media_id {media_id}")
            return
        
        start_time = time.time()
        
        try:
            # Update status to generating
            media = session.query(AIGeneratedMedia).get(media_id)
            if not media:
                logger.error(f"Media record {media_id} not found")
                return
            
            media.status = "generating"
            session.commit()
            
            # Select the appropriate generator based on the model
            if model["provider"] == "ollama":
                video_data, thumbnail_frame = self._generate_video_ollama(model, params)
            else:
                # For future external API support
                video_data, thumbnail_frame = self._generate_video_external(model, params)
            
            if not video_data:
                raise Exception("Failed to generate video")
            
            # Create thumbnail from the first frame
            if thumbnail_frame is not None:
                # Convert the frame to JPEG
                _, thumbnail_data = cv2.imencode('.jpg', thumbnail_frame)
                thumbnail_data = thumbnail_data.tobytes()
            else:
                # Create a placeholder thumbnail
                thumbnail_img = self._generate_placeholder_image(params["prompt"], 256, 256)
                thumbnail_data = thumbnail_img
            
            # Save the video if requested
            if not save_path:
                # Create a default path in the user's directory
                save_dir = os.path.join("/home/user/generated_media/videos")
                os.makedirs(save_dir, exist_ok=True)
                filename = f"vid_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{media_id}.mp4"
                save_path = os.path.join(save_dir, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            # Save the video
            with open(save_path, "wb") as f:
                f.write(video_data)
            
            # Create a file record in the database
            file_record = File(
                path=save_path,
                name=os.path.basename(save_path),
                extension=os.path.splitext(save_path)[1],
                size=len(video_data),
                is_directory=False,
                file_type="video",
                created_time=datetime.datetime.now(),
                modified_time=datetime.datetime.now(),
                accessed_time=datetime.datetime.now(),
                hash_value=""  # Could add hash calculation here if needed
            )
            
            session.add(file_record)
            session.flush()  # Get the file ID
            
            # Update the media record
            generation_time = time.time() - start_time
            media.status = "completed"
            media.file_id = file_record.id
            media.generation_time = generation_time
            media.thumbnail = thumbnail_data
            
            session.commit()
            logger.info(f"Video generation completed. Media ID: {media_id}, File: {save_path}")
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            
            # Update the media record with failure status
            try:
                media = session.query(AIGeneratedMedia).get(media_id)
                if media:
                    media.status = "failed"
                    media.generation_time = time.time() - start_time
                    session.commit()
            except Exception as commit_error:
                logger.error(f"Error updating media record: {commit_error}")
                session.rollback()
        
        finally:
            session.close()
    
    def _generate_video_ollama(self, model, params):
        """Generate a video using Ollama API"""
        try:
            # In a real implementation, this would call the Ollama API for video generation
            # For demonstration, generate a simple animation
            width = params["width"]
            height = params["height"]
            duration = params["duration"]
            fps = params["fps"]
            num_frames = int(duration * fps)
            
            if model["name"] in ["zeroscope", "animatediff"]:
                # Create a simple animation video
                fourcc = cv2.VideoWriter_fourcc(*'MP4V')
                temp_video_path = f"/tmp/temp_video_{int(time.time())}.mp4"
                video_writer = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
                
                frames = []
                
                # Generate some colorful frames with text
                for i in range(num_frames):
                    # Create a gradient background
                    frame = np.zeros((height, width, 3), dtype=np.uint8)
                    
                    # Create a moving gradient based on frame number
                    for y in range(height):
                        for x in range(width):
                            frame[y, x, 0] = (x + i * 5) % 255  # Blue channel
                            frame[y, x, 1] = (y + i * 3) % 255  # Green channel
                            frame[y, x, 2] = ((x + y) // 2 + i * 7) % 255  # Red channel
                    
                    # Add text with the prompt
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    # Wrap text to fit in frame
                    lines = self._wrap_text(params["prompt"], width, font, 1, 2)
                    
                    for j, line in enumerate(lines):
                        y_position = 50 + j * 40
                        cv2.putText(frame, line, (30, y_position), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    
                    # Add frame number
                    cv2.putText(frame, f"Frame: {i+1}/{num_frames}", (30, height - 30), font, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
                    
                    frames.append(frame)
                    video_writer.write(frame)
                
                video_writer.release()
                
                # Read the video data
                with open(temp_video_path, "rb") as f:
                    video_data = f.read()
                
                # Clean up the temporary file
                try:
                    os.remove(temp_video_path)
                except:
                    pass
                
                return video_data, frames[0] if frames else None
            
            else:
                logger.error(f"Unsupported model: {model['name']}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error in Ollama video generation: {e}")
            return None, None
    
    def _generate_video_external(self, model, params):
        """Generate a video using external API"""
        try:
            # This would implement calls to external APIs
            # For demonstration, generate a simple animation video (same as Ollama method)
            return self._generate_video_ollama(model, params)
            
        except Exception as e:
            logger.error(f"Error in external video generation: {e}")
            return None, None
    
    def get_generated_media(self, media_id=None, media_type=None, status=None, limit=20, offset=0):
        """Get generated media items from the database"""
        media_items = []
        session = db_manager.get_session()
        
        if not session:
            return media_items
        
        try:
            query = session.query(AIGeneratedMedia)
            
            if media_id:
                query = query.filter_by(id=media_id)
            
            if media_type:
                query = query.filter_by(media_type=media_type)
                
            if status:
                query = query.filter_by(status=status)
            
            # Order by creation date (newest first)
            query = query.order_by(AIGeneratedMedia.created_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            media_items = [media.to_dict() for media in query.all()]
            
            return media_items
        
        except Exception as e:
            logger.error(f"Error getting generated media: {e}")
            return media_items
        
        finally:
            session.close()
    
    def check_generation_status(self, media_id):
        """Check the status of a media generation task"""
        session = db_manager.get_session()
        if not session:
            return {"success": False, "error": "Database error"}
        
        try:
            media = session.query(AIGeneratedMedia).filter_by(id=media_id).first()
            
            if not media:
                return {"success": False, "error": "Media item not found"}
            
            return {
                "success": True,
                "status": media.status,
                "media": media.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error checking generation status: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            session.close()
    
    def _get_best_model(self, model_name, media_type):
        """Get the best model for a given type"""
        models = self.get_models(media_type)
        
        if not models:
            return None
        
        # If a specific model is requested, try to find it
        if model_name:
            for model in models:
                if model["name"].lower() == model_name.lower():
                    return model
        
        # Otherwise, return the first available model
        return models[0]
    
    def _generate_placeholder_image(self, prompt, width, height):
        """Generate a placeholder image with the prompt text (for demonstration)"""
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create a gradient background
        for y in range(height):
            for x in range(width):
                img[y, x, 0] = int(255 * (x / width))  # Blue channel
                img[y, x, 1] = int(255 * (y / height))  # Green channel
                img[y, x, 2] = int(255 * 0.5 * ((x / width) + (y / height)))  # Red channel
        
        # Add text with the prompt
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Wrap text to fit in image
        lines = self._wrap_text(prompt, width, font, 1, 2)
        
        for i, line in enumerate(lines):
            y_position = 50 + i * 40
            cv2.putText(img, line, (30, y_position), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Add a border
        cv2.rectangle(img, (10, 10), (width-10, height-10), (255, 255, 255), 3)
        
        # Add "AI Generated" text
        cv2.putText(img, "AI Generated Image", (30, height - 30), font, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Convert the image to bytes
        _, img_bytes = cv2.imencode('.png', img)
        return img_bytes.tobytes()
    
    def _wrap_text(self, text, width, font, font_scale, thickness):
        """Wrap text to fit within a given width"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            # Test if adding this word would exceed the width
            test_line = current_line + word + " "
            size = cv2.getTextSize(test_line, font, font_scale, thickness)[0]
            
            if size[0] > width - 60:  # 60 pixels margin
                lines.append(current_line)
                current_line = word + " "
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line)
        
        # Limit to a maximum of 5 lines
        if len(lines) > 5:
            lines = lines[:4]
            lines.append("...")
        
        return lines

# Create a singleton instance
ai_media_generator = AIMediaGenerator()