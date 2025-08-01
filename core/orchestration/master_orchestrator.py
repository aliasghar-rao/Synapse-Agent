"""
Master Orchestrator - No Prompt Mechanism
Advanced language detection and prompt generation system
Handles multilingual queries with cultural context
"""

import re
import json
import structlog
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
from pathlib import Path

from config.settings import get_settings
from core.language_detection import LanguageDetector
from core.cultural_context import CulturalContextEngine
from core.prompt_generator import PromptEngine

logger = structlog.get_logger()
settings = get_settings()

@dataclass
class MasterQuery:
    """Master query object with full context"""
    original_input: str
    detected_language: str
    language_confidence: float
    cultural_context: Dict[str, Any]
    ambiguity_flags: List[str]
    generated_prompt: str
    internal_system_prompt: str
    cultural_metadata: Dict[str, Any]
    timestamp: datetime

class MasterOrchestrator:
    """Master orchestrator for no-prompt mechanism"""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.cultural_engine = CulturalContextEngine()
        self.prompt_engine = PromptEngine()
        self.ambiguity_resolver = AmbiguityResolver()
        
    async def process_user_input(self, user_input: str) -> MasterQuery:
        """Process user input without requiring explicit prompts"""
        try:
            logger.info("processing_user_input", input=user_input)
            
            # Step 1: Language Detection
            language_result = await self._detect_language(user_input)
            
            # Step 2: Cultural Context Analysis
            cultural_context = await self._analyze_cultural_context(
                user_input, 
                language_result
            )
            
            # Step 3: Ambiguity Detection
            ambiguity_flags = await self._detect_ambiguities(
                user_input,
                language_result,
                cultural_context
            )
            
            # Step 4: Prompt Generation
            internal_prompt = await self._generate_internal_prompt(
                user_input,
                language_result,
                cultural_context,
                ambiguity_flags
            )
            
            # Step 5: Cultural Metadata
            cultural_metadata = await self._extract_cultural_metadata(
                user_input,
                cultural_context
            )
            
            master_query = MasterQuery(
                original_input=user_input,
                detected_language=language_result['language'],
                language_confidence=language_result['confidence'],
                cultural_context=cultural_context,
                ambiguity_flags=ambiguity_flags,
                generated_prompt=internal_prompt['system_prompt'],
                internal_system_prompt=internal_prompt['full_prompt'],
                cultural_metadata=cultural_metadata,
                timestamp=datetime.now()
            )
            
            logger.info("master_query_generated", 
                       query_id=self._generate_query_id(),
                       language=language_result['language'],
                       confidence=language_result['confidence'],
                       ambiguities=len(ambiguity_flags))
            
            return master_query
            
        except Exception as e:
            logger.error("master_orchestrator_error", error=str(e))
            raise
    
    async def _detect_language(self, text: str) -> Dict[str, Any]:
        """Advanced language detection with cultural context"""
        
        # Primary language detection
        detected = await self.language_detector.detect(text)
        
        # Cultural language variants
        cultural_hints = self._extract_cultural_language_hints(text)
        
        # Confidence adjustment based on cultural context
        confidence = detected['confidence']
        if cultural_hints['cultural_match']:
            confidence = min(confidence * 1.2, 1.0)
        
        return {
            'language': detected['language'],
            'confidence': confidence,
            'cultural_hints': cultural_hints,
            'script_type': detected.get('script', 'latin')
        }
    
    async def _analyze_cultural_context(self, text: str, language_result: Dict) -> Dict[str, Any]:
        """Deep cultural context analysis"""
        
        cultural_context = await self.cultural_engine.analyze(text, language_result)
        
        # Pakistani cultural context
        pakistani_context = self._extract_pakistani_context(text)
        
        # Religious/cultural markers
        religious_markers = self._detect_religious_markers(text)
        
        # Social context
        social_context = self._extract_social_context(text)
        
        return {
            'primary_culture': cultural_context.get('primary_culture', 'general'),
            'pakistani_context': pakistani_context,
            'religious_markers': religious_markers,
            'social_context': social_context,
            'formality_level': cultural_context.get('formality', 'neutral'),
            'regional_dialect': cultural_context.get('dialect', 'standard')
        }
    
    async def _detect_ambiguities(self, text: str, language: Dict, context: Dict) -> List[str]:
        """Detect language ambiguities within same language"""
        
        ambiguities = []
        
        # Word sense disambiguation
        word_senses = await self._disambiguate_word_senses(text, context)
        if word_senses.get('ambiguous_terms'):
            ambiguities.extend(word_senses['ambiguous_terms'])
        
        # Contextual ambiguity
        contextual_ambiguities = await self._detect_contextual_ambiguities(text)
        ambiguities.extend(contextual_ambiguities)
        
        # Cultural ambiguity
        cultural_ambiguities = await self._detect_cultural_ambiguities(text, context)
        ambiguities.extend(cultural_ambiguities)
        
        return ambiguities
    
    async def _generate_internal_prompt(self, user_input: str, language: Dict, 
                                      context: Dict, ambiguities: List[str]) -> Dict[str, str]:
        """Generate robust internal prompts without user intervention"""
        
        # Base system prompt
        base_prompt = self._build_base_system_prompt(language, context)
        
        # Task-specific prompt
        task_prompt = await self._determine_task_type_prompt(user_input, context)
        
        # Cultural integration
        cultural_prompt = self._build_cultural_integration_prompt(context)
        
        # Ambiguity resolution
        ambiguity_resolution = self._build_ambiguity_resolution_prompt(ambiguities)
        
        # Final internal prompt
        full_prompt = f"""
{base_prompt}

{task_prompt}

{cultural_prompt}

{ambiguity_resolution}

USER INPUT: {user_input}

RESPONSE REQUIREMENTS:
- Address all detected ambiguities
- Apply appropriate cultural context
- Provide comprehensive analysis
- Include cultural sensitivity considerations
"""
        
        return {
            'system_prompt': base_prompt,
            'task_prompt': task_prompt,
            'cultural_prompt': cultural_prompt,
            'ambiguity_resolution': ambiguity_resolution,
            'full_prompt': full_prompt.strip()
        }
    
    def _build_base_system_prompt(self, language: Dict, context: Dict) -> str:
        """Build base system prompt for internal processing"""
        
        return f"""
You are Ali Orchestration Core - an advanced AI system with cultural intelligence.

LANGUAGE DETECTED: {language['language']} (confidence: {language['confidence']})
CULTURAL CONTEXT: {context['primary_culture']}
REGIONAL DIALECT: {context.get('regional_dialect', 'standard')}
FORMALITY LEVEL: {context.get('formality_level', 'neutral')}

CULTURAL GUIDELINES:
- Respect Pakistani cultural values and sensitivities
- Consider Islamic cultural markers and religious context
- Account for regional linguistic variations (Urdu, Punjabi, etc.)
- Maintain appropriate formality levels based on cultural context
- Be sensitive to social and religious nuances

PROCESSING APPROACH:
- Analyze input comprehensively
- Resolve any linguistic ambiguities
- Apply cultural context appropriately
- Provide culturally sensitive responses
- Ensure complete understanding of user intent
"""
    
    async def _determine_task_type_prompt(self, user_input: str, context: Dict) -> str:
        """Determine appropriate task type based on input"""
        
        # Task type detection
        task_indicators = {
            'swarm_coordination': ['multi-agent', 'collaborate', 'swarm', 'team'],
            'liquid_emergence': ['emergence', 'pattern', 'chaos', 'proof'],
            'ingestion_processing': ['media', 'audio', 'video', 'document', 'analyze'],
            'neural_memory': ['memory', 'remember', 'store', 'recall'],
            'self_learning': ['learn', 'improve', 'evolve', 'adapt']
        }
        
        detected_tasks = []
        user_input_lower = user_input.lower()
        
        for task_type, indicators in task_indicators.items():
            if any(indicator in user_input_lower for indicator in indicators):
                detected_tasks.append(task_type)
        
        # Default to comprehensive processing if no specific task detected
        if not detected_tasks:
            detected_tasks = ['comprehensive_analysis']
        
        return f"""
DETECTED TASK TYPE: {', '.join(detected_tasks)}
PROCESSING APPROACH: Apply appropriate AI head(s) based on detected intent
"""
    
    def _build_cultural_integration_prompt(self, context: Dict) -> str:
        """Build cultural integration prompt"""
        
        pakistani_context = context.get('pakistani_context', {})
        religious_markers = context.get('religious_markers', [])
        
        return f"""
PAKISTANI CULTURAL CONTEXT:
- Regional dialect: {pakistani_context.get('dialect', 'standard')}
- Cultural formality: {pakistani_context.get('formality', 'neutral')}
- Religious considerations: {', '.join(religious_markers) if religious_markers else 'general'}

CULTURAL PROCESSING GUIDELINES:
- Apply appropriate cultural context
- Respect Pakistani social norms
- Consider Islamic cultural markers
- Maintain linguistic authenticity
"""
    
    def _build_ambiguity_resolution_prompt(self, ambiguities: List[str]) -> str:
        """Build ambiguity resolution prompt"""
        
        if not ambiguities:
            return "No linguistic ambiguities detected. Proceed with standard processing."
        
        return f"""
DETECTED AMBIGUITIES: {len(ambiguities)}
AMBIGUOUS TERMS: {', '.join(ambiguities)}

AMBIGUITY RESOLUTION STRATEGY:
- Provide comprehensive explanations for ambiguous terms
- Offer multiple interpretations when appropriate
- Include cultural context for disambiguation
- Ensure complete understanding of user intent
"""
    
    async def _extract_cultural_metadata(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract cultural metadata for processing"""
        
        return {
            'processing_timestamp': datetime.now().isoformat(),
            'cultural_confidence': context.get('cultural_confidence', 0.8),
            'linguistic_features': await self._extract_linguistic_features(text),
            'cultural_markers': context.get('cultural_markers', []),
            'ambiguity_resolution': await self._resolve_ambiguities(text, context),
            'internal_processing_notes': 'Generated via Master Orchestrator'
        }
    
    def _extract_cultural_language_hints(self, text: str) -> Dict[str, Any]:
        """Extract cultural language hints from text"""
        
        hints = {
            'cultural_match': False,
            'pakistani_english_indicators': [],
            'urdu_script_indicators': [],
            'punjabi_indicators': [],
            'religious_markers': []
        }
        
        # Pakistani English indicators
        pakistani_patterns = [
            r'\b(bhai|behen|sahab|ji)\b',
            r'\b(inshallah|mashallah|alhamdulillah)\b',
            r'\b(lakh|crore|paisa)\b'
        ]
        
        for pattern in pakistani_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                hints['pakistani_english_indicators'].extend(matches)
                hints['cultural_match'] = True
        
        return hints
    
    def _extract_pakistani_context(self, text: str) -> Dict[str, Any]:
        """Extract Pakistani cultural context"""
        
        return {
            'dialect': self._detect_pakistani_dialect(text),
            'formality': self._detect_formality_level(text),
            'cultural_markers': self._extract_pakistani_markers(text),
            'religious_context': self._detect_religious_context(text)
        }
    
    def _detect_pakistani_dialect(self, text: str) -> str:
        """Detect Pakistani dialect/regional variation"""
        
        # Dialect indicators
        dialects = {
            'punjabi': ['punjabi', 'lahore', 'punjab', 'balle', 'shukriya'],
            'urdu': ['urdu', 'karachi', 'islamabad', 'meharbani', 'shukriya'],
            'sindhi': ['sindhi', 'karachi', 'hyderabad', 'sindh'],
            'pashto': ['pashto', 'peshawar', 'kpk', 'pakhtoon'],
            'balochi': ['balochi', 'quetta', 'balochistan']
        }
        
        text_lower = text.lower()
        for dialect, indicators in dialects.items():
            if any(indicator in text_lower for indicator in indicators):
                return dialect
        
        return 'standard'
    
    def _detect_formality_level(self, text: str) -> str:
        """Detect formality level based on cultural context"""
        
        formal_indicators = ['please', 'kindly', 'respectfully', 'sir', 'madam']
        informal_indicators = ['hey', 'hi', 'yo', 'bro', 'dude']
        
        text_lower = text.lower()
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in text_lower)
        informal_count = sum(1 for indicator in informal_indicators if indicator in text_lower)
        
        if formal_count > informal_count:
            return 'formal'
        elif informal_count > formal_count:
            return 'informal'
        else:
            return 'neutral'
    
    def _extract_pakistani_markers(self, text: str) -> List[str]:
        """Extract Pakistani cultural markers"""
        
        markers = []
        
        # Religious markers
        religious_terms = ['allah', 'muhammad', 'islam', 'muslim', 'quran', 'hadith']
        for term in religious_terms:
            if term in text.lower():
                markers.append(f'religious_{term}')
        
        # Cultural terms
        cultural_terms = ['biryani', 'shalwar', 'kameez', 'mehndi', 'eid', 'ramadan']
        for term in cultural_terms:
            if term in text.lower():
                markers.append(f'cultural_{term}')
        
        return markers
    
    def _detect_religious_context(self, text: str) -> Dict[str, Any]:
        """Detect religious context"""
        
        religious_markers = {
            'islamic_references': [],
            'prayer_times': False,
            'halal_haram': False,
            'islamic_greetings': False
        }
        
        islamic_terms = {
            'prayer_times': ['fajr', 'zuhr', 'asr', 'maghrib', 'isha'],
            'halal_haram': ['halal', 'haram', 'makruh'],
            'greetings': ['assalamualaikum', 'mashallah', 'inshallah', 'alhamdulillah']
        }
        
        text_lower = text.lower()
        
        for category, terms in islamic_terms.items():
            for term in terms:
                if term in text_lower:
                    if category == 'greetings':
                        religious_markers['islamic_greetings'] = True
                    else:
                        religious_markers[f'{category}'].append(term)
        
        return religious_markers
    
    def _generate_query_id(self) -> str:
        """Generate unique query ID"""
        return f"master_query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    async def _extract_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Extract linguistic features for processing"""
        
        return {
            'length': len(text),
            'word_count': len(text.split()),
            'sentence_count': text.count('.') + text.count('!') + text.count('?'),
            'complexity_score': len(set(text.lower().split())) / len(text.split()) if text.split() else 0,
            'cultural_density': len(self._extract_pakistani_markers(text)),
            'linguistic_patterns': await self._analyze_linguistic_patterns(text)
        }
    
    async def _analyze_linguistic_patterns(self, text: str) -> Dict[str, Any]:
        """Analyze linguistic patterns"""
        
        return {
            'sentence_structure': self._analyze_sentence_structure(text),
            'vocabulary_level': self._analyze_vocabulary_level(text),
            'cultural_integrations': self._analyze_cultural_integrations(text),
            'ambiguity_patterns': self._analyze_ambiguity_patterns(text)
        }
    
    def _analyze_sentence_structure(self, text: str) -> Dict[str, Any]:
        """Analyze sentence structure"""
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            'sentence_count': len(sentences),
            'average_sentence_length': sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0,
            'complexity_indicators': len([s for s in sentences if len(s.split()) > 20])
        }
    
    def _analyze_vocabulary_level(self, text: str) -> Dict[str, Any]:
        """Analyze vocabulary level"""
        
        words = text.lower().split()
        unique_words = set(words)
        
        return {
            'unique_word_ratio': len(unique_words) / len(words) if words else 0,
            'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'cultural_word_density': len(self._extract_pakistani_markers(text)) / len(words) if words else 0
        }
    
    def _analyze_cultural_integrations(self, text: str) -> Dict[str, Any]:
        """Analyze cultural integrations"""
        
        return {
            'cultural_markers': self._extract_pakistani_markers(text),
            'cultural_context_strength': len(self._extract_pakistani_markers(text)),
            'linguistic_cultural_blend': self._assess_cultural_linguistic_blend(text)
        }
    
    def _analyze_ambiguity_patterns(self, text: str) -> Dict[str, Any]:
        """Analyze ambiguity patterns"""
        
        return {
            'homograph_detection': self._detect_homographs(text),
            'contextual_ambiguities': self._detect_contextual_ambiguities(text),
            'cultural_ambiguities': self._detect_cultural_ambiguities(text, {})
        }
    
    def _assess_cultural_linguistic_blend(self, text: str) -> float:
        """Assess blend of cultural and linguistic elements"""
        
        cultural_markers = len(self._extract_pakistani_markers(text))
        total_words = len(text.split())
        
        return cultural_markers / total_words if total_words > 0 else 0
    
    def _detect_homographs(self, text: str) -> List[str]:
        """Detect homographs in text"""
        
        # Common homographs in Pakistani English
        homographs = [
            'bark', 'bat', 'bank', 'bear', 'spring', 'well', 'fair',
            'lie', 'tear', 'lead', 'wind', 'close', 'desert', 'object'
        ]
        
        found_homographs = []
        text_lower = text.lower()
        
        for homograph in homographs:
            if homograph in text_lower:
                found_homographs.append(homograph)
        
        return found_homographs
    
    async def _resolve_ambiguities(self, text: str, context: Dict) -> Dict[str, Any]:
        """Resolve detected ambiguities"""
        
        return {
            'resolution_strategy': 'contextual_analysis',
            'cultural_context_applied': True,
            'ambiguity_resolution_notes': 'Resolved using cultural and linguistic context'
        }

# Usage example
async def main():
    """Example usage of Master Orchestrator"""
    
    orchestrator = MasterOrchestrator()
    
    # Test with multilingual input
    test_inputs = [
        "Asalamualaikum bhai, can you help me with some work?",
        "I need to analyze this document for cultural content",
        "Please help me understand the patterns in this data",
        "Can you process this audio file and extract insights?"
    ]
    
    for user_input in test_inputs:
        master_query = await orchestrator.process_user_input(user_input)
        print(f"\nInput: {user_input}")
        print(f"Detected Language: {master_query.detected_language}")
        print(f"Cultural Context: {master_query.cultural_context}")
        print(f"Generated Prompt: {master_query.generated_prompt[:200]}...")

if __name__ == "__main__":
    asyncio.run(main())
