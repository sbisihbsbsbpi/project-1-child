"""
AI Assistant for Logo Automation

Main integration point for all AI-powered features.
"""

import sys
import os
from typing import Dict, Optional
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_integration.pattern_classifier import TemplateClassifier
from ai_integration.log_analyzer import AILogAnalyzer
from ai_integration.test_generator import TestGenerator


class AIAssistant:
    """
    Main AI assistant that coordinates all AI capabilities.
    """
    
    def __init__(self):
        """Initialize all AI components."""
        print("🤖 Initializing AI Assistant...")
        
        try:
            self.classifier = TemplateClassifier()
            print("✅ Pattern Classifier ready")
        except Exception as e:
            print(f"⚠️  Pattern Classifier failed: {e}")
            self.classifier = None
        
        try:
            self.log_analyzer = AILogAnalyzer(provider='openai')
            print("✅ Log Analyzer ready")
        except Exception as e:
            print(f"⚠️  Log Analyzer failed: {e}")
            self.log_analyzer = None
        
        try:
            self.test_generator = TestGenerator()
            print("✅ Test Generator ready")
        except Exception as e:
            print(f"⚠️  Test Generator failed: {e}")
            self.test_generator = None
        
        print("🎉 AI Assistant initialized!\n")
    
    def analyze_template(self, template_data: Dict) -> Dict:
        """
        Analyze a template before processing.
        
        Args:
            template_data: Template metadata dict
            
        Returns:
            Analysis with predictions and recommendations
        """
        if not self.classifier:
            return {'error': 'Classifier not available'}
        
        prediction = self.classifier.predict(template_data)
        
        # Add recommendations
        recommendations = []
        if prediction['confidence'] < 0.7:
            recommendations.append("⚠️  Unusual template structure - proceed with caution")
        if prediction['anomalies']:
            recommendations.append(f"🔍 Anomalies detected: {', '.join(prediction['anomalies'])}")
        
        return {
            **prediction,
            'recommendations': recommendations,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def diagnose_log(self, log_path: str) -> Dict:
        """
        Diagnose issues from a log file.
        
        Args:
            log_path: Path to log file
            
        Returns:
            Diagnosis with root cause and fixes
        """
        if not self.log_analyzer:
            return {'error': 'Log Analyzer not available'}
        
        diagnosis = self.log_analyzer.diagnose_failure(log_path)
        
        # Format output
        report = {
            'log_file': log_path,
            'diagnosis': diagnosis,
            'action_items': self._generate_action_items(diagnosis)
        }
        
        return report
    
    def generate_tests_for_change(self, git_diff: Optional[str] = None) -> Dict:
        """
        Generate test suite for code changes.
        
        Args:
            git_diff: Git diff string (optional)
            
        Returns:
            Test suite specification
        """
        if not self.test_generator:
            return {'error': 'Test Generator not available'}
        
        # If no diff provided, get latest from git
        if git_diff is None:
            import subprocess
            try:
                git_diff = subprocess.check_output(
                    ['git', 'diff', 'HEAD~1', 'HEAD'],
                    cwd=os.path.dirname(os.path.dirname(__file__))
                ).decode('utf-8')
            except:
                git_diff = ""
        
        # Analyze impact
        impact = self.test_generator.analyze_code_change(git_diff)
        
        # Generate test suite
        test_suite = self.test_generator.generate_test_suite(impact)
        
        return {
            'impact_analysis': impact,
            'test_suite': test_suite,
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_action_items(self, diagnosis: Dict) -> list:
        """Generate actionable items from diagnosis."""
        actions = []
        
        if diagnosis.get('errors_found', 0) > 0:
            actions.append({
                'priority': 'high',
                'action': 'Review and fix detected error patterns',
                'details': diagnosis.get('patterns_matched', [])
            })
        
        if diagnosis.get('analysis_type') == 'ai-powered':
            actions.append({
                'priority': 'medium',
                'action': 'Review AI analysis',
                'details': 'Check ai_analysis field for detailed insights'
            })
        
        return actions
    
    def run_interactive(self):
        """Run interactive CLI."""
        print("\n" + "="*60)
        print("🤖 AI Assistant for Logo Automation")
        print("="*60 + "\n")
        
        while True:
            print("\nWhat would you like to do?")
            print("1. Analyze a template")
            print("2. Diagnose a log file")
            print("3. Generate test suite for changes")
            print("4. Exit")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                self._interactive_analyze_template()
            elif choice == '2':
                self._interactive_diagnose_log()
            elif choice == '3':
                self._interactive_generate_tests()
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
    
    def _interactive_analyze_template(self):
        """Interactive template analysis."""
        template_name = input("Enter template name: ").strip()
        
        # Find template in metadata
        with open('../template_metadata.json', 'r') as f:
            data = json.load(f)
            template = next((t for t in data['templates'] if t['name'] == template_name), None)
        
        if template:
            result = self.analyze_template(template)
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Template '{template_name}' not found")
    
    def _interactive_diagnose_log(self):
        """Interactive log diagnosis."""
        log_path = input("Enter log file path: ").strip()
        
        if os.path.exists(log_path):
            result = self.diagnose_log(log_path)
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Log file not found: {log_path}")
    
    def _interactive_generate_tests(self):
        """Interactive test generation."""
        print("Generating tests for latest git changes...")
        result = self.generate_tests_for_change()
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    assistant = AIAssistant()
    assistant.run_interactive()
