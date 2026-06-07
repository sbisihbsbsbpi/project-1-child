"""
Metadata Updater - Automatically updates template_metadata.json with enhanced features

This module provides safe, atomic updates to the template metadata file,
ensuring we don't lose data and can track changes over time.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import shutil


class MetadataUpdater:
    """
    Safely updates template_metadata.json with enhanced features from detection runs.
    
    Features:
    - Automatic backups before any modification
    - Atomic writes (write to temp file, then rename)
    - Change tracking (logs what was updated)
    - Error handling with rollback capability
    """
    
    def __init__(self, metadata_path: str = None):
        """
        Initialize the metadata updater.
        
        Args:
            metadata_path: Path to template_metadata.json (auto-detected if not provided)
        """
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
        
        self.metadata_path = os.path.abspath(metadata_path)
        self.backup_dir = os.path.join(os.path.dirname(self.metadata_path), 'metadata_backups')
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _create_backup(self) -> str:
        """
        Create a timestamped backup of the metadata file.
        
        Returns:
            Path to the backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"template_metadata_backup_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        shutil.copy2(self.metadata_path, backup_path)
        print(f"📦 Backup created: {backup_filename}")
        
        return backup_path
    
    def _load_metadata(self) -> Dict:
        """Load the current metadata file."""
        with open(self.metadata_path, 'r') as f:
            return json.load(f)
    
    def _save_metadata(self, metadata: Dict):
        """
        Atomically save metadata to file.
        
        Uses a temporary file and rename to ensure atomic writes.
        """
        temp_path = self.metadata_path + '.tmp'
        
        # Write to temporary file
        with open(temp_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Atomic rename
        os.replace(temp_path, self.metadata_path)
    
    def update_template_detection(self, template_id: str, template_name: str, 
                                  detection_result: Dict) -> bool:
        """
        Update a template's detection data with enhanced features.
        
        Args:
            template_id: Template ID to update
            template_name: Template name (for logging)
            detection_result: Detection result containing enhancedFeatures
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Create backup first
            backup_path = self._create_backup()
            
            # Load current metadata
            metadata = self._load_metadata()
            
            # Find the template
            template_found = False
            for template in metadata.get('templates', []):
                # Match by ID or name
                if (template.get('id') == template_id or 
                    template.get('name') == template_name):
                    
                    template_found = True
                    
                    # Extract enhanced features
                    enhanced = detection_result.get('enhancedFeatures', {})

                    if not enhanced:
                        print(f"⚠️  No enhanced features found for {template_name}")
                        return False

                    # Update detection data
                    if 'detection' not in template:
                        template['detection'] = {}

                    # Add enhanced features (Phase 1)
                    template['detection']['sortable_item_count'] = enhanced.get('sortableItemCount', 0)
                    template['detection']['total_table_count'] = enhanced.get('totalTableCount', 0)
                    template['detection']['non_logo_table_count'] = enhanced.get('nonLogoTableCount', 0)
                    template['detection']['has_buttons'] = enhanced.get('hasButtons', False)
                    template['detection']['dynamic_tag_count'] = enhanced.get('dynamicTagCount', 0)

                    # PHASE 2 ENHANCEMENTS (June 7, 2026)
                    # Add learned logo markers count
                    learned_logos = detection_result.get('learnedLogosCount', 0)
                    if learned_logos > 0:
                        template['detection']['learned_logos_count'] = learned_logos
                        print(f"   ✨ Learned logos found: {learned_logos}")

                    # Add API cross-validation results
                    cross_validation = detection_result.get('apiCrossValidation', {})
                    if cross_validation:
                        template['detection']['api_cross_validation'] = {
                            'api_has_logo': cross_validation.get('apiHasLogo', False),
                            'detection_found_logo': cross_validation.get('detectionFoundLogo', False),
                            'false_negative': cross_validation.get('falseNegative', False),
                            'validated_at': datetime.now().isoformat()
                        }

                        if cross_validation.get('falseNegative'):
                            print(f"   ⚠️  FALSE NEGATIVE: API has logo but detection missed it")
                            template['detection']['needs_manual_inspection'] = True

                    # Add metadata about the update
                    template['detection']['enhanced_features_updated'] = datetime.now().isoformat()
                    template['detection']['phase_2_enhanced'] = True

                    print(f"✅ Updated {template_name}:")
                    print(f"   • Sortable items: {enhanced.get('sortableItemCount', 0)}")
                    print(f"   • Total tables: {enhanced.get('totalTableCount', 0)}")
                    print(f"   • Dynamic tags: {enhanced.get('dynamicTagCount', 0)}")
                    
                    break
            
            if not template_found:
                print(f"⚠️  Template not found in metadata: {template_name} ({template_id})")
                return False
            
            # Save updated metadata
            self._save_metadata(metadata)
            print(f"💾 Metadata saved successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating metadata: {e}")
            print(f"   Backup available at: {backup_path}")
            return False
    
    def get_templates_without_enhanced_features(self) -> list:
        """
        Get list of templates that don't have enhanced features yet.
        
        Returns:
            List of template names
        """
        metadata = self._load_metadata()
        templates_without = []
        
        for template in metadata.get('templates', []):
            detection = template.get('detection', {})
            if 'sortable_item_count' not in detection:
                templates_without.append(template.get('name', 'Unknown'))
        
        return templates_without
