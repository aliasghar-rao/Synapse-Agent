"""
App Generator module for Drive-Manager Pro.
Generates applications based on user prompts and analysis of existing apps.
"""

import logging
import os
import json
import datetime
import random
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models import Base, File
from database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppTemplate(Base):
    """Model representing an application template extracted from analysis"""
    __tablename__ = 'app_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)
    description = Column(Text)
    features = Column(Text)  # JSON list of features
    ui_components = Column(Text)  # JSON description of UI components
    api_endpoints = Column(Text)  # JSON list of API endpoints
    complexity = Column(Integer)  # 1-10 scale
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<AppTemplate(name='{self.name}', category='{self.category}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'features': json.loads(self.features) if self.features else [],
            'ui_components': json.loads(self.ui_components) if self.ui_components else {},
            'api_endpoints': json.loads(self.api_endpoints) if self.api_endpoints else [],
            'complexity': self.complexity
        }

class GeneratedApp(Base):
    """Model representing a generated application"""
    __tablename__ = 'generated_apps'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    prompt = Column(Text)  # Original prompt used to generate
    template_id = Column(Integer, ForeignKey('app_templates.id'))
    features = Column(Text)  # JSON list of features
    status = Column(String)  # pending, generating, completed, failed
    output_path = Column(String)  # Path to generated files
    
    template = relationship("AppTemplate")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<GeneratedApp(name='{self.name}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'prompt': self.prompt,
            'template_id': self.template_id,
            'template_name': self.template.name if self.template else None,
            'features': json.loads(self.features) if self.features else [],
            'status': self.status,
            'output_path': self.output_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AppGenerator:
    """Manager for app generation functionality"""
    
    def __init__(self):
        """Initialize the app generator"""
        self.initialize_templates()
    
    def initialize_templates(self):
        """Initialize the database with sample app templates if needed"""
        session = db_manager.get_session()
        if not session:
            logger.error("Failed to get database session")
            return
        
        try:
            # Check if we already have templates
            template_count = session.query(AppTemplate).count()
            if template_count > 0:
                logger.info(f"Database already contains {template_count} app templates")
                session.close()
                return
            
            # Sample app templates
            templates = [
                {
                    "name": "Social Media App",
                    "category": "Social",
                    "description": "A social media application with user profiles, posts, and messaging",
                    "features": json.dumps([
                        "User authentication", 
                        "Profile management", 
                        "Post creation and sharing", 
                        "Image uploads", 
                        "Direct messaging", 
                        "Notifications"
                    ]),
                    "ui_components": json.dumps({
                        "screens": ["Login", "Registration", "Feed", "Profile", "Messaging", "Settings"],
                        "components": ["Post Card", "User Avatar", "Comment Section", "Navigation Bar"]
                    }),
                    "api_endpoints": json.dumps([
                        "/api/auth/login", 
                        "/api/auth/register", 
                        "/api/users/profile", 
                        "/api/posts", 
                        "/api/messages"
                    ]),
                    "complexity": 8
                },
                {
                    "name": "Task Manager",
                    "category": "Productivity",
                    "description": "A task management application with projects, tasks, and deadlines",
                    "features": json.dumps([
                        "Task creation and management", 
                        "Project organization", 
                        "Deadline tracking", 
                        "Priority levels", 
                        "Task assignments", 
                        "Progress tracking"
                    ]),
                    "ui_components": json.dumps({
                        "screens": ["Dashboard", "Projects", "Tasks", "Calendar", "Settings"],
                        "components": ["Task Card", "Project List", "Calendar View", "Progress Bar"]
                    }),
                    "api_endpoints": json.dumps([
                        "/api/tasks", 
                        "/api/projects", 
                        "/api/users/assignments", 
                        "/api/deadlines"
                    ]),
                    "complexity": 6
                },
                {
                    "name": "E-commerce Store",
                    "category": "E-commerce",
                    "description": "An online store with product listings, shopping cart, and checkout",
                    "features": json.dumps([
                        "Product catalog", 
                        "Shopping cart", 
                        "User accounts", 
                        "Payment processing", 
                        "Order tracking", 
                        "Product reviews"
                    ]),
                    "ui_components": json.dumps({
                        "screens": ["Home", "Product List", "Product Details", "Cart", "Checkout", "Orders"],
                        "components": ["Product Card", "Category List", "Cart Summary", "Payment Form"]
                    }),
                    "api_endpoints": json.dumps([
                        "/api/products", 
                        "/api/categories", 
                        "/api/cart", 
                        "/api/orders", 
                        "/api/payments"
                    ]),
                    "complexity": 9
                },
                {
                    "name": "Weather App",
                    "category": "Utility",
                    "description": "A weather forecasting application with location-based weather data",
                    "features": json.dumps([
                        "Current weather conditions", 
                        "5-day forecast", 
                        "Location detection", 
                        "Weather alerts", 
                        "Multiple locations", 
                        "Weather maps"
                    ]),
                    "ui_components": json.dumps({
                        "screens": ["Current Weather", "Forecast", "Maps", "Settings"],
                        "components": ["Weather Card", "Forecast List", "Temperature Chart", "Location Picker"]
                    }),
                    "api_endpoints": json.dumps([
                        "/api/weather/current", 
                        "/api/weather/forecast", 
                        "/api/locations", 
                        "/api/alerts"
                    ]),
                    "complexity": 5
                },
                {
                    "name": "Fitness Tracker",
                    "category": "Health",
                    "description": "A fitness and health tracking application for exercises and nutrition",
                    "features": json.dumps([
                        "Workout tracking", 
                        "Exercise library", 
                        "Nutrition tracking", 
                        "Progress charts", 
                        "Goal setting", 
                        "Fitness challenges"
                    ]),
                    "ui_components": json.dumps({
                        "screens": ["Dashboard", "Workouts", "Nutrition", "Progress", "Goals", "Settings"],
                        "components": ["Exercise Card", "Progress Chart", "Goal Tracker", "Nutrition Log"]
                    }),
                    "api_endpoints": json.dumps([
                        "/api/workouts", 
                        "/api/exercises", 
                        "/api/nutrition", 
                        "/api/progress", 
                        "/api/goals"
                    ]),
                    "complexity": 7
                }
            ]
            
            # Add templates to database
            for template_data in templates:
                template = AppTemplate(**template_data)
                session.add(template)
            
            session.commit()
            logger.info(f"Added {len(templates)} app templates to database")
        
        except Exception as e:
            logger.error(f"Error initializing app templates: {e}")
            session.rollback()
        
        finally:
            session.close()
    
    def get_templates(self):
        """Get all app templates from the database"""
        templates = []
        session = db_manager.get_session()
        
        if not session:
            return templates
        
        try:
            templates = [template.to_dict() for template in session.query(AppTemplate).all()]
            return templates
        
        except Exception as e:
            logger.error(f"Error getting app templates: {e}")
            return templates
        
        finally:
            session.close()
    
    def get_template_by_id(self, template_id):
        """Get an app template by ID"""
        session = db_manager.get_session()
        
        if not session:
            return None
        
        try:
            template = session.query(AppTemplate).filter_by(id=template_id).first()
            return template.to_dict() if template else None
        
        except Exception as e:
            logger.error(f"Error getting app template by ID: {e}")
            return None
        
        finally:
            session.close()
    
    def analyze_prompt(self, prompt):
        """Analyze a user prompt to find the best matching template and features"""
        # In a real implementation, this would use NLP to analyze the prompt
        # For now, we'll use a simple keyword matching approach
        
        prompt = prompt.lower()
        matches = []
        
        templates = self.get_templates()
        for template in templates:
            score = 0
            
            # Check if name or category matches
            if template['name'].lower() in prompt:
                score += 10
            if template['category'].lower() in prompt:
                score += 5
            
            # Check for feature matches
            for feature in template['features']:
                if feature.lower() in prompt:
                    score += 3
            
            if score > 0:
                matches.append({
                    'template': template,
                    'score': score
                })
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        if matches:
            # Return best match
            return matches[0]['template']
        else:
            # Return a default template if no matches
            return self.get_templates()[0] if self.get_templates() else None
    
    def create_app(self, prompt, name=None):
        """Create a new app based on a user prompt"""
        if not name:
            # Generate a name based on the prompt if none provided
            words = prompt.split()
            name = " ".join([word.capitalize() for word in words[:3] if len(word) > 3]) + " App"
        
        # Analyze prompt to find best template
        template = self.analyze_prompt(prompt)
        if not template:
            return {"error": "Could not find a suitable template"}
        
        # Create generated app record
        session = db_manager.get_session()
        if not session:
            return {"error": "Database error"}
        
        try:
            # Extract features from prompt and template
            features = self._extract_features_from_prompt(prompt, template)
            
            # Create a new generated app
            generated_app = GeneratedApp(
                name=name,
                description=f"Generated app based on {template['name']} template",
                prompt=prompt,
                template_id=template['id'],
                features=json.dumps(features),
                status="pending",
                output_path=f"/home/user/generated_apps/{name.replace(' ', '_').lower()}"
            )
            
            session.add(generated_app)
            session.commit()
            
            # Start the generation process (would be async in a real implementation)
            self._update_app_status(generated_app.id, "generating")
            
            # Generate the app code
            success = self._generate_app_code(generated_app.id, template, features)
            
            if success:
                self._update_app_status(generated_app.id, "completed")
                return {"success": True, "app_id": generated_app.id, "message": "App generated successfully"}
            else:
                self._update_app_status(generated_app.id, "failed")
                return {"success": False, "app_id": generated_app.id, "message": "App generation failed"}
        
        except Exception as e:
            logger.error(f"Error creating app: {e}")
            session.rollback()
            return {"error": str(e)}
        
        finally:
            session.close()
    
    def _extract_features_from_prompt(self, prompt, template):
        """Extract requested features from the prompt and template"""
        features = []
        
        # Add base features from template
        for feature in template['features'][:3]:  # Add some basic features
            features.append(feature)
        
        # Look for specific feature mentions in prompt
        prompt_lower = prompt.lower()
        for feature in template['features'][3:]:  # Check remaining features
            if feature.lower() in prompt_lower:
                features.append(feature)
        
        # Ensure we have at least some features
        if len(features) < 3:
            features = template['features'][:3]
        
        return features
    
    def _update_app_status(self, app_id, status):
        """Update the status of a generated app"""
        session = db_manager.get_session()
        if not session:
            return False
        
        try:
            app = session.query(GeneratedApp).filter_by(id=app_id).first()
            if app:
                app.status = status
                session.commit()
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error updating app status: {e}")
            session.rollback()
            return False
        
        finally:
            session.close()
    
    def _generate_app_code(self, app_id, template, features):
        """Generate the app code based on template and features"""
        # In a real implementation, this would generate actual code
        # For this demo, we'll just create a structure with placeholders
        
        session = db_manager.get_session()
        if not session:
            return False
        
        try:
            app = session.query(GeneratedApp).filter_by(id=app_id).first()
            if not app:
                return False
            
            # Create output directory structure if it doesn't exist
            os.makedirs(app.output_path, exist_ok=True)
            
            # Create a README file with app information
            with open(os.path.join(app.output_path, "README.md"), "w") as f:
                f.write(f"# {app.name}\n\n")
                f.write(f"{app.description}\n\n")
                f.write("## Features\n\n")
                for feature in json.loads(app.features):
                    f.write(f"- {feature}\n")
                f.write("\n## Generated based on prompt:\n\n")
                f.write(f"{app.prompt}\n")
            
            # Create a basic structure based on template
            if template['category'] == 'Social':
                self._generate_social_app_structure(app.output_path)
            elif template['category'] == 'Productivity':
                self._generate_productivity_app_structure(app.output_path)
            elif template['category'] == 'E-commerce':
                self._generate_ecommerce_app_structure(app.output_path)
            else:
                self._generate_generic_app_structure(app.output_path, template['name'])
            
            # Record the app in our database
            app_file = File(
                path=app.output_path,
                name=app.name,
                extension="",
                size=0,
                is_directory=True,
                file_type="application",
                created_time=datetime.datetime.now(),
                modified_time=datetime.datetime.now(),
                accessed_time=datetime.datetime.now()
            )
            session.add(app_file)
            session.commit()
            
            return True
        
        except Exception as e:
            logger.error(f"Error generating app code: {e}")
            session.rollback()
            return False
        
        finally:
            session.close()
    
    def _generate_social_app_structure(self, output_path):
        """Generate a social media app structure"""
        directories = ["src", "src/components", "src/screens", "src/api", "src/assets", "public"]
        for directory in directories:
            os.makedirs(os.path.join(output_path, directory), exist_ok=True)
        
        # Create basic files
        with open(os.path.join(output_path, "src", "App.js"), "w") as f:
            f.write("""
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import LoginScreen from './screens/LoginScreen';
import RegisterScreen from './screens/RegisterScreen';
import FeedScreen from './screens/FeedScreen';
import ProfileScreen from './screens/ProfileScreen';
import MessagingScreen from './screens/MessagingScreen';

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="Feed" component={FeedScreen} />
        <Stack.Screen name="Profile" component={ProfileScreen} />
        <Stack.Screen name="Messaging" component={MessagingScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
""")
        
        # Create a component
        with open(os.path.join(output_path, "src", "components", "PostCard.js"), "w") as f:
            f.write("""
import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity } from 'react-native';

export default function PostCard({ post, onLike }) {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Image source={{ uri: post.userAvatar }} style={styles.avatar} />
        <Text style={styles.username}>{post.username}</Text>
      </View>
      
      {post.imageUrl && (
        <Image source={{ uri: post.imageUrl }} style={styles.postImage} />
      )}
      
      <Text style={styles.content}>{post.content}</Text>
      
      <View style={styles.actions}>
        <TouchableOpacity onPress={() => onLike(post.id)}>
          <Text style={styles.actionText}>Like ({post.likes})</Text>
        </TouchableOpacity>
        <TouchableOpacity>
          <Text style={styles.actionText}>Comment ({post.comments.length})</Text>
        </TouchableOpacity>
        <TouchableOpacity>
          <Text style={styles.actionText}>Share</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 8,
  },
  username: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  postImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    marginBottom: 12,
  },
  content: {
    fontSize: 14,
    marginBottom: 12,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: '#eee',
    paddingTop: 12,
  },
  actionText: {
    color: '#6200ee',
    fontWeight: '500',
  },
});
""")
        
        # Create package.json
        with open(os.path.join(output_path, "package.json"), "w") as f:
            f.write("""
{
  "name": "social-media-app",
  "version": "1.0.0",
  "description": "A social media application with user profiles, posts, and messaging",
  "main": "index.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web"
  },
  "dependencies": {
    "@react-navigation/native": "^6.0.0",
    "@react-navigation/stack": "^6.0.0",
    "expo": "~44.0.0",
    "expo-status-bar": "~1.2.0",
    "react": "17.0.1",
    "react-dom": "17.0.1",
    "react-native": "0.64.3",
    "react-native-gesture-handler": "~2.1.0",
    "react-native-safe-area-context": "3.3.2",
    "react-native-screens": "~3.10.1",
    "react-native-web": "0.17.1"
  },
  "devDependencies": {
    "@babel/core": "^7.12.9"
  },
  "private": true
}
""")
    
    def _generate_productivity_app_structure(self, output_path):
        """Generate a productivity app structure"""
        directories = ["src", "src/components", "src/pages", "src/api", "src/assets", "public"]
        for directory in directories:
            os.makedirs(os.path.join(output_path, directory), exist_ok=True)
        
        # Create basic files
        with open(os.path.join(output_path, "src", "App.js"), "w") as f:
            f.write("""
import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Tasks from './pages/Tasks';
import Calendar from './pages/Calendar';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <div className="content-wrapper">
          <Sidebar />
          <main className="main-content">
            <Switch>
              <Route exact path="/" component={Dashboard} />
              <Route path="/projects" component={Projects} />
              <Route path="/tasks" component={Tasks} />
              <Route path="/calendar" component={Calendar} />
              <Route path="/settings" component={Settings} />
            </Switch>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
""")
        
        # Create CSS
        with open(os.path.join(output_path, "src", "App.css"), "w") as f:
            f.write("""
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.content-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f7fa;
}

/* Task Styles */
.task-card {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border-left: 4px solid #3498db;
}

.task-card.priority-high {
  border-left-color: #e74c3c;
}

.task-card.priority-medium {
  border-left-color: #f39c12;
}

.task-card.priority-low {
  border-left-color: #2ecc71;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-title {
  font-weight: 600;
  font-size: 16px;
}

.task-content {
  color: #555;
  margin-bottom: 16px;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-due-date {
  font-size: 14px;
  color: #777;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.task-actions button {
  background: none;
  border: none;
  cursor: pointer;
  color: #555;
}

.task-actions button:hover {
  color: #3498db;
}
""")
        
        # Create package.json
        with open(os.path.join(output_path, "package.json"), "w") as f:
            f.write("""
{
  "name": "task-manager-app",
  "version": "1.0.0",
  "description": "A task management application with projects, tasks, and deadlines",
  "main": "index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-router-dom": "^5.3.0",
    "react-scripts": "5.0.0",
    "axios": "^0.24.0",
    "date-fns": "^2.28.0",
    "react-beautiful-dnd": "^13.1.0",
    "react-datepicker": "^4.6.0"
  },
  "devDependencies": {
    "web-vitals": "^2.1.4"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
""")
    
    def _generate_ecommerce_app_structure(self, output_path):
        """Generate an e-commerce app structure"""
        directories = ["src", "src/components", "src/pages", "src/context", "src/api", "src/assets", "public"]
        for directory in directories:
            os.makedirs(os.path.join(output_path, directory), exist_ok=True)
        
        # Create basic files
        with open(os.path.join(output_path, "src", "App.js"), "w") as f:
            f.write("""
import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import ProductListPage from './pages/ProductListPage';
import ProductDetailPage from './pages/ProductDetailPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import OrdersPage from './pages/OrdersPage';
import { CartProvider } from './context/CartContext';
import './App.css';

function App() {
  return (
    <CartProvider>
      <Router>
        <div className="app">
          <Header />
          <main className="main-content">
            <Switch>
              <Route exact path="/" component={HomePage} />
              <Route path="/products" component={ProductListPage} />
              <Route path="/product/:id" component={ProductDetailPage} />
              <Route path="/cart" component={CartPage} />
              <Route path="/checkout" component={CheckoutPage} />
              <Route path="/orders" component={OrdersPage} />
            </Switch>
          </main>
          <Footer />
        </div>
      </Router>
    </CartProvider>
  );
}

export default App;
""")
        
        # Create Cart Context
        with open(os.path.join(output_path, "src", "context", "CartContext.js"), "w") as f:
            f.write("""
import React, { createContext, useState, useEffect } from 'react';

export const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);
  const [cartTotal, setCartTotal] = useState(0);
  
  useEffect(() => {
    // Calculate cart total whenever cartItems changes
    const total = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    setCartTotal(total);
  }, [cartItems]);
  
  const addToCart = (product, quantity = 1) => {
    setCartItems(prevItems => {
      // Check if item is already in cart
      const existingItemIndex = prevItems.findIndex(item => item.id === product.id);
      
      if (existingItemIndex > -1) {
        // Item exists, update quantity
        const updatedItems = [...prevItems];
        updatedItems[existingItemIndex].quantity += quantity;
        return updatedItems;
      } else {
        // Item doesn't exist, add new item
        return [...prevItems, { ...product, quantity }];
      }
    });
  };
  
  const removeFromCart = (productId) => {
    setCartItems(prevItems => prevItems.filter(item => item.id !== productId));
  };
  
  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    
    setCartItems(prevItems => 
      prevItems.map(item => 
        item.id === productId ? { ...item, quantity } : item
      )
    );
  };
  
  const clearCart = () => {
    setCartItems([]);
  };
  
  return (
    <CartContext.Provider value={{
      cartItems,
      cartTotal,
      addToCart,
      removeFromCart,
      updateQuantity,
      clearCart
    }}>
      {children}
    </CartContext.Provider>
  );
};
""")
        
        # Create package.json
        with open(os.path.join(output_path, "package.json"), "w") as f:
            f.write("""
{
  "name": "ecommerce-store",
  "version": "1.0.0",
  "description": "An online store with product listings, shopping cart, and checkout",
  "main": "index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-router-dom": "^5.3.0",
    "react-scripts": "5.0.0",
    "axios": "^0.24.0",
    "stripe": "^8.195.0",
    "react-slick": "^0.28.1",
    "react-icons": "^4.3.1"
  },
  "devDependencies": {
    "web-vitals": "^2.1.4"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
""")
    
    def _generate_generic_app_structure(self, output_path, template_name):
        """Generate a generic app structure"""
        directories = ["src", "src/components", "src/screens", "src/services", "src/assets", "public"]
        for directory in directories:
            os.makedirs(os.path.join(output_path, directory), exist_ok=True)
        
        # Create basic files
        with open(os.path.join(output_path, "src", "index.js"), "w") as f:
            f.write(f"""
// Main entry point for {template_name}
import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);
""")
        
        with open(os.path.join(output_path, "src", "App.js"), "w") as f:
            f.write(f"""
// Main App component for {template_name}
import React, { useState, useEffect } from 'react';
import './App.css';
import MainScreen from './screens/MainScreen';
import { fetchData } from './services/api';

function App() {{
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {{
    // Fetch data when component mounts
    const loadData = async () => {{
      try {{
        const result = await fetchData();
        setData(result);
      }} catch (error) {{
        console.error('Error loading data:', error);
      }} finally {{
        setLoading(false);
      }}
    }};
    
    loadData();
  }}, []);
  
  return (
    <div className="app">
      <header className="app-header">
        <h1>{template_name}</h1>
      </header>
      
      <main className="app-content">
        {{loading ? (
          <p>Loading...</p>
        ) : (
          <MainScreen data={{data}} />
        )}}
      </main>
      
      <footer className="app-footer">
        <p>&copy; 2025 {template_name}. All rights reserved.</p>
      </footer>
    </div>
  );
}}

export default App;
""")
        
        with open(os.path.join(output_path, "src", "services", "api.js"), "w") as f:
            f.write(f"""
// API service for {template_name}

// Base URL for API calls
const API_BASE_URL = 'https://api.example.com';

// Fetch data from API
export const fetchData = async () => {{
  try {{
    // In a real app, this would be an actual API call
    // For now, we'll return mock data
    return mockData;
  }} catch (error) {{
    console.error('Error fetching data:', error);
    throw error;
  }}
}};

// Mock data for development
const mockData = [
  {{ id: 1, name: 'Item 1', description: 'Description for item 1' }},
  {{ id: 2, name: 'Item 2', description: 'Description for item 2' }},
  {{ id: 3, name: 'Item 3', description: 'Description for item 3' }},
  {{ id: 4, name: 'Item 4', description: 'Description for item 4' }},
  {{ id: 5, name: 'Item 5', description: 'Description for item 5' }},
];

// Post data to API
export const postData = async (data) => {{
  try {{
    // In a real app, this would be an actual API call
    console.log('Posting data:', data);
    return {{ success: true, message: 'Data saved successfully' }};
  }} catch (error) {{
    console.error('Error posting data:', error);
    throw error;
  }}
}};
""")
        
        # Create a main screen component
        with open(os.path.join(output_path, "src", "screens", "MainScreen.js"), "w") as f:
            f.write(f"""
// Main screen component for {template_name}
import React from 'react';
import ItemList from '../components/ItemList';

const MainScreen = ({{ data }}) => {{
  return (
    <div className="main-screen">
      <h2>Welcome to {template_name}</h2>
      <p>This is the main screen of your application.</p>
      
      <section className="content-section">
        <h3>Your Items</h3>
        <ItemList items={{data}} />
      </section>
    </div>
  );
}};

export default MainScreen;
""")
        
        # Create a component
        with open(os.path.join(output_path, "src", "components", "ItemList.js"), "w") as f:
            f.write("""
// Item list component
import React from 'react';

const ItemList = ({ items = [] }) => {
  if (items.length === 0) {
    return <p>No items found.</p>;
  }
  
  return (
    <div className="item-list">
      {items.map(item => (
        <div key={item.id} className="item-card">
          <h4>{item.name}</h4>
          <p>{item.description}</p>
          <button className="view-button">View Details</button>
        </div>
      ))}
    </div>
  );
};

export default ItemList;
""")
        
        # Create CSS file
        with open(os.path.join(output_path, "src", "App.css"), "w") as f:
            f.write("""
/* App styles */
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.app-header {
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-content {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background-color: #f5f5f5;
  padding: 1rem 2rem;
  text-align: center;
  color: #666;
  border-top: 1px solid #eaeaea;
}

/* Item list styles */
.item-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.item-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.item-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.item-card h4 {
  margin-top: 0;
  color: #333;
}

.item-card p {
  color: #666;
  margin-bottom: 1.5rem;
}

.view-button {
  background-color: #2575fc;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.view-button:hover {
  background-color: #1a65e0;
}

/* Main screen styles */
.main-screen h2 {
  color: #333;
  margin-bottom: 1rem;
}

.content-section {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 2rem;
}

.content-section h3 {
  margin-top: 0;
  color: #444;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 0.5rem;
  margin-bottom: 1.5rem;
}
""")
        
        # Create package.json
        with open(os.path.join(output_path, "package.json"), "w") as f:
            f.write(f"""
{{
  "name": "{template_name.lower().replace(' ', '-')}",
  "version": "1.0.0",
  "description": "Generated app based on {template_name} template",
  "main": "index.js",
  "scripts": {{
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }},
  "dependencies": {{
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-scripts": "5.0.0",
    "axios": "^0.24.0"
  }},
  "devDependencies": {{
    "web-vitals": "^2.1.4"
  }},
  "browserslist": {{
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }}
}}
""")
    
    def get_generated_apps(self):
        """Get all generated apps from the database"""
        generated_apps = []
        session = db_manager.get_session()
        
        if not session:
            return generated_apps
        
        try:
            generated_apps = [app.to_dict() for app in session.query(GeneratedApp).all()]
            return generated_apps
        
        except Exception as e:
            logger.error(f"Error getting generated apps: {e}")
            return generated_apps
        
        finally:
            session.close()
    
    def get_generated_app_by_id(self, app_id):
        """Get a generated app by ID"""
        session = db_manager.get_session()
        
        if not session:
            return None
        
        try:
            app = session.query(GeneratedApp).filter_by(id=app_id).first()
            return app.to_dict() if app else None
        
        except Exception as e:
            logger.error(f"Error getting generated app by ID: {e}")
            return None
        
        finally:
            session.close()

# Singleton instance
app_generator = AppGenerator()