"""
Template Page Comprehensive Detector
Detects ALL elements, filters, metadata, and UI components on Tekion templates list page
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime
from playwright.async_api import Page, Browser
import json

logger = logging.getLogger(__name__)


class TemplatePageDetector:
    """Comprehensive detector for Tekion templates page"""
    
    def __init__(self):
        logger.info("🔍 Template Page Detector initialized")
    
    async def detect_all(self, browser: Browser, base_url: str = "https://preprodapp.tekioncloud.com") -> Dict[str, Any]:
        """
        Detect EVERYTHING on the templates list page
        Returns comprehensive analysis of all elements
        """
        
        logger.info("=" * 80)
        logger.info("🔍 COMPREHENSIVE TEMPLATE PAGE DETECTION")
        logger.info("=" * 80)
        
        detection_results = {
            "timestamp": datetime.now().isoformat(),
            "url": f"{base_url}/templates/list",
            "page_info": {},
            "filters": {},
            "ui_elements": {},
            "templates": [],
            "api_data": {},
            "interactions": {},
            "metadata": {}
        }
        
        try:
            # Get browser context
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await context.new_page()
            
            logger.info(f"🌐 Navigating to {base_url}/templates/list")
            await page.goto(f"{base_url}/templates/list", wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(3)
            
            # 1. PAGE INFO
            logger.info("\n📄 DETECTING PAGE INFORMATION...")
            detection_results["page_info"] = await self._detect_page_info(page)
            
            # 2. FILTERS & DROPDOWNS
            logger.info("\n🎛️ DETECTING FILTERS...")
            detection_results["filters"] = await self._detect_filters(page)
            
            # 3. UI ELEMENTS
            logger.info("\n🖼️ DETECTING UI ELEMENTS...")
            detection_results["ui_elements"] = await self._detect_ui_elements(page)
            
            # 4. TEMPLATES VIA API
            logger.info("\n📡 DETECTING TEMPLATES VIA API...")
            detection_results["templates"] = await self._detect_templates_api(page)
            
            # 5. API ENDPOINTS
            logger.info("\n🌐 DETECTING API CALLS...")
            detection_results["api_data"] = await self._detect_api_calls(page)
            
            # 6. INTERACTIVE ELEMENTS
            logger.info("\n🖱️ DETECTING INTERACTIVE ELEMENTS...")
            detection_results["interactions"] = await self._detect_interactions(page)
            
            # 7. METADATA
            logger.info("\n📊 DETECTING METADATA...")
            detection_results["metadata"] = await self._detect_metadata(page)
            
            # 8. FORM ELEMENTS
            logger.info("\n📝 DETECTING FORM ELEMENTS...")
            detection_results["forms"] = await self._detect_forms(page)
            
            # 9. NAVIGATION
            logger.info("\n🧭 DETECTING NAVIGATION...")
            detection_results["navigation"] = await self._detect_navigation(page)
            
            # 10. LAYOUT STRUCTURE
            logger.info("\n📐 DETECTING LAYOUT...")
            detection_results["layout"] = await self._detect_layout(page)
            
            logger.info("\n✅ Detection complete!")
            
            # Save results to file
            self._save_results(detection_results)
            
            return detection_results
            
        except Exception as e:
            logger.exception(f"Error in detection: {e}")
            detection_results["error"] = str(e)
            return detection_results
    
    async def _detect_page_info(self, page: Page) -> Dict[str, Any]:
        """Detect basic page information"""
        
        info = await page.evaluate("""
            () => {
                return {
                    title: document.title,
                    url: window.location.href,
                    domain: window.location.hostname,
                    path: window.location.pathname,
                    hash: window.location.hash,
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    documentReady: document.readyState,
                    cookies: document.cookie ? document.cookie.split(';').length : 0
                };
            }
        """)
        
        logger.info(f"   Title: {info['title']}")
        logger.info(f"   URL: {info['url']}")
        logger.info(f"   Viewport: {info['viewport']['width']}x{info['viewport']['height']}")
        
        return info
    
    async def _detect_filters(self, page: Page) -> Dict[str, Any]:
        """Detect all filter elements and their options"""
        
        filters = await page.evaluate("""
            () => {
                const result = {
                    dropdowns: [],
                    checkboxes: [],
                    chips: [],
                    search_boxes: [],
                    department_filter: null,
                    status_filter: null,
                    type_filter: null
                };
                
                // Detect Department Filter (Ant Design dropdown)
                const deptTrigger = document.querySelector('.ant-dropdown-trigger');
                if (deptTrigger) {
                    result.department_filter = {
                        type: 'ant-dropdown',
                        text: deptTrigger.textContent.trim(),
                        className: deptTrigger.className,
                        visible: deptTrigger.offsetParent !== null
                    };
                }
                
                // Detect all dropdowns/comboboxes
                const comboboxes = document.querySelectorAll('[role="combobox"]');
                comboboxes.forEach(cb => {
                    result.dropdowns.push({
                        role: cb.getAttribute('role'),
                        ariaLabel: cb.getAttribute('aria-label'),
                        ariaExpanded: cb.getAttribute('aria-expanded'),
                        text: cb.textContent.substring(0, 100),
                        className: cb.className.substring(0, 100)
                    });
                });
                
                // Detect checkboxes
                const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(checkbox => {
                    const label = checkbox.nextElementSibling?.textContent || 
                                 checkbox.parentElement?.textContent.substring(0, 50);
                    result.checkboxes.push({
                        checked: checkbox.checked,
                        disabled: checkbox.disabled,
                        label: label,
                        name: checkbox.name,
                        id: checkbox.id
                    });
                });
                
                // Detect filter chips/tags
                const chips = document.querySelectorAll('[class*="chip"], [class*="tag"], [class*="badge"]');
                chips.forEach(chip => {
                    if (chip.offsetParent !== null) {
                        result.chips.push({
                            text: chip.textContent.trim(),
                            className: chip.className.substring(0, 60),
                            hasCloseButton: chip.querySelector('[class*="close"]') !== null
                        });
                    }
                });
                
                // Detect search boxes
                const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="search" i], input[placeholder*="Search"]');
                searchInputs.forEach(input => {
                    result.search_boxes.push({
                        placeholder: input.placeholder,
                        value: input.value,
                        className: input.className.substring(0, 60)
                    });
                });
                
                return result;
            }
        """)
        
        logger.info(f"   Dropdowns: {len(filters['dropdowns'])}")
        logger.info(f"   Checkboxes: {len(filters['checkboxes'])}")
        logger.info(f"   Chips/Tags: {len(filters['chips'])}")
        logger.info(f"   Search Boxes: {len(filters['search_boxes'])}")
        if filters['department_filter']:
            logger.info(f"   Department Filter: {filters['department_filter']['text']}")
        
        return filters

    async def _detect_ui_elements(self, page: Page) -> Dict[str, Any]:
        """Detect all UI elements on the page"""

        elements = await page.evaluate("""
            () => {
                const result = {
                    buttons: [],
                    links: [],
                    tables: [],
                    lists: [],
                    images: [],
                    iframes: [],
                    modals: []
                };

                // Detect buttons
                const buttons = document.querySelectorAll('button');
                buttons.forEach(btn => {
                    if (btn.offsetParent !== null) {
                        result.buttons.push({
                            text: btn.textContent.trim().substring(0, 50),
                            type: btn.type,
                            className: btn.className.substring(0, 60),
                            disabled: btn.disabled,
                            ariaLabel: btn.getAttribute('aria-label')
                        });
                    }
                });

                // Detect links
                const links = document.querySelectorAll('a[href]');
                links.forEach(link => {
                    if (link.offsetParent !== null) {
                        result.links.push({
                            text: link.textContent.trim().substring(0, 50),
                            href: link.href.substring(0, 100),
                            className: link.className.substring(0, 60)
                        });
                    }
                });

                // Detect tables
                const tables = document.querySelectorAll('table');
                tables.forEach(table => {
                    const rows = table.querySelectorAll('tr');
                    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
                    result.tables.push({
                        rows: rows.length,
                        columns: headers.length,
                        headers: headers,
                        className: table.className.substring(0, 60)
                    });
                });

                // Detect lists
                const lists = document.querySelectorAll('ul, ol');
                lists.forEach(list => {
                    const items = list.querySelectorAll('li');
                    if (items.length > 0) {
                        result.lists.push({
                            type: list.tagName,
                            itemCount: items.length,
                            firstItem: items[0]?.textContent.trim().substring(0, 50)
                        });
                    }
                });

                // Detect images
                const images = document.querySelectorAll('img');
                images.forEach(img => {
                    if (img.offsetParent !== null) {
                        result.images.push({
                            src: img.src.substring(0, 100),
                            alt: img.alt,
                            width: img.width,
                            height: img.height
                        });
                    }
                });

                // Detect iframes
                const iframes = document.querySelectorAll('iframe');
                iframes.forEach(iframe => {
                    result.iframes.push({
                        src: iframe.src?.substring(0, 100),
                        title: iframe.title,
                        width: iframe.width,
                        height: iframe.height
                    });
                });

                // Detect modals/dialogs
                const modals = document.querySelectorAll('[role="dialog"], .modal, [class*="modal"]');
                modals.forEach(modal => {
                    if (modal.offsetParent !== null) {
                        result.modals.push({
                            className: modal.className.substring(0, 60),
                            visible: true,
                            title: modal.querySelector('h1, h2, h3')?.textContent.trim()
                        });
                    }
                });

                return result;
            }
        """)

        logger.info(f"   Buttons: {len(elements['buttons'])}")
        logger.info(f"   Links: {len(elements['links'])}")
        logger.info(f"   Tables: {len(elements['tables'])}")
        logger.info(f"   Lists: {len(elements['lists'])}")
        logger.info(f"   Images: {len(elements['images'])}")

        return elements

    async def _detect_templates_api(self, page: Page) -> List[Dict]:
        """Detect templates by intercepting API calls"""

        templates = []
        response_received = asyncio.Event()

        async def handle_response(response):
            nonlocal templates
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    if 'data' in data and 'hits' in data['data']:
                        templates.extend(data['data']['hits'])
                        response_received.set()
                except:
                    pass

        page.on('response', handle_response)

        # Trigger API by reloading
        await page.reload(wait_until='domcontentloaded')

        try:
            await asyncio.wait_for(response_received.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            pass

        page.remove_listener('response', handle_response)

        logger.info(f"   Templates found: {len(templates)}")
        if templates:
            logger.info(f"   First template: {templates[0].get('name', 'Unknown')}")

        return templates

    async def _detect_api_calls(self, page: Page) -> Dict[str, Any]:
        """Detect all API calls and network activity"""

        api_calls = {
            "endpoints": [],
            "methods": {},
            "domains": set()
        }

        requests_data = []

        async def log_request(request):
            requests_data.append({
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "resourceType": request.resource_type
            })

        page.on('request', log_request)

        await page.reload(wait_until='domcontentloaded')
        await asyncio.sleep(2)

        page.remove_listener('request', log_request)

        # Analyze requests
        for req in requests_data:
            url = req['url']
            if '/api/' in url:
                api_calls['endpoints'].append(url)
                method = req['method']
                api_calls['methods'][method] = api_calls['methods'].get(method, 0) + 1

            # Extract domain
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            api_calls['domains'].add(domain)

        api_calls['domains'] = list(api_calls['domains'])

        logger.info(f"   API endpoints called: {len(api_calls['endpoints'])}")
        logger.info(f"   HTTP methods: {api_calls['methods']}")

        return api_calls

    async def _detect_interactions(self, page: Page) -> Dict[str, Any]:
        """Detect interactive elements"""

        interactions = await page.evaluate("""
            () => {
                return {
                    clickable: document.querySelectorAll('[onclick], button, a, [role="button"]').length,
                    hoverable: document.querySelectorAll('[onmouseover], [class*="hover"]').length,
                    draggable: document.querySelectorAll('[draggable="true"]').length,
                    editable: document.querySelectorAll('[contenteditable="true"], textarea, input[type="text"]').length,
                    sortable: document.querySelectorAll('[class*="sort"]').length
                };
            }
        """)

        logger.info(f"   Clickable elements: {interactions['clickable']}")
        logger.info(f"   Editable elements: {interactions['editable']}")

        return interactions

    async def _detect_metadata(self, page: Page) -> Dict[str, Any]:
        """Detect page metadata"""

        metadata = await page.evaluate("""
            () => {
                const metas = {};
                document.querySelectorAll('meta').forEach(meta => {
                    const name = meta.getAttribute('name') || meta.getAttribute('property');
                    const content = meta.getAttribute('content');
                    if (name) {
                        metas[name] = content;
                    }
                });

                return {
                    meta_tags: metas,
                    scripts: document.querySelectorAll('script').length,
                    stylesheets: document.querySelectorAll('link[rel="stylesheet"]').length,
                    fonts: Array.from(document.fonts).map(f => f.family)
                };
            }
        """)

        logger.info(f"   Scripts loaded: {metadata['scripts']}")
        logger.info(f"   Stylesheets: {metadata['stylesheets']}")

        return metadata

    async def _detect_forms(self, page: Page) -> Dict[str, Any]:
        """Detect form elements"""

        forms = await page.evaluate("""
            () => {
                const result = {
                    forms: [],
                    inputs: [],
                    selects: [],
                    textareas: []
                };

                // Forms
                document.querySelectorAll('form').forEach(form => {
                    result.forms.push({
                        action: form.action,
                        method: form.method,
                        elements: form.elements.length
                    });
                });

                // Inputs
                document.querySelectorAll('input').forEach(input => {
                    result.inputs.push({
                        type: input.type,
                        name: input.name,
                        placeholder: input.placeholder,
                        required: input.required
                    });
                });

                // Selects
                document.querySelectorAll('select').forEach(select => {
                    result.selects.push({
                        name: select.name,
                        multiple: select.multiple,
                        options: select.options.length
                    });
                });

                // Textareas
                document.querySelectorAll('textarea').forEach(textarea => {
                    result.textareas.push({
                        name: textarea.name,
                        placeholder: textarea.placeholder,
                        rows: textarea.rows
                    });
                });

                return result;
            }
        """)

        logger.info(f"   Forms: {len(forms['forms'])}")
        logger.info(f"   Input fields: {len(forms['inputs'])}")

        return forms

    async def _detect_navigation(self, page: Page) -> Dict[str, Any]:
        """Detect navigation elements"""

        navigation = await page.evaluate("""
            () => {
                return {
                    nav_elements: document.querySelectorAll('nav').length,
                    breadcrumbs: document.querySelectorAll('[class*="breadcrumb"]').length,
                    pagination: document.querySelectorAll('[class*="pag"]').length,
                    tabs: document.querySelectorAll('[role="tab"]').length,
                    menus: document.querySelectorAll('[role="menu"]').length
                };
            }
        """)

        logger.info(f"   Navigation elements: {navigation['nav_elements']}")
        logger.info(f"   Tabs: {navigation['tabs']}")

        return navigation

    async def _detect_layout(self, page: Page) -> Dict[str, Any]:
        """Detect page layout structure"""

        layout = await page.evaluate("""
            () => {
                return {
                    containers: document.querySelectorAll('[class*="container"]').length,
                    rows: document.querySelectorAll('[class*="row"]').length,
                    columns: document.querySelectorAll('[class*="col"]').length,
                    grids: document.querySelectorAll('[class*="grid"]').length,
                    flexbox: document.querySelectorAll('[style*="display: flex"], [class*="flex"]').length
                };
            }
        """)

        logger.info(f"   Containers: {layout['containers']}")
        logger.info(f"   Grid elements: {layout['grids']}")

        return layout

    def _save_results(self, results: Dict[str, Any]):
        """Save detection results to file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"template_page_detection_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")


# Global instance
template_page_detector = TemplatePageDetector()

