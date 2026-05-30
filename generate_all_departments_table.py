#!/usr/bin/env python3
"""
Generate Complete Templates Table - All Departments
Fetches templates from ALL departments and creates comprehensive table
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import pandas as pd
from smart_template_filter_builder import SmartTemplateFilterBuilder
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class CompleteTemplatesTableGenerator:
    """
    Generates complete table of ALL templates from ALL departments
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.all_templates = []
        self.templates_by_dept = {}
    
    async def connect_to_browser(self):
        """Connect to browser"""
        logger.info("🔌 Connecting to browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9223")
        self.context = self.browser.contexts[0]
        
        # Find template list page
        for page in self.context.pages:
            if 'templates/list' in page.url:
                self.page = page
                logger.info(f"✅ Connected to template list page")
                return True
        
        logger.error("❌ Template list page not found")
        return False
    
    async def fetch_department_templates(self, department, comm_types=None):
        """
        Fetch templates for a specific department using grouped payload
        """
        if not comm_types:
            comm_types = ["EMAIL", "TEXT", "CHAT"]
        
        builder = SmartTemplateFilterBuilder()
        
        # Build grouped payload for this department
        payload = builder.build_grouped_payload(
            departments=[department],
            comm_types=comm_types,
            status=["ACTIVE"],
            max_results=500
        )
        
        try:
            response = await self.page.evaluate("""
                async (payload) => {
                    const response = await fetch('/api/templatestore/u/search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });
                    return await response.json();
                }
            """, payload)
            
            templates = []
            
            # Check for grouped response
            if 'data' in response and 'groups' in response['data']:
                groups = response['data']['groups']
                for group in groups:
                    if 'hits' in group:
                        templates.extend(group['hits'])
            
            # Check for flat response
            elif 'data' in response and 'hits' in response['data']:
                templates = response['data']['hits']
            
            return templates
        
        except Exception as e:
            logger.error(f"Error fetching {department}: {e}")
            return []
    
    async def fetch_all_departments(self):
        """
        Fetch templates from all departments
        """
        logger.info("=" * 80)
        logger.info("📋 FETCHING TEMPLATES FROM ALL DEPARTMENTS")
        logger.info("=" * 80)
        
        departments = ["SERVICE", "SALES", "PARTS", "ACCOUNTING", "GENERAL"]
        comm_types = ["EMAIL", "TEXT", "CHAT", "SMS"]
        
        all_template_ids = set()  # To avoid duplicates
        
        for dept in departments:
            logger.info(f"\n🏢 Fetching {dept} department...")
            
            templates = await self.fetch_department_templates(dept, comm_types)
            
            if templates:
                logger.info(f"  ✅ Found {len(templates)} templates")
                
                # Track which department we fetched this from
                new_templates = 0
                for template in templates:
                    template_id = template.get('templateId') or template.get('id')
                    
                    # Only add if we haven't seen this template yet
                    if template_id not in all_template_ids:
                        all_template_ids.add(template_id)
                        template['fetched_from_dept'] = dept
                        self.all_templates.append(template)
                        new_templates += 1
                
                logger.info(f"  ➕ Added {new_templates} new templates (rest were duplicates)")
                self.templates_by_dept[dept] = len(templates)
            else:
                logger.info(f"  ⚪ No templates found")
                self.templates_by_dept[dept] = 0
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        logger.info(f"\n✅ Total unique templates fetched: {len(self.all_templates)}")
        return self.all_templates
    
    def create_comprehensive_table(self, templates):
        """
        Create detailed table with all template information
        """
        logger.info("=" * 80)
        logger.info("📊 CREATING COMPREHENSIVE TABLE")
        logger.info("=" * 80)
        
        table_data = []
        
        for template in templates:
            row = {
                'Template ID': template.get('templateId') or template.get('id'),
                'MongoDB ID': template.get('id'),
                'Name': template.get('name', 'Unknown'),
                'Departments': ', '.join(template.get('departments', [])),
                'Fetched From': template.get('fetched_from_dept', 'N/A'),
                'Communication Type': template.get('purposeSubType', 'N/A'),
                'Status': template.get('status', 'N/A'),
                'Category': template.get('category', 'N/A'),
                'Visible on UI': template.get('visibleOnUI', False),
                'Created Date': pd.to_datetime(template.get('createdTime'), unit='ms').strftime('%Y-%m-%d %H:%M:%S') if template.get('createdTime') else 'N/A',
                'Modified Date': pd.to_datetime(template.get('modifiedTime'), unit='ms').strftime('%Y-%m-%d %H:%M:%S') if template.get('modifiedTime') else 'N/A',
                'Description': (template.get('description') or 'N/A')[:100],  # Truncate long descriptions
                'Edit URL': f"https://preprodapp.tekioncloud.com/templates/edit/{template.get('templateId') or template.get('id')}"
            }
            table_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(table_data)
        
        # Sort by fetched department, then comm type, then name
        df = df.sort_values(['Fetched From', 'Communication Type', 'Name'])
        
        logger.info(f"✅ Created table with {len(df)} rows and {len(df.columns)} columns")
        
        return df
    
    def save_table(self, df):
        """
        Save table in multiple formats
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []
        
        logger.info("=" * 80)
        logger.info("💾 SAVING TABLE")
        logger.info("=" * 80)
        
        # CSV
        filename = f"all_templates_{timestamp}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"✅ CSV: {filename}")
        saved_files.append(filename)
        
        # Excel with formatting
        filename_excel = f"all_templates_{timestamp}.xlsx"
        with pd.ExcelWriter(filename_excel, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='All Templates')
            
            # Get worksheet
            worksheet = writer.sheets['All Templates']
            
            # Auto-adjust column widths
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        logger.info(f"✅ Excel: {filename_excel}")
        saved_files.append(filename_excel)
        
        # JSON
        filename_json = f"all_templates_{timestamp}.json"
        df.to_json(filename_json, orient='records', indent=2)
        logger.info(f"✅ JSON: {filename_json}")
        saved_files.append(filename_json)
        
        return saved_files
    
    def print_summary(self, df):
        """
        Print comprehensive summary
        """
        logger.info("\n" + "=" * 80)
        logger.info("📈 SUMMARY STATISTICS")
        logger.info("=" * 80)
        
        logger.info(f"\n📊 Total Templates: {len(df)}")
        
        logger.info(f"\n🏢 By Department (where fetched from):")
        for dept, count in self.templates_by_dept.items():
            logger.info(f"  {dept}: {count}")
        
        logger.info(f"\n📧 By Communication Type:")
        type_counts = df['Communication Type'].value_counts()
        for comm_type, count in type_counts.items():
            logger.info(f"  {comm_type}: {count}")
        
        logger.info(f"\n✅ By Status:")
        status_counts = df['Status'].value_counts()
        for status, count in status_counts.items():
            logger.info(f"  {status}: {count}")


async def main():
    generator = CompleteTemplatesTableGenerator()
    
    try:
        # Connect
        if not await generator.connect_to_browser():
            return
        
        # Fetch from all departments
        templates = await generator.fetch_all_departments()
        
        if not templates:
            logger.error("❌ No templates fetched")
            return
        
        # Create table
        df = generator.create_comprehensive_table(templates)
        
        # Save
        saved_files = generator.save_table(df)
        
        # Summary
        generator.print_summary(df)
        
        # Show sample
        logger.info("\n" + "=" * 80)
        logger.info("📋 SAMPLE (First 15 Templates)")
        logger.info("=" * 80)
        print("\n" + df[['Name', 'Departments', 'Communication Type', 'Status']].head(15).to_string(index=False))
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ COMPLETE - TABLE GENERATION SUCCESSFUL")
        logger.info("=" * 80)
        logger.info(f"\n📄 Saved files:")
        for file in saved_files:
            logger.info(f"  {file}")
    
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
