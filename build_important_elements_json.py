#!/usr/bin/env python3
"""
Build JSON for Important Elements Only
Based on user feedback - focus on critical UI elements
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🎯 BUILDING IMPORTANT ELEMENTS JSON")
    print("=" * 100)
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            print("🌐 Navigating to templates page...")
            await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(4)
            
            print("🔍 Detecting important elements...\n")
            
            # Detect important elements
            elements = await page.evaluate("""
                () => {
                    const important = {
                        metadata: {
                            page_title: document.title,
                            url: window.location.href,
                            timestamp: new Date().toISOString()
                        },
                        elements: []
                    };
                    
                    let elementCounter = 1;
                    
                    function addElement(selector, label, type, extraData = {}) {
                        const el = document.querySelector(selector);
                        if (el && el.offsetParent !== null) {
                            const rect = el.getBoundingClientRect();
                            important.elements.push({
                                id: elementCounter++,
                                label: label,
                                type: type,
                                selector: selector,
                                text: el.textContent.trim().substring(0, 100),
                                className: el.className.substring(0, 100),
                                position: {
                                    x: Math.round(rect.left),
                                    y: Math.round(rect.top),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                },
                                visible: el.offsetParent !== null,
                                ...extraData
                            });
                            return true;
                        }
                        return false;
                    }
                    
                    // 1. DEPARTMENT FILTER
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    if (deptFilter) {
                        const cleanText = deptFilter.textContent.split('}').pop().trim();
                        const rect = deptFilter.getBoundingClientRect();
                        important.elements.push({
                            id: elementCounter++,
                            label: "Department Filter",
                            type: "dropdown",
                            selector: ".ant-dropdown-trigger",
                            text: cleanText,
                            full_text: deptFilter.textContent,
                            className: deptFilter.className,
                            position: {
                                x: Math.round(rect.left),
                                y: Math.round(rect.top),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            },
                            visible: true,
                            purpose: "Filter templates by department (Sales, Service, Parts, etc.)"
                        });
                    }
                    
                    // 2. DRAFTS BUTTON
                    const buttons = Array.from(document.querySelectorAll('button'));
                    buttons.forEach(btn => {
                        const text = btn.textContent.trim();
                        const rect = btn.getBoundingClientRect();
                        
                        if (text.includes('Draft') && btn.offsetParent !== null) {
                            const match = text.match(/Drafts?\\s*\\((\\d+)\\)/);
                            important.elements.push({
                                id: elementCounter++,
                                label: "Drafts Button",
                                type: "button",
                                text: text,
                                count: match ? parseInt(match[1]) : 0,
                                className: btn.className.substring(0, 100),
                                position: {
                                    x: Math.round(rect.left),
                                    y: Math.round(rect.top),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                },
                                visible: true,
                                purpose: "View draft templates"
                            });
                        }
                        
                        // 3. ARCHIVE BUTTON
                        if (text.includes('Archive') && btn.offsetParent !== null) {
                            const match = text.match(/Archive\\s*\\((\\d+)\\)/);
                            important.elements.push({
                                id: elementCounter++,
                                label: "Archive Button",
                                type: "button",
                                text: text,
                                count: match ? parseInt(match[1]) : 0,
                                className: btn.className.substring(0, 100),
                                position: {
                                    x: Math.round(rect.left),
                                    y: Math.round(rect.top),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                },
                                visible: true,
                                purpose: "View archived templates"
                            });
                        }
                        
                        // 4. NEW TEMPLATE BUTTON
                        if (text.includes('New Template') && btn.offsetParent !== null) {
                            important.elements.push({
                                id: elementCounter++,
                                label: "New Template Button",
                                type: "button",
                                text: text,
                                className: btn.className.substring(0, 100),
                                position: {
                                    x: Math.round(rect.left),
                                    y: Math.round(rect.top),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                },
                                visible: true,
                                disabled: btn.disabled,
                                purpose: "Create a new template"
                            });
                        }
                    });
                    
                    // 5. PAGE SIZE DROPDOWN (Select50)
                    const pageSize = document.querySelector('[role="combobox"]');
                    if (pageSize) {
                        const rect = pageSize.getBoundingClientRect();
                        important.elements.push({
                            id: elementCounter++,
                            label: "Page Size Dropdown",
                            type: "dropdown",
                            selector: '[role="combobox"]',
                            text: pageSize.textContent.trim(),
                            className: pageSize.className.substring(0, 100),
                            position: {
                                x: Math.round(rect.left),
                                y: Math.round(rect.top),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            },
                            visible: true,
                            aria_expanded: pageSize.getAttribute('aria-expanded'),
                            purpose: "Set number of items per page"
                        });
                    }
