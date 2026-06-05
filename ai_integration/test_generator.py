"""
AI-Powered Test Generator

Analyzes code changes and generates targeted test cases for affected templates.
"""

import json
import os
from typing import Dict, List, Set, Optional
import ast
import re


class TestGenerator:
    """
    Generates targeted test cases based on code changes.
    Predicts which templates will be affected by changes.
    """
    
    def __init__(self, metadata_path: str = '../template_metadata.json'):
        self.metadata_path = metadata_path
        self._load_metadata()
    
    def _load_metadata(self):
        """Load template metadata."""
        with open(self.metadata_path, 'r') as f:
            data = json.load(f)
            self.templates = data['templates']
            self.categories = {}
            for template in self.templates:
                category = template['category']
                if category not in self.categories:
                    self.categories[category] = []
                self.categories[category].append(template)
    
    def analyze_code_change(self, code_diff: str) -> Dict:
        """
        Analyze a code change to determine impact.
        
        Args:
            code_diff: Git diff or code snippet that changed
            
        Returns:
            Impact analysis dict
        """
        impact = {
            'affects_detection': False,
            'affects_table_detection': False,
            'affects_hardcoded_detection': False,
            'affects_header_detection': False,
            'affects_guardrails': False,
            'affected_categories': set(),
            'risk_level': 'low'
        }
        
        # Keywords that indicate detection changes
        detection_keywords = {
            'table-based': 'affects_table_detection',
            'hardcoded': 'affects_hardcoded_detection',
            'header': 'affects_header_detection',
            'globalLogoRowsWithContent': 'affects_guardrails',
            'PASS 1': 'affects_table_detection',
            'PASS 2': 'affects_table_detection',
            'logoTablesCount': 'affects_guardrails',
        }
        
        for keyword, flag in detection_keywords.items():
            if keyword in code_diff:
                impact[flag] = True
                impact['affects_detection'] = True
        
        # Determine affected categories
        if impact['affects_table_detection']:
            impact['affected_categories'].update([
                'Service/Parts - 4 Logo Tables (No Extra Logos)',
                'Service/Parts - 4 Logo Tables (Has Extra Logos) - BUG',
                'Service/Parts - 2 Logo Tables (No Extra Logos)',
                'Service/Parts - 2 Logo Tables (Has Extra Logos) - BUG'
            ])
        
        if impact['affects_header_detection']:
            impact['affected_categories'].update([
                'CPRA - Has Header Already',
                'Service/Parts - No Logo Tables (Needs Header)'
            ])
        
        # Determine risk level
        if impact['affects_guardrails']:
            impact['risk_level'] = 'high'
        elif len(impact['affected_categories']) > 2:
            impact['risk_level'] = 'medium'
        
        return impact
    
    def generate_test_suite(self, code_change_impact: Dict) -> Dict:
        """
        Generate a test suite based on code change impact.
        
        Args:
            code_change_impact: Output from analyze_code_change()
            
        Returns:
            Test suite dict with templates to test
        """
        test_suite = {
            'risk_level': code_change_impact['risk_level'],
            'total_templates': 0,
            'test_templates': [],
            'rationale': []
        }
        
        # If no detection changes, minimal testing
        if not code_change_impact['affects_detection']:
            # Test 2 templates from each category
            for category, templates in self.categories.items():
                selected = templates[:2]
                test_suite['test_templates'].extend(selected)
            test_suite['rationale'].append("No detection changes - smoke test only")
        
        # If affects specific categories, test those thoroughly
        elif code_change_impact['affected_categories']:
            for category in code_change_impact['affected_categories']:
                if category in self.categories:
                    # Test ALL templates in affected category
                    test_suite['test_templates'].extend(self.categories[category])
                    test_suite['rationale'].append(f"Category affected: {category}")
            
            # Add 1 template from unaffected categories (regression check)
            for category, templates in self.categories.items():
                if category not in code_change_impact['affected_categories']:
                    test_suite['test_templates'].append(templates[0])
            test_suite['rationale'].append("Added regression checks for unaffected categories")
        
        # If high risk, test everything
        if code_change_impact['risk_level'] == 'high':
            test_suite['test_templates'] = self.templates
            test_suite['rationale'].append("HIGH RISK: Testing all templates")
        
        test_suite['total_templates'] = len(test_suite['test_templates'])
        
        return test_suite
    
    def generate_pytest_code(self, test_suite: Dict) -> str:
        """
        Generate pytest code for the test suite.
        
        Args:
            test_suite: Output from generate_test_suite()
            
        Returns:
            Python test code as string
        """
        test_code = '''"""
Auto-generated test suite for logo automation changes.
Generated by AI Test Generator.
"""

import pytest
from logo_addition_diagnostics.temp_logo_adding_FINAL import TemplateLogo Processor

@pytest.fixture
def processor():
    """Create template processor instance."""
    return TemplateLogoProcessor()

'''
        
        # Generate test for each template
        for template in test_suite['test_templates']:
            template_id = template['id']
            template_name = template['name'].replace(' ', '_').replace('-', '_')
            
            test_code += f'''
def test_{template_name}_{template_id[:8]}(processor):
    """Test: {template['name']}"""
    result = processor.process_template("{template_id}")
    
    # Expected outcomes based on category
    category = "{template['category']}"
    
    if "Has Header Already" in category:
        assert result['action'] == 'skipped', "Should skip templates with headers"
    elif "No Extra Logos" in category:
        assert result['logos_processed'] == 0, "Should not add logos to complete templates"
    elif "Has Extra Logos" in category:
        # Verify guardrails prevented duplicates
        assert result['logos_processed'] <= result['total_logo_rows'], "No duplicate logos per row"
    
    assert result['success'], f"Template processing failed: {{result.get('error')}}"

'''
        
        return test_code
    
    def save_test_suite(self, test_suite: Dict, output_path: str = 'generated_tests.py'):
        """Save generated test suite to file."""
        test_code = self.generate_pytest_code(test_suite)
        
        with open(output_path, 'w') as f:
            f.write(test_code)
        
        print(f"✅ Generated test suite: {output_path}")
        print(f"📊 Total tests: {test_suite['total_templates']}")
        print(f"⚠️  Risk level: {test_suite['risk_level']}")
        print(f"📋 Rationale:")
        for reason in test_suite['rationale']:
            print(f"   - {reason}")
