"""
AI Integration Module for Logo Automation

This module provides AI-powered capabilities to detect and fix logic issues
in the logo automation system.
"""

__version__ = '1.0.0'
__author__ = 'Logo Automation Team'

from .pattern_classifier import TemplateClassifier
from .log_analyzer import AILogAnalyzer
from .test_generator import TestGenerator
from .ai_assistant import AIAssistant

__all__ = [
    'TemplateClassifier',
    'AILogAnalyzer',
    'TestGenerator',
    'AIAssistant',
]
