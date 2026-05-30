#!/usr/bin/env python3
"""
Smart Template Filter Builder
Dynamically builds search API payloads based on:
- Department (SERVICE, SALES, PARTS, etc.)
- Communication Type (EMAIL, SMS, TEXT, CHAT)
- Category
- Status

Can intercept existing payload and modify it, or build from scratch
"""

import json
from typing import List, Dict, Optional


class SmartTemplateFilterBuilder:
    """
    Builds Tekion template search API payloads dynamically
    """
    
    def __init__(self):
        # Common departments
        self.departments = ["SERVICE", "SALES", "PARTS", "ACCOUNTING", "GENERAL"]
        
        # Common communication types
        self.comm_types = ["EMAIL", "TEXT", "SMS", "CHAT", "PUSH", "VOICE"]
        
        # Common statuses
        self.statuses = ["ACTIVE", "INACTIVE", "DRAFT"]
    
    def build_simple_payload(
        self,
        departments: List[str] = None,
        comm_types: List[str] = None,
        status: List[str] = None,
        max_results: int = 200
    ) -> Dict:
        """
        Build a simple flat payload (easier to understand)
        
        Example:
            builder.build_simple_payload(
                departments=["SERVICE"],
                comm_types=["EMAIL"],
                status=["ACTIVE"]
            )
        """
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
        
        # Add status filter
        if status:
            payload["filters"].append({
                "field": "status",
                "operator": "IN",
                "values": status,
                "key": "status"
            })
        else:
            payload["filters"].append({
                "field": "status",
                "operator": "IN",
                "values": ["ACTIVE"],
                "key": "status"
            })
        
        # Add communication type filter
        if comm_types:
            payload["filters"].append({
                "field": "purposeSubType",
                "operator": "IN",
                "values": comm_types,
                "key": "purposeSubType"
            })
        
        # Add department filter
        if departments:
            payload["filters"].append({
                "field": "departments",
                "operator": "IN",
                "values": departments,
                "key": "departments"
            })
        
        # Add visibleOnUI filter
        payload["filters"].append({
            "field": "visibleOnUI",
            "operator": "IN",
            "values": [True],
            "key": "visibleOnUI"
        })
        
        return payload
    
    def build_grouped_payload(
        self,
        departments: List[str] = None,
        comm_types: List[str] = None,
        status: List[str] = None,
        max_results: int = 200
    ) -> Dict:
        """
        Build a grouped payload (matches Tekion's format with groupBy)
        This is what Tekion uses when showing templates grouped by type
        
        Example:
            builder.build_grouped_payload(
                departments=["SERVICE"],
                comm_types=["EMAIL", "TEXT"],
                status=["ACTIVE"]
            )
        """
        # Default values
        if not status:
            status = ["ACTIVE"]
        if not departments:
            departments = ["SERVICE"]
        if not comm_types:
            comm_types = ["EMAIL", "TEXT", "CHAT"]
        
        # Build groupBy filters for each communication type
        group_filters = []
        
        for comm_type in comm_types:
            group_filter = {
                "key": comm_type,
                "field": "purposeSubType",
                "operator": "BOOL",
                "andFilters": [
                    {
                        "field": "status",
                        "operator": "IN",
                        "values": status,
                        "key": "status"
                    },
                    {
                        "field": "purposeSubType",
                        "operator": "IN",
                        "values": [comm_type],
                        "key": "purposeSubType"
                    },
                    {
                        "field": "departments",
                        "operator": "IN",
                        "values": departments,
                        "key": "departments"
                    },
                    {
                        "field": "visibleOnUI",
                        "operator": "IN",
                        "values": [True],
                        "key": "visibleOnUI"
                    }
                ]
            }
            group_filters.append(group_filter)
        
        # Build the full payload
        payload = {
            "sort": [],
            "filters": [],
            "searchText": "",
            "groupBy": [
                {
                    "key": "template",
                    "groupType": "FILTERS",
                    "filters": group_filters
                }
            ],
            "includeFields": [],
            "searchableFields": [],
            "excludeFields": [],
            "pageInfo": {"start": 0, "rows": max_results}
        }
        
        return payload
    
    def modify_existing_payload(
        self,
        existing_payload: Dict,
        new_departments: List[str] = None,
        new_comm_types: List[str] = None,
        new_status: List[str] = None,
        new_max_results: int = None
    ) -> Dict:
        """
        Modify an intercepted payload to change filters
        
        Example:
            # Change from SALES to SERVICE
            modified = builder.modify_existing_payload(
                existing_payload,
                new_departments=["SERVICE"]
            )
        """
        payload = json.loads(json.dumps(existing_payload))  # Deep copy
        
        # Check if it's a grouped payload
        if "groupBy" in payload and payload["groupBy"]:
            # Modify grouped payload
            for group in payload["groupBy"]:
                if "filters" in group:
                    for filter_group in group["filters"]:
                        if "andFilters" in filter_group:
                            for and_filter in filter_group["andFilters"]:
                                # Update departments
                                if new_departments and and_filter.get("field") == "departments":
                                    and_filter["values"] = new_departments
                                
                                # Update status
                                if new_status and and_filter.get("field") == "status":
                                    and_filter["values"] = new_status
                                
                                # Update communication type
                                if new_comm_types and and_filter.get("field") == "purposeSubType":
                                    # This is trickier - would need to rebuild the groups
                                    pass
        else:
            # Modify simple payload
            for filter_item in payload.get("filters", []):
                if new_departments and filter_item.get("field") == "departments":
                    filter_item["values"] = new_departments
                
                if new_status and filter_item.get("field") == "status":
                    filter_item["values"] = new_status
                
                if new_comm_types and filter_item.get("field") == "purposeSubType":
                    filter_item["values"] = new_comm_types
        
        # Update max results
        if new_max_results and "pageInfo" in payload:
            payload["pageInfo"]["rows"] = new_max_results
        
        return payload
    
    def extract_filters_from_payload(self, payload: Dict) -> Dict:
        """
        Extract department, comm type, status from a payload
        """
        result = {
            "departments": [],
            "comm_types": [],
            "status": [],
            "max_results": 0
        }
        
        # Check grouped format
        if "groupBy" in payload and payload["groupBy"]:
            for group in payload["groupBy"]:
                if "filters" in group:
                    for filter_group in group["filters"]:
                        if "andFilters" in filter_group:
                            for and_filter in filter_group["andFilters"]:
                                field = and_filter.get("field")
                                values = and_filter.get("values", [])
                                
                                if field == "departments":
                                    result["departments"].extend([v for v in values if v not in result["departments"]])
                                elif field == "purposeSubType":
                                    result["comm_types"].extend([v for v in values if v not in result["comm_types"]])
                                elif field == "status":
                                    result["status"].extend([v for v in values if v not in result["status"]])
        
        # Check simple format
        for filter_item in payload.get("filters", []):
            field = filter_item.get("field")
            values = filter_item.get("values", [])
            
            if field == "departments":
                result["departments"].extend([v for v in values if v not in result["departments"]])
            elif field == "purposeSubType":
                result["comm_types"].extend([v for v in values if v not in result["comm_types"]])
            elif field == "status":
                result["status"].extend([v for v in values if v not in result["status"]])
        
        # Get max results
        if "pageInfo" in payload and "rows" in payload["pageInfo"]:
            result["max_results"] = payload["pageInfo"]["rows"]
        
        return result


# Example usage
if __name__ == "__main__":
    builder = SmartTemplateFilterBuilder()
    
    print("=" * 80)
    print("EXAMPLE 1: Simple Payload - SERVICE EMAIL Templates")
    print("=" * 80)
    simple = builder.build_simple_payload(
        departments=["SERVICE"],
        comm_types=["EMAIL"],
        status=["ACTIVE"],
        max_results=200
    )
    print(json.dumps(simple, indent=2))
    
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Grouped Payload - SERVICE EMAIL/TEXT Templates")
    print("=" * 80)
    grouped = builder.build_grouped_payload(
        departments=["SERVICE"],
        comm_types=["EMAIL", "TEXT"],
        status=["ACTIVE"],
        max_results=200
    )
    print(json.dumps(grouped, indent=2))
    
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Extract Filters from Payload")
    print("=" * 80)
    filters = builder.extract_filters_from_payload(grouped)
    print(json.dumps(filters, indent=2))
