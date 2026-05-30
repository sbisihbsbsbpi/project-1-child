"""
API Extraction and Documentation Service

Auto-generates metadata from API responses, extracts fields, and generates documentation.
"""

import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from jsonpath_ng import parse as jsonpath_parse
from deepdiff import DeepDiff


class APIExtractionService:
    """Service for extracting and documenting API responses"""

    def __init__(self) -> None:
        """Initialize API extraction service and create necessary directories."""
        self.metadata_dir = Path("metadata")
        self.docs_dir = Path("docs")
        self.extractions_dir = Path("extractions")
        self.comparisons_dir = Path("comparisons")

        # Create directories if they don't exist
        for directory in [self.metadata_dir, self.docs_dir, self.extractions_dir, self.comparisons_dir]:
            directory.mkdir(exist_ok=True)

    def get_type(self, value: Any) -> str:
        """Determine type of value"""
        if value is None:
            return "any"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int) or isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "any"

    def generate_display_name(self, field_id: str) -> str:
        """
        Generate human-readable display name from field ID
        
        Examples:
            "dealerName" → "Dealer Name"
            "dealerAddress[].city" → "Dealer Address City"
            "taxRegimeConfig.taxRegimes[].taxPercentage" → "Tax Regime Tax Percentage"
        """
        # Remove array brackets
        clean = field_id.replace('[]', ' ')

        # Split on dots and underscores
        parts = clean.replace('.', ' ').replace('_', ' ').split()

        # Convert camelCase to separate words
        words = []
        for part in parts:
            # Split camelCase: "dealerName" → ["dealer", "Name"]
            split_words = re.sub('([A-Z][a-z]+)', r' \1',
                                 re.sub('([A-Z]+)', r' \1', part)).split()
            words.extend(split_words)

        # Capitalize each word
        display_name = ' '.join(word.capitalize() for word in words if word)

        return display_name

    def auto_generate_metadata(
            self,
            api_response: dict,
            prefix: str = "data",
            max_depth: int = 10
    ) -> dict:
        """
        Auto-generate metadata schema from API response
        
        Recursively traverses JSON and creates field mappings
        
        Args:
            api_response: API response JSON
            prefix: Current path prefix (e.g., "data")
            max_depth: Maximum recursion depth
            
        Returns:
            Metadata schema with api_path, type, display_name for each field
        """
        metadata = {}

        def traverse(obj: Any, path: str, depth: int = 0) -> None:
            """
            Recursively traverse API response to extract field metadata.

            Args:
                obj: Current object/value being traversed (dict, list, or primitive)
                path: Current JSONPath (e.g., "data.users[*].name")
                depth: Current recursion depth (prevents infinite recursion)
            """
            if depth > max_depth:
                return

            if isinstance(obj, dict):
                # Object - recurse into each key
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key

                    # Add field to metadata
                    field_id = new_path.replace(f'{prefix}.', '') if prefix else new_path

                    if isinstance(value, (dict, list)):
                        # Complex type - add and recurse
                        metadata[field_id] = {
                            "api_path": new_path,
                            "type": self.get_type(value),
                            "display_name": self.generate_display_name(field_id)
                        }
                        traverse(value, new_path, depth + 1)
                    else:
                        # Primitive type
                        metadata[field_id] = {
                            "api_path": new_path,
                            "type": self.get_type(value),
                            "display_name": self.generate_display_name(field_id)
                        }

            elif isinstance(obj, list) and len(obj) > 0:
                # Array - check first item to determine structure
                if isinstance(obj[0], dict):
                    # Array of objects - recurse into first item
                    for key in obj[0].keys():
                        array_path = f"{path}[*].{key}"
                        field_id = f"{path.replace(f'{prefix}.', '') if prefix else path}[].{key}"

                        metadata[field_id] = {
                            "api_path": array_path,
                            "type": self.get_type(obj[0][key]),
                            "display_name": self.generate_display_name(field_id)
                        }

                        # Recurse if nested object/array
                        if isinstance(obj[0][key], (dict, list)):
                            traverse(obj[0][key], array_path, depth + 1)

        traverse(api_response, prefix)
        return metadata

    def extract_json_path(self, data: dict, json_path: str) -> Any:
        """
        Extract data from JSON using JSON path expression

        Args:
            data: JSON response data
            json_path: JSON path expression (e.g., "data[*].id")

        Returns:
            Extracted value(s) - could be single value or list
        """
        try:
            # Parse the JSON path expression
            jsonpath_expr = jsonpath_parse(json_path)

            # Find all matches
            matches = jsonpath_expr.find(data)

            # Extract values
            values = [match.value for match in matches]

            # Return single value if only one match, otherwise return list
            if len(values) == 0:
                return None
            elif len(values) == 1:
                return values[0]
            else:
                return values

        except Exception as e:
            print(f"❌ JSON path extraction failed for '{json_path}': {e}")
            return None

    def extract_fields_from_response(
            self,
            response_data: dict,
            field_mappings: dict
    ) -> dict:
        """
        Extract all fields from API response using metadata mappings

        Args:
            response_data: API response JSON
            field_mappings: Field metadata (api_path, type, display_name)

        Returns:
            Dictionary of extracted fields with display names
        """
        extracted = {}

        for field_id, field_meta in field_mappings.items():
            api_path = field_meta.get("api_path")
            display_name = field_meta.get("display_name")
            expected_type = field_meta.get("type")

            # Extract value using JSON path
            value = self.extract_json_path(response_data, api_path)

            # Validate type
            actual_type = self.get_type(value)
            type_match = actual_type == expected_type

            # Store with display name
            extracted[field_id] = {
                "display_name": display_name,
                "value": value,
                "type": actual_type,
                "expected_type": expected_type,
                "type_match": type_match,
                "api_path": api_path
            }

        return extracted

    def generate_markdown_doc(self, result: dict, screenshot_path: str = None) -> str:
        """Generate Markdown documentation"""
        api_url = result.get("api_url", "")
        method = result.get("method", "GET")
        status = result.get("status", 200)
        timestamp = result.get("timestamp", "")
        extracted_fields = result.get("extracted_fields", {})

        md = f"""# API Documentation

**Endpoint:** `{method} {api_url}`
**Status:** {status}
**Timestamp:** {timestamp}
"""

        if screenshot_path:
            md += f"**Screenshot:** [{screenshot_path}]({screenshot_path})\n"

        md += f"""
---

## Extracted Fields ({len(extracted_fields)})

| Field ID | Display Name | API Path | Type | Value Preview |
|----------|--------------|----------|------|---------------|
"""

        for field_id, field_data in extracted_fields.items():
            display_name = field_data.get("display_name", "")
            api_path = field_data.get("api_path", "")
            field_type = field_data.get("type", "")
            value = field_data.get("value")

            # Truncate value for preview
            value_preview = str(value)[:50]
            if len(str(value)) > 50:
                value_preview += "..."

            # Escape pipe characters in value
            value_preview = value_preview.replace("|", "\\|")

            md += f"| `{field_id}` | {display_name} | `{api_path}` | {field_type} | {value_preview} |\n"

        return md

    def save_metadata(self, metadata: dict, filename: str) -> str:
        """Save metadata to file"""
        filepath = self.metadata_dir / f"{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
        return str(filepath)

    def save_extraction(self, extraction: dict, filename: str) -> str:
        """Save extraction result to file"""
        filepath = self.extractions_dir / f"{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(extraction, f, indent=2)
        return str(filepath)

    def save_documentation(self, doc: str, filename: str, format: str = "md") -> str:
        """Save documentation to file"""
        filepath = self.docs_dir / f"{filename}.{format}"
        with open(filepath, 'w') as f:
            f.write(doc)
        return str(filepath)

    def compare_environments(self, extractions: dict) -> dict:
        """
        Compare API responses across multiple environments

        Args:
            extractions: {
                "dev": extraction_result,
                "staging": extraction_result,
                "prod": extraction_result
            }

        Returns:
            Comparison report with differences
        """
        comparison = {
            "environments": list(extractions.keys()),
            "field_comparison": {},
            "differences": [],
            "summary": {
                "total_fields": 0,
                "fields_with_differences": 0,
                "identical_fields": 0
            }
        }

        # Get all field IDs from all environments
        all_field_ids = set()
        for env, result in extractions.items():
            all_field_ids.update(result.get("extracted_fields", {}).keys())

        comparison["summary"]["total_fields"] = len(all_field_ids)

        # Compare each field across environments
        for field_id in all_field_ids:
            field_values = {}

            for env, result in extractions.items():
                extracted_fields = result.get("extracted_fields", {})
                if field_id in extracted_fields:
                    field_values[env] = extracted_fields[field_id].get("value")
                else:
                    field_values[env] = None

            # Check if values differ
            unique_values = set(str(v) for v in field_values.values())
            has_difference = len(unique_values) > 1

            if has_difference:
                comparison["differences"].append({
                    "field_id": field_id,
                    "values": field_values
                })
                comparison["summary"]["fields_with_differences"] += 1
            else:
                comparison["summary"]["identical_fields"] += 1

            comparison["field_comparison"][field_id] = {
                "values": field_values,
                "has_difference": has_difference
            }

        return comparison

    def validate_response(self, response_data: dict, metadata: dict) -> dict:
        """
        Validate API response against metadata schema

        Args:
            response_data: API response JSON
            metadata: Expected metadata schema

        Returns:
            Validation report
        """
        validation = {
            "total_fields": len(metadata),
            "fields_found": 0,
            "fields_missing": 0,
            "type_mismatches": 0,
            "missing_fields": [],
            "type_mismatch_details": [],
            "validation_passed": True
        }

        for field_id, field_meta in metadata.items():
            api_path = field_meta.get("api_path")
            expected_type = field_meta.get("type")

            # Try to extract value
            value = self.extract_json_path(response_data, api_path)

            if value is None:
                validation["fields_missing"] += 1
                validation["missing_fields"].append({
                    "field_id": field_id,
                    "api_path": api_path,
                    "expected_type": expected_type
                })
                validation["validation_passed"] = False
            else:
                validation["fields_found"] += 1

                # Check type
                actual_type = self.get_type(value)
                if actual_type != expected_type and expected_type != "any":
                    validation["type_mismatches"] += 1
                    validation["type_mismatch_details"].append({
                        "field_id": field_id,
                        "api_path": api_path,
                        "expected_type": expected_type,
                        "actual_type": actual_type,
                        "value_preview": str(value)[:100]
                    })
                    validation["validation_passed"] = False

        return validation
