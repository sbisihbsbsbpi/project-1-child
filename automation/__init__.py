"""
Tekion Templates Automation Library
====================================

This package provides automation tools for Tekion CRM Templates module.

Modules:
    - department_filter_automation: Change department filter selections
    - clear_filters_automation: Click Clear button to reset all filters

Usage:
    from automation.department_filter_automation import change_department_filter
    from automation.clear_filters_automation import click_clear_button

    # Change department filter
    result = await change_department_filter(
        departments_to_select=['Service', 'Parts'],
        departments_to_unselect=['Sales']
    )

    # Clear all filters
    result = await click_clear_button()
"""

__version__ = '1.1.0'
__author__ = 'Automation Team'
__status__ = 'Active Development'

from .department_filter_automation import change_department_filter
from .clear_filters_automation import click_clear_button

__all__ = ['change_department_filter', 'click_clear_button']
