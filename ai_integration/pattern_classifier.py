"""
AI-Powered Template Pattern Classifier

This module uses machine learning to classify templates into categories
and predict their structure based on DOM analysis.
"""

import json
import os
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np
import pickle


class TemplateClassifier:
    """
    Classifies templates into categories and predicts structural properties.
    
    Trained on template_metadata.json with 39 labeled examples.
    """
    
    def __init__(self, metadata_path: str = None):
        # Auto-detect metadata path
        if metadata_path is None:
            # Try current directory first
            if os.path.exists('template_metadata.json'):
                metadata_path = 'template_metadata.json'
            # Try parent directory
            elif os.path.exists('../template_metadata.json'):
                metadata_path = '../template_metadata.json'
            # Try from ai_integration directory
            elif os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'template_metadata.json')):
                metadata_path = os.path.join(os.path.dirname(__file__), '..', 'template_metadata.json')
            else:
                raise FileNotFoundError("template_metadata.json not found")

        self.metadata_path = metadata_path
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        self.categories = []

        # Load training data
        self._load_metadata()

        # Try to load pre-trained model, otherwise train
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'template_classifier.pkl')
        if os.path.exists(model_path):
            self._load_model()
        else:
            self._train_model()
    
    def _load_metadata(self):
        """Load and parse template metadata."""
        with open(self.metadata_path, 'r') as f:
            data = json.load(f)
            self.templates = data['templates']
            self.categories = list(set(t['category'] for t in self.templates))
    
    def _extract_features(self, template: Dict) -> np.ndarray:
        """
        Extract numerical features from template metadata.

        Features (11 total):
        Original 6:
        - logo_tables_found (int)
        - header_button_opacity (float)
        - has_logos (bool -> int)
        - logo_count (int)
        - department_count (int)
        - logo_type encoded (int)

        Enhanced 5 (Phase 1):
        - sortable_item_count (int)
        - total_table_count (int)
        - non_logo_table_count (int)
        - has_buttons (bool -> int)
        - dynamic_tag_count (int)
        """
        detection = template.get('detection', {})

        # Original 6 features
        logo_type = detection.get('logo_type', 'none')
        logo_type_map = {
            'none': 0,
            'null': 0,
            None: 0,
            'sortable item images': 1,
            'resizable images': 2,
            'table-based': 3
        }

        original_features = [
            detection.get('logo_tables_found', 0),
            detection.get('header_button_opacity', 1.0),
            1 if detection.get('has_logos', False) else 0,
            detection.get('logo_count', 0),
            len(template.get('departments', [])),
            logo_type_map.get(logo_type, 0)
        ]

        # Enhanced 5 features (Phase 1)
        enhanced_features = [
            detection.get('sortable_item_count', 0),
            detection.get('total_table_count', 0),
            detection.get('non_logo_table_count', 0),
            1 if detection.get('has_buttons', False) else 0,
            detection.get('dynamic_tag_count', 0)
        ]

        # Combine all features
        all_features = original_features + enhanced_features

        # Update feature names
        self.feature_names = [
            'logo_tables_found',
            'header_button_opacity',
            'has_logos',
            'logo_count',
            'department_count',
            'logo_type_encoded',
            # Enhanced features
            'sortable_item_count',
            'total_table_count',
            'non_logo_table_count',
            'has_buttons',
            'dynamic_tag_count'
        ]

        return np.array(all_features)
    
    def _train_model(self):
        """Train the classifier on metadata."""
        print("🤖 Training template classifier...")
        
        # Extract features and labels
        X = []
        y = []
        
        for template in self.templates:
            features = self._extract_features(template)
            X.append(features)
            y.append(template['category'])
        
        X = np.array(X)
        y = self.label_encoder.fit_transform(y)
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X, y)
        
        # Save model
        model_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, 'template_classifier.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'label_encoder': self.label_encoder,
                'feature_names': self.feature_names
            }, f)
        
        # Print training accuracy
        accuracy = self.model.score(X, y)
        print(f"✅ Training accuracy: {accuracy:.2%}")
        print(f"📊 Trained on {len(X)} templates")
        print(f"🏷️  Categories: {len(self.categories)}")
    
    def _load_model(self):
        """Load pre-trained model."""
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'template_classifier.pkl')
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.label_encoder = data['label_encoder']
            self.feature_names = data['feature_names']
        print("✅ Loaded pre-trained classifier")
    
    def predict(self, template: Dict) -> Dict[str, Any]:
        """
        Predict category and properties for a template.
        
        Args:
            template: Template metadata dict
            
        Returns:
            Prediction dict with category, confidence, and anomalies
        """
        features = self._extract_features(template).reshape(1, -1)
        
        # Predict
        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]
        
        category = self.label_encoder.inverse_transform([prediction])[0]
        confidence = float(np.max(probabilities))
        
        # Detect anomalies (low confidence = unusual)
        anomalies = []
        if confidence < 0.7:
            anomalies.append(f"Low confidence ({confidence:.2%})")
        
        # Feature-based anomalies
        if template.get('detection', {}).get('logo_tables_found', 0) > 4:
            anomalies.append("Unusually high logo table count")
        
        return {
            'category': category,
            'confidence': confidence,
            'probabilities': dict(zip(self.label_encoder.classes_, probabilities)),
            'anomalies': anomalies,
            'features': dict(zip(self.feature_names, features[0]))
        }
