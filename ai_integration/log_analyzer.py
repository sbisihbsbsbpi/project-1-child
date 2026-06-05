"""
AI-Powered Log Analyzer

Uses LLM (GPT-4 or Claude) to analyze automation logs and diagnose failures.
"""

import os
import re
from typing import Dict, List, Optional
from datetime import datetime
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()


class AILogAnalyzer:
    """
    Analyzes automation logs using AI to identify root causes and suggest fixes.
    """
    
    def __init__(self, provider: str = 'openai'):
        """
        Initialize the log analyzer.
        
        Args:
            provider: 'openai' or 'anthropic'
        """
        self.provider = provider
        
        if provider == 'openai' and OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                print("⚠️  OPENAI_API_KEY not found in .env")
                self.client = None
        elif provider == 'anthropic' and ANTHROPIC_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.client = Anthropic(api_key=api_key)
            else:
                print("⚠️  ANTHROPIC_API_KEY not found in .env")
                self.client = None
        else:
            print(f"⚠️  Provider {provider} not available. Install: pip install {provider}")
            self.client = None
        
        # Load historical patterns
        self.known_patterns = self._load_known_patterns()
    
    def _load_known_patterns(self) -> Dict:
        """Load known error patterns from previous fixes."""
        return {
            'duplicate_logos': {
                'pattern': r'⏭️\s+Skipping.*already has a logo',
                'cause': 'Guardrail preventing duplicate logos',
                'related_fix': 'FIX #2: Two-Pass Processing'
            },
            'header_misidentification': {
                'pattern': r'Header.*misidentified.*Logo 1/2',
                'cause': 'Header detection running before logo validation',
                'related_fix': 'FIX #6: Header Misidentification Prevention'
            },
            'wrong_department': {
                'pattern': r'Skipping logo.*wrong department',
                'cause': 'Logo department mismatch with template',
                'related_fix': 'Department verification check'
            },
            'non_standard_template': {
                'pattern': r'Non-standard template.*header',
                'cause': 'Template has logos but non-standard structure',
                'related_fix': 'FIX #5 & #7: Header button and logo table checks'
            }
        }
    
    def extract_errors(self, log_content: str) -> List[Dict]:
        """Extract error patterns from log content."""
        errors = []
        
        # Find all templates that failed or were skipped
        template_sections = re.split(r'={100}', log_content)
        
        for section in template_sections:
            # Extract template name
            template_match = re.search(r'TEMPLATE \d+/\d+: (.+)', section)
            if not template_match:
                continue
            
            template_name = template_match.group(1)
            
            # Check for known error patterns
            for error_type, pattern_info in self.known_patterns.items():
                if re.search(pattern_info['pattern'], section):
                    errors.append({
                        'template': template_name,
                        'error_type': error_type,
                        'cause': pattern_info['cause'],
                        'fix': pattern_info['related_fix'],
                        'excerpt': section[:500]
                    })
        
        return errors
    
    def diagnose_failure(self, log_path: str) -> Dict:
        """
        Diagnose failures from a log file.
        
        Args:
            log_path: Path to log file
            
        Returns:
            Diagnosis dict with root cause and suggestions
        """
        # Read log file
        with open(log_path, 'r') as f:
            log_content = f.read()
        
        # Extract known errors
        errors = self.extract_errors(log_content)
        
        # If no AI client, return pattern-based analysis only
        if not self.client:
            return {
                'analysis_type': 'pattern-based',
                'errors_found': len(errors),
                'patterns_matched': errors,
                'suggestions': self._generate_basic_suggestions(errors)
            }
        
        # Use AI for deeper analysis
        return self._ai_diagnose(log_content, errors)
    
    def _ai_diagnose(self, log_content: str, known_errors: List[Dict]) -> Dict:
        """Use AI to analyze logs."""
        # Prepare prompt
        prompt = self._create_diagnosis_prompt(log_content, known_errors)
        
        # Get AI response
        if self.provider == 'openai':
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert in debugging automation scripts for logo detection and processing."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )
            analysis = response.choices[0].message.content
        else:  # anthropic
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            analysis = response.content[0].text
        
        return {
            'analysis_type': 'ai-powered',
            'errors_found': len(known_errors),
            'known_patterns': known_errors,
            'ai_analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_diagnosis_prompt(self, log_content: str, errors: List) -> str:
        """Create a prompt for AI diagnosis."""
        # Truncate log if too long
        log_excerpt = log_content[-5000:] if len(log_content) > 5000 else log_content
        
        return f"""
Analyze this logo automation log and provide a diagnosis.

KNOWN ERROR PATTERNS DETECTED:
{json.dumps(errors, indent=2)}

LOG EXCERPT (last 5000 chars):
{log_excerpt}

Please provide:
1. Root cause analysis
2. Which guardrail failed (if any)
3. Suggested fix with code snippets
4. Priority level (critical/high/medium/low)
5. Similar past issues (if identifiable)

Format your response as JSON.
"""
    
    def _generate_basic_suggestions(self, errors: List[Dict]) -> List[str]:
        """Generate basic suggestions from pattern matching."""
        suggestions = []
        error_types = set(e['error_type'] for e in errors)
        
        for error_type in error_types:
            if error_type == 'duplicate_logos':
                suggestions.append("Check two-pass processing logic (FIX #2)")
            elif error_type == 'header_misidentification':
                suggestions.append("Verify header detection runs after logo detection (FIX #6)")
            elif error_type == 'wrong_department':
                suggestions.append("Validate department matching logic")
            elif error_type == 'non_standard_template':
                suggestions.append("Check header button opacity and logo table count (FIX #5 & #7)")
        
        return suggestions
