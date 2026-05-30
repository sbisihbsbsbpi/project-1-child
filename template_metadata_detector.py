#!/usr/bin/env python3
"""
Template Metadata Detector
Analyzes the template list page to detect Department, Communication Type, Category filters
and builds the search API payload dynamically
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class TemplateMetadataDetector:
    """
    Detects template metadata from the UI:
    - Department (e.g., SERVICE, SALES, PARTS)
    - Communication Type (e.g., EMAIL, SMS)
    - Category
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def connect_to_browser(self):
        """Connect to existing browser"""
        logger.info("🔌 Connecting to browser...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9223")
        self.context = self.browser.contexts[0]
        
        logger.info(f"✅ Connected! Found {len(self.context.pages)} tab(s)")
    
    async def find_template_list_page(self):
        """Find or navigate to template list page"""
        logger.info("🔍 Finding template list page...")
        
        # Check if template list already open
        for page in self.context.pages:
            if 'templates/list' in page.url:
                self.page = page
                logger.info(f"✅ Found template list: {page.url}")
                return True
        
        logger.warning("⚠️  Template list page not found")
        return False
    
    async def detect_active_filters(self):
        """
        Detect currently active filters from the UI
        Analyzes dropdowns, checkboxes, and selected filters
        """
        logger.info("=" * 80)
        logger.info("🔍 DETECTING ACTIVE FILTERS FROM UI")
        logger.info("=" * 80)
        
        # Extract filter information from the page
        filters = await self.page.evaluate("""
            () => {
                const result = {
                    departments: [],
                    communicationTypes: [],
                    categories: [],
                    status: [],
                    otherFilters: {}
                };
                
                // Strategy 1: Look for selected dropdown values
                const dropdowns = document.querySelectorAll('select, [role="combobox"], [role="listbox"]');
                
                dropdowns.forEach(dropdown => {
                    const label = dropdown.getAttribute('aria-label') || 
                                 dropdown.getAttribute('name') || 
                                 dropdown.id || '';
                    
                    const value = dropdown.value || 
                                 dropdown.getAttribute('data-value') ||
                                 dropdown.textContent?.trim();
                    
                    if (label.toLowerCase().includes('department') && value) {
                        result.departments.push(value);
                    } else if (label.toLowerCase().includes('type') || label.toLowerCase().includes('communication')) {
                        if (value) result.communicationTypes.push(value);
                    } else if (label.toLowerCase().includes('category')) {
                        if (value) result.categories.push(value);
                    } else if (label.toLowerCase().includes('status')) {
                        if (value) result.status.push(value);
                    }
                });
                
                // Strategy 2: Look for filter chips/tags (selected filters shown as chips)
                const chips = document.querySelectorAll('[class*="chip"], [class*="tag"], [class*="filter"], [class*="badge"]');
                
                chips.forEach(chip => {
                    const text = chip.textContent?.trim() || '';
                    const chipClass = chip.className || '';
                    
                    // Common department values
                    if (['SERVICE', 'SALES', 'PARTS', 'ACCOUNTING', 'GENERAL'].includes(text.toUpperCase())) {
                        if (!result.departments.includes(text.toUpperCase())) {
                            result.departments.push(text.toUpperCase());
                        }
                    }
                    
                    // Common communication types
                    if (['EMAIL', 'SMS', 'PUSH', 'VOICE'].includes(text.toUpperCase())) {
                        if (!result.communicationTypes.includes(text.toUpperCase())) {
                            result.communicationTypes.push(text.toUpperCase());
                        }
                    }
                    
                    // Status
                    if (['ACTIVE', 'INACTIVE', 'DRAFT'].includes(text.toUpperCase())) {
                        if (!result.status.includes(text.toUpperCase())) {
                            result.status.push(text.toUpperCase());
                        }
                    }
                });
                
                // Strategy 3: Look for checked checkboxes
                const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
                
                checkboxes.forEach(checkbox => {
                    const label = checkbox.labels?.[0]?.textContent?.trim() || 
                                 checkbox.getAttribute('aria-label') ||
                                 checkbox.getAttribute('name') || '';
                    
                    if (label) {
                        const upperLabel = label.toUpperCase();
                        
                        if (['SERVICE', 'SALES', 'PARTS', 'ACCOUNTING', 'GENERAL'].includes(upperLabel)) {
                            if (!result.departments.includes(upperLabel)) {
                                result.departments.push(upperLabel);
                            }
                        } else if (['EMAIL', 'SMS', 'PUSH', 'VOICE'].includes(upperLabel)) {
                            if (!result.communicationTypes.includes(upperLabel)) {
                                result.communicationTypes.push(upperLabel);
                            }
                        } else if (['ACTIVE', 'INACTIVE', 'DRAFT'].includes(upperLabel)) {
                            if (!result.status.includes(upperLabel)) {
                                result.status.push(upperLabel);
                            }
                        }
                    }
                });
                
                // Strategy 4: Look for URL parameters
                const urlParams = new URLSearchParams(window.location.search);
                
                if (urlParams.has('department')) {
                    const dept = urlParams.get('department').toUpperCase();
                    if (!result.departments.includes(dept)) {
                        result.departments.push(dept);
                    }
                }
                
                if (urlParams.has('type')) {
                    const type = urlParams.get('type').toUpperCase();
                    if (!result.communicationTypes.includes(type)) {
                        result.communicationTypes.push(type);
                    }
                }
                
                return result;
            }
        """)
        
        logger.info("🎯 Detected Filters:")
        logger.info(f"  Departments: {filters['departments'] or '(none)'}")
        logger.info(f"  Communication Types: {filters['communicationTypes'] or '(none)'}")
        logger.info(f"  Categories: {filters['categories'] or '(none)'}")
        logger.info(f"  Status: {filters['status'] or '(none)'}")

        return filters

    async def intercept_search_api(self):
        """
        Intercept the search API call to see the actual payload
        """
        logger.info("=" * 80)
        logger.info("🎯 INTERCEPTING SEARCH API CALL")
        logger.info("=" * 80)

        api_payloads = []
        response_received = asyncio.Event()

        async def handle_request(route, request):
            """Intercept requests"""
            if '/api/templatestore/u/search' in request.url:
                try:
                    # Get the request payload
                    post_data = request.post_data

                    if post_data:
                        payload = json.loads(post_data)
                        api_payloads.append({
                            'url': request.url,
                            'method': request.method,
                            'payload': payload,
                            'headers': request.headers
                        })

                        logger.info("✅ Intercepted API Request:")
                        logger.info(f"  URL: {request.url}")
                        logger.info(f"  Method: {request.method}")
                        logger.info(f"  Payload:")
                        logger.info(json.dumps(payload, indent=2))

                        response_received.set()

                except Exception as e:
                    logger.error(f"Error intercepting request: {e}")

            # Continue the request
            await route.continue_()

        # Enable request interception
        await self.page.route('**/*', handle_request)

        # Trigger a search by reloading
        logger.info("🔄 Reloading page to trigger search API...")
        await self.page.reload()

        # Wait for API call
        try:
            await asyncio.wait_for(response_received.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("⚠️  Timeout waiting for API call")

        # Disable interception
        await self.page.unroute('**/*')

        return api_payloads

    def build_search_payload(self, filters: dict, max_results: int = 200):
        """
        Build the search API payload based on detected filters
        """
        logger.info("=" * 80)
        logger.info("🔧 BUILDING SEARCH PAYLOAD")
        logger.info("=" * 80)

        # Start with base payload structure
        payload = {
            "sort": [{"field": "modifiedTime", "order": "DESC"}],
            "filters": [],
            "searchText": "",
            "groupBy": [],
            "includeFields": [],
            "searchableFields": ["name"],
            "excludeFields": ["body", "htmlBody", "subject", "htmlSubject", "preHeader", "languages"],
            "pageInfo": {"start": 0, "rows": max_results}
        }

        # Add status filter (default to ACTIVE)
        status_values = filters.get('status', []) or ['ACTIVE']
        payload['filters'].append({
            "field": "status",
            "operator": "IN",
            "values": status_values,
            "key": "status"
        })

        # Add communication type filter (e.g., EMAIL)
        if filters.get('communicationTypes'):
            payload['filters'].append({
                "field": "purposeSubType",
                "operator": "IN",
                "values": filters['communicationTypes'],
                "key": "purposeSubType"
            })

        # Add department filter (e.g., SERVICE)
        if filters.get('departments'):
            payload['filters'].append({
                "field": "departments",
                "operator": "IN",
                "values": filters['departments']
            })

        # Add category filter if present
        if filters.get('categories'):
            payload['filters'].append({
                "field": "category",
                "operator": "IN",
                "values": filters['categories']
            })

        # Add visibleOnUI filter (common in Tekion)
        payload['filters'].append({
            "field": "visibleOnUI",
            "operator": "IN",
            "values": [True],
            "key": "visibleOnUI"
        })

        logger.info("✅ Built search payload:")
        logger.info(json.dumps(payload, indent=2))

        return payload

    async def test_search_with_payload(self, payload: dict):
        """
        Test the search API with the built payload
        """
        logger.info("=" * 80)
        logger.info("🧪 TESTING SEARCH API WITH PAYLOAD")
        logger.info("=" * 80)

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

            if response and 'data' in response and 'hits' in response['data']:
                hits = response['data']['hits']
                logger.info(f"✅ API Response successful!")
                logger.info(f"  Total hits: {len(hits)}")

                logger.info(f"\n📋 First 5 templates:")
                for idx, template in enumerate(hits[:5], 1):
                    logger.info(f"  {idx}. {template.get('name', 'Unknown')}")
                    logger.info(f"     - ID: {template.get('templateId', template.get('id'))}")
                    logger.info(f"     - Department: {template.get('departments', [])}")
                    logger.info(f"     - Type: {template.get('purposeSubType', 'N/A')}")

                return response
            else:
                logger.error("❌ API response format unexpected")
                logger.error(json.dumps(response, indent=2))
                return None

        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            return None


async def main():
    """
    Main workflow:
    1. Connect to browser
    2. Find template list page
    3. Detect active filters from UI
    4. Intercept search API call
    5. Build search payload
    6. Test search API
    """
    detector = TemplateMetadataDetector()

    try:
        # Connect
        await detector.connect_to_browser()

        # Find template list page
        if not await detector.find_template_list_page():
            logger.error("Please open the template list page first")
            return

        # Method 1: Detect filters from UI
        logger.info("\n" + "=" * 80)
        logger.info("METHOD 1: DETECT FROM UI")
        logger.info("=" * 80)
        ui_filters = await detector.detect_active_filters()

        # Method 2: Intercept actual API call
        logger.info("\n" + "=" * 80)
        logger.info("METHOD 2: INTERCEPT ACTUAL API CALL")
        logger.info("=" * 80)
        api_payloads = await detector.intercept_search_api()

        # Save intercepted payloads
        if api_payloads:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intercepted_search_payload_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(api_payloads, f, indent=2)
            logger.info(f"\n💾 Saved intercepted payload to: {filename}")

        # Build payload from detected filters
        logger.info("\n" + "=" * 80)
        logger.info("METHOD 3: BUILD FROM DETECTED FILTERS")
        logger.info("=" * 80)
        custom_payload = detector.build_search_payload(ui_filters, max_results=200)

        # Test the custom payload
        await detector.test_search_with_payload(custom_payload)

        logger.info("\n" + "=" * 80)
        logger.info("✅ DETECTION COMPLETE")
        logger.info("=" * 80)

    finally:
        # Keep browser open
        pass


if __name__ == "__main__":
    asyncio.run(main())

