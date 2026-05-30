#!/usr/bin/env python3
"""
Generate Templates Table
Creates a comprehensive table of all templates with metadata
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


class TemplateTableGenerator:
    """
    Generates comprehensive table of all templates
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.all_templates = []
    
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
    
    async def fetch_all_templates(self, departments=None, comm_types=None):
        """
        Fetch all templates using API interception (reload page method)
        """
        logger.info("=" * 80)
        logger.info("📋 FETCHING ALL TEMPLATES VIA INTERCEPTION")
        logger.info("=" * 80)

        # We'll intercept the response when page reloads
        api_data = []
        response_received = asyncio.Event()

        async def handle_response(response):
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()

                    if 'data' in data and 'hits' in data.get('data', {}):
                        hits = data['data']['hits']
                        if hits and len(api_data) == 0:  # Only first response
                            logger.info(f"✅ Intercepted response with {len(hits)} templates")
                            api_data.extend(hits)
                            response_received.set()

                    # Also check grouped format
                    elif 'data' in data and 'groups' in data.get('data', {}):
                        groups = data['data']['groups']
                        total = 0
                        for group in groups:
                            if 'hits' in group:
                                total += len(group['hits'])
                                api_data.extend(group['hits'])

                        if total > 0 and len(api_data) > 0:
                            logger.info(f"✅ Intercepted grouped response with {total} templates")
                            response_received.set()

                except Exception as e:
                    logger.error(f"Error parsing response: {e}")

        # Listen for responses
        self.page.on('response', handle_response)

        # Reload to trigger API call
        logger.info("🔄 Reloading page to trigger API...")
        await self.page.reload()

        # Wait for response
        try:
            await asyncio.wait_for(response_received.wait(), timeout=15.0)
        except asyncio.TimeoutError:
            logger.warning("⚠️  Timeout waiting for API")

        # Remove listener
        self.page.remove_listener('response', handle_response)

        self.all_templates = api_data
        logger.info(f"\n✅ Total templates fetched: {len(self.all_templates)}")
        return self.all_templates
    
    def create_table(self, templates):
        """
        Create a pandas DataFrame with all template information
        """
        logger.info("=" * 80)
        logger.info("📊 CREATING TEMPLATES TABLE")
        logger.info("=" * 80)
        
        table_data = []
        
        for template in templates:
            row = {
                'Template ID': template.get('templateId') or template.get('id'),
                'MongoDB ID': template.get('id'),
                'Name': template.get('name', 'Unknown'),
                'Department': ', '.join(template.get('departments', [])),
                'Communication Type': template.get('purposeSubType', 'N/A'),
                'Status': template.get('status', 'N/A'),
                'Category': template.get('category', 'N/A'),
                'Visible on UI': template.get('visibleOnUI', False),
                'Created Date': template.get('createdTime', 'N/A'),
                'Modified Date': template.get('modifiedTime', 'N/A'),
                'Created By': template.get('createdBy', 'N/A'),
                'Modified By': template.get('modifiedBy', 'N/A'),
                'Description': template.get('description', 'N/A'),
                'Tags': ', '.join(template.get('tags', [])),
                'Edit URL': f"https://preprodapp.tekioncloud.com/templates/edit/{template.get('templateId') or template.get('id')}"
            }
            table_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(table_data)
        
        # Sort by department, then communication type, then name
        df = df.sort_values(['Department', 'Communication Type', 'Name'])
        
        logger.info(f"✅ Created table with {len(df)} rows and {len(df.columns)} columns")
        
        return df
    
    def save_table(self, df, formats=['csv', 'excel', 'json', 'markdown']):
        """
        Save table in multiple formats
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []
        
        logger.info("=" * 80)
        logger.info("💾 SAVING TABLE")
        logger.info("=" * 80)
        
        # CSV
        if 'csv' in formats:
            filename = f"templates_table_{timestamp}.csv"
            df.to_csv(filename, index=False)
            logger.info(f"✅ CSV: {filename}")
            saved_files.append(filename)
        
        # Excel
        if 'excel' in formats:
            filename = f"templates_table_{timestamp}.xlsx"
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"✅ Excel: {filename}")
            saved_files.append(filename)
        
        # JSON
        if 'json' in formats:
            filename = f"templates_table_{timestamp}.json"
            df.to_json(filename, orient='records', indent=2)
            logger.info(f"✅ JSON: {filename}")
            saved_files.append(filename)
        
        # Markdown
        if 'markdown' in formats:
            filename = f"templates_table_{timestamp}.md"
            with open(filename, 'w') as f:
                f.write("# All Templates\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Total Templates: {len(df)}\n\n")
                f.write(df.to_markdown(index=False))
            logger.info(f"✅ Markdown: {filename}")
            saved_files.append(filename)
        
        return saved_files
    
    def print_summary(self, df):
        """
        Print summary statistics
        """
        logger.info("=" * 80)
        logger.info("📈 SUMMARY STATISTICS")
        logger.info("=" * 80)
        
        logger.info(f"\nTotal Templates: {len(df)}")
        
        logger.info(f"\n📊 By Department:")
        dept_counts = df['Department'].value_counts()
        for dept, count in dept_counts.items():
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
    """
    Main workflow:
    1. Connect to browser
    2. Fetch all templates from all departments
    3. Create comprehensive table
    4. Save in multiple formats
    5. Print summary
    """
    generator = TemplateTableGenerator()
    
    try:
        # Connect
        if not await generator.connect_to_browser():
            return
        
        # Fetch all templates (via interception)
        templates = await generator.fetch_all_templates()
        
        if not templates:
            logger.error("❌ No templates fetched")
            return
        
        # Create table
        df = generator.create_table(templates)
        
        # Save in multiple formats
        saved_files = generator.save_table(df, formats=['csv', 'excel', 'json', 'markdown'])
        
        # Print summary
        generator.print_summary(df)
        
        # Print first few rows
        logger.info("\n" + "=" * 80)
        logger.info("📋 SAMPLE (First 10 Templates)")
        logger.info("=" * 80)
        print("\n" + df[['Name', 'Department', 'Communication Type', 'Status']].head(10).to_string(index=False))
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TABLE GENERATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"\nSaved files:")
        for file in saved_files:
            logger.info(f"  📄 {file}")
    
    finally:
        # Keep browser open
        pass


if __name__ == "__main__":
    asyncio.run(main())
