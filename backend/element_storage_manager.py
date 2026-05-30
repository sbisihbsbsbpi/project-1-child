"""
Element Storage & Adaptive Detection Manager
Stores detected elements, tracks changes, and adapts to UI modifications
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)


class ElementStorageManager:
    """
    Manages element detection storage with:
    1. Multiple storage strategies (JSON, cache, in-memory)
    2. Change detection
    3. Adaptive element location
    4. Fallback strategies when elements move
    """
    
    def __init__(self, storage_dir: str = "element_storage"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # In-memory cache for fast access
        self.cache = {}
        
        # Storage paths
        self.elements_file = os.path.join(storage_dir, "elements.json")
        self.history_file = os.path.join(storage_dir, "element_history.json")
        self.strategies_file = os.path.join(storage_dir, "location_strategies.json")
        
        logger.info(f"📂 Element Storage Manager initialized at: {storage_dir}")
    
    
    # ============================================================================
    # 1. STORAGE: Save detected elements with multiple identifiers
    # ============================================================================
    
    def save_elements(self, page_url: str, elements: Dict[str, Any]) -> str:
        """
        Save detected elements with multiple identification strategies
        
        Returns: Version ID
        """
        version_id = self._generate_version_id(page_url)
        
        # Enrich elements with multiple identifiers
        enriched_elements = self._enrich_with_identifiers(elements)
        
        # Create storage entry
        storage_entry = {
            "version_id": version_id,
            "timestamp": datetime.now().isoformat(),
            "page_url": page_url,
            "elements": enriched_elements,
            "element_count": self._count_elements(enriched_elements),
            "page_signature": self._generate_page_signature(enriched_elements)
        }
        
        # Save to file
        self._save_to_file(self.elements_file, storage_entry)
        
        # Save to history
        self._append_to_history(storage_entry)
        
        # Update cache
        self.cache[page_url] = storage_entry
        
        logger.info(f"💾 Saved {storage_entry['element_count']} elements for {page_url}")
        logger.info(f"   Version ID: {version_id}")
        
        return version_id
    
    
    def _enrich_with_identifiers(self, elements: Dict) -> Dict:
        """
        Add multiple ways to identify each element:
        1. CSS Selector (primary)
        2. XPath (backup)
        3. Text content (fuzzy matching)
        4. Relative position (parent/sibling context)
        5. Attributes (class, id, data-*)
        """
        enriched = {}
        
        for category, items in elements.items():
            if isinstance(items, list):
                enriched[category] = []
                for item in items:
                    enriched_item = item.copy() if isinstance(item, dict) else {"value": item}
                    
                    # Add identification strategies
                    enriched_item["_identifiers"] = {
                        "primary": self._build_css_selector(enriched_item),
                        "xpath": self._build_xpath(enriched_item),
                        "text_signature": self._get_text_signature(enriched_item),
                        "position_hint": self._get_position_hint(enriched_item),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    enriched[category].append(enriched_item)
            else:
                enriched[category] = items
        
        return enriched
    
    
    # ============================================================================
    # 2. ACCESS: Multiple ways to retrieve elements
    # ============================================================================
    
    def get_element(self, page_url: str, element_id: str, 
                   strategy: str = "auto") -> Optional[Dict]:
        """
        Get element by ID using specified strategy:
        - auto: Try all strategies
        - selector: CSS selector
        - xpath: XPath
        - text: Text content matching
        - fuzzy: Fuzzy matching
        """
        # Try cache first
        if page_url in self.cache:
            return self._find_in_data(self.cache[page_url], element_id, strategy)
        
        # Load from file
        data = self._load_from_file(self.elements_file)
        if data and data.get("page_url") == page_url:
            self.cache[page_url] = data
            return self._find_in_data(data, element_id, strategy)
        
        return None
    
    
    def get_all_elements(self, page_url: str) -> Optional[Dict]:
        """Get all elements for a page"""
        if page_url in self.cache:
            return self.cache[page_url]
        
        data = self._load_from_file(self.elements_file)
        if data and data.get("page_url") == page_url:
            self.cache[page_url] = data
            return data
        
        return None
    
    
    def search_elements(self, page_url: str, query: str) -> List[Dict]:
        """
        Search elements by text, class, or any property
        Fuzzy matching supported
        """
        data = self.get_all_elements(page_url)
        if not data:
            return []
        
        results = []
        query_lower = query.lower()
        
        for category, items in data.get("elements", {}).items():
            if isinstance(items, list):
                for item in items:
                    if self._matches_query(item, query_lower):
                        results.append({
                            "category": category,
                            "element": item
                        })
        
        return results
    
    
    # ============================================================================
    # 3. CHANGE DETECTION: Detect when elements have moved or changed
    # ============================================================================
    
    def detect_changes(self, page_url: str, new_elements: Dict) -> Dict[str, Any]:
        """
        Compare new elements with stored ones
        Returns: Change report
        """
        old_data = self.get_all_elements(page_url)
        
        if not old_data:
            return {
                "status": "new_page",
                "message": "No previous data found",
                "changes": []
            }
        
        old_elements = old_data.get("elements", {})
        old_signature = old_data.get("page_signature")
        new_signature = self._generate_page_signature(new_elements)
        
        changes = {
            "status": "changed" if old_signature != new_signature else "unchanged",
            "old_version": old_data.get("version_id"),
            "new_signature": new_signature,
            "timestamp": datetime.now().isoformat(),
            "changes": []
        }
        
        # Detailed change analysis
        for category in set(list(old_elements.keys()) + list(new_elements.keys())):
            old_items = old_elements.get(category, [])
            new_items = new_elements.get(category, [])
            
            if len(old_items) != len(new_items):
                changes["changes"].append({
                    "category": category,
                    "type": "count_changed",
                    "old_count": len(old_items) if isinstance(old_items, list) else 1,
                    "new_count": len(new_items) if isinstance(new_items, list) else 1
                })
        
        logger.info(f"🔍 Change detection: {changes['status']}")
        logger.info(f"   Found {len(changes['changes'])} differences")

        return changes


    # ============================================================================
    # 4. ADAPTIVE STRATEGIES: Find elements even if they moved
    # ============================================================================

    async def find_element_adaptive(self, page, element_data: Dict) -> Optional[Any]:
        """
        Find element using multiple fallback strategies:
        1. Try primary CSS selector
        2. Try XPath
        3. Try text content matching
        4. Try fuzzy position matching
        5. Try attribute matching

        Returns: Playwright element handle or None
        """
        identifiers = element_data.get("_identifiers", {})

        strategies = [
            ("CSS Selector", lambda: self._try_css_selector(page, identifiers.get("primary"))),
            ("XPath", lambda: self._try_xpath(page, identifiers.get("xpath"))),
            ("Text Match", lambda: self._try_text_match(page, identifiers.get("text_signature"))),
            ("Class Match", lambda: self._try_class_match(page, element_data.get("className"))),
            ("Aria Label", lambda: self._try_aria_label(page, element_data.get("ariaLabel"))),
        ]

        # Try each strategy
        for strategy_name, strategy_func in strategies:
            try:
                element = await strategy_func()
                if element:
                    logger.info(f"✅ Found element using: {strategy_name}")

                    # Update location strategy for future use
                    self._save_successful_strategy(element_data, strategy_name)

                    return element
            except Exception as e:
                logger.debug(f"   Strategy '{strategy_name}' failed: {e}")
                continue

        logger.warning(f"⚠️  Could not find element with any strategy")
        return None


    async def _try_css_selector(self, page, selector: str):
        """Try CSS selector"""
        if not selector:
            return None
        return await page.query_selector(selector)


    async def _try_xpath(self, page, xpath: str):
        """Try XPath"""
        if not xpath:
            return None
        elements = await page.query_selector_all(f"xpath={xpath}")
        return elements[0] if elements else None


    async def _try_text_match(self, page, text_signature: str):
        """Try matching by text content"""
        if not text_signature:
            return None

        # Use Playwright's text selector
        return await page.query_selector(f"text={text_signature}")


    async def _try_class_match(self, page, class_name: str):
        """Try matching by class name"""
        if not class_name:
            return None

        # Extract first class
        first_class = class_name.split()[0] if class_name else None
        if first_class:
            return await page.query_selector(f".{first_class}")
        return None


    async def _try_aria_label(self, page, aria_label: str):
        """Try matching by aria-label"""
        if not aria_label:
            return None

        return await page.query_selector(f"[aria-label='{aria_label}']")


    def _save_successful_strategy(self, element_data: Dict, strategy_name: str):
        """Save which strategy worked for future optimization"""
        strategies = self._load_from_file(self.strategies_file) or {}

        element_id = element_data.get("text", str(hash(str(element_data))))
        strategies[element_id] = {
            "preferred_strategy": strategy_name,
            "last_success": datetime.now().isoformat(),
            "success_count": strategies.get(element_id, {}).get("success_count", 0) + 1
        }

        self._save_to_file(self.strategies_file, strategies)


    # ============================================================================
    # 5. HELPER METHODS
    # ============================================================================

    def _generate_version_id(self, page_url: str) -> str:
        """Generate unique version ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_hash = hashlib.md5(page_url.encode()).hexdigest()[:8]
        return f"{timestamp}_{url_hash}"


    def _generate_page_signature(self, elements: Dict) -> str:
        """Generate signature for change detection"""
        # Create a hash based on element counts and types
        signature_data = {
            "element_counts": self._count_elements(elements),
            "categories": sorted(elements.keys())
        }
        return hashlib.md5(json.dumps(signature_data, sort_keys=True).encode()).hexdigest()


    def _count_elements(self, elements: Dict) -> Dict[str, int]:
        """Count elements by category"""
        counts = {}
        for category, items in elements.items():
            counts[category] = len(items) if isinstance(items, list) else 1
        return counts


    def _build_css_selector(self, element: Dict) -> str:
        """Build CSS selector for element"""
        if "className" in element and element["className"]:
            first_class = element["className"].split()[0]
            return f".{first_class}"
        return ""


    def _build_xpath(self, element: Dict) -> str:
        """Build XPath for element"""
        # Simplified XPath builder
        if "text" in element:
            return f"//*[contains(text(), '{element['text'][:20]}')]"
        return ""


    def _get_text_signature(self, element: Dict) -> str:
        """Get text signature for fuzzy matching"""
        return element.get("text", "")[:50]


    def _get_position_hint(self, element: Dict) -> str:
        """Get position hint (simplified)"""
        return f"index_{element.get('index', 0)}"


    def _find_in_data(self, data: Dict, element_id: str, strategy: str) -> Optional[Dict]:
        """Find element in stored data"""
        for category, items in data.get("elements", {}).items():
            if isinstance(items, list):
                for item in items:
                    if str(item.get("index")) == element_id or item.get("text") == element_id:
                        return item
        return None


    def _matches_query(self, item: Dict, query: str) -> bool:
        """Check if item matches search query"""
        searchable = json.dumps(item).lower()
        return query in searchable


    def _save_to_file(self, filepath: str, data: Dict):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving to {filepath}: {e}")


    def _load_from_file(self, filepath: str) -> Optional[Dict]:
        """Load data from JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading from {filepath}: {e}")
        return None


    def _append_to_history(self, entry: Dict):
        """Append entry to history log"""
        history = self._load_from_file(self.history_file) or {"entries": []}
        history["entries"].append({
            "version_id": entry["version_id"],
            "timestamp": entry["timestamp"],
            "element_count": entry["element_count"],
            "page_signature": entry["page_signature"]
        })

        # Keep only last 50 entries
        history["entries"] = history["entries"][-50:]

        self._save_to_file(self.history_file, history)


    # ============================================================================
    # 6. USAGE EXAMPLES & STATISTICS
    # ============================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        history = self._load_from_file(self.history_file) or {"entries": []}
        strategies = self._load_from_file(self.strategies_file) or {}

        return {
            "total_versions": len(history.get("entries", [])),
            "cached_pages": len(self.cache),
            "successful_strategies": len(strategies),
            "storage_location": self.storage_dir,
            "files": {
                "elements": os.path.exists(self.elements_file),
                "history": os.path.exists(self.history_file),
                "strategies": os.path.exists(self.strategies_file)
            }
        }


# Global instance
element_storage_manager = ElementStorageManager()

