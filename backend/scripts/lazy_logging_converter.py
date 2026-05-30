#!/usr/bin/env python3
"""
Lazy Logging Converter
Converts f-strings in logger calls to % formatting for better performance

Usage:
    python lazy_logging_converter.py <file.py>
    python lazy_logging_converter.py --scan <directory>
    python lazy_logging_converter.py --stats <file.py>
"""

import re
import sys
import ast
from pathlib import Path
from typing import List, Tuple, Dict


class LoggerFStringDetector(ast.NodeVisitor):
    """Detect f-strings in logger calls using AST"""
    
    def __init__(self):
        self.findings: List[Tuple[int, str, str]] = []
        
    def visit_Call(self, node):
        """Visit function calls looking for logger.method(f"...")"""
        try:
            # Check if this is a logger method call
            if (hasattr(node.func, 'value') and 
                hasattr(node.func.value, 'id') and 
                node.func.value.id == 'logger' and
                hasattr(node.func, 'attr') and
                node.func.attr in ['debug', 'info', 'warning', 'error']):
                
                # Check if first argument is an f-string
                if node.args and isinstance(node.args[0], ast.JoinedStr):
                    method = node.func.attr
                    line_no = node.lineno
                    self.findings.append((line_no, method, 'f-string'))
        except Exception:
            pass
        
        self.generic_visit(node)


def scan_file(filepath: Path) -> Dict[str, int]:
    """Scan a file for logger f-strings"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        detector = LoggerFStringDetector()
        detector.visit(tree)
        
        stats = {
            'debug': 0,
            'info': 0,
            'warning': 0,
            'error': 0,
            'total': 0
        }
        
        for line_no, method, _ in detector.findings:
            stats[method] += 1
            stats['total'] += 1
        
        return stats
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")
        return {}


def scan_directory(directory: Path) -> None:
    """Scan all Python files in a directory"""
    total_stats = {
        'debug': 0,
        'info': 0,
        'warning': 0,
        'error': 0,
        'total': 0
    }
    
    python_files = list(directory.rglob('*.py'))
    print(f"Scanning {len(python_files)} Python files in {directory}...\n")
    
    for filepath in python_files:
        stats = scan_file(filepath)
        if stats and stats['total'] > 0:
            print(f"{filepath.relative_to(directory)}: {stats['total']} f-strings")
            print(f"  debug={stats['debug']}, info={stats['info']}, warning={stats['warning']}, error={stats['error']}")
            
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
    
    print(f"\n{'='*60}")
    print(f"Total logger f-strings found: {total_stats['total']}")
    print(f"  debug: {total_stats['debug']}")
    print(f"  info: {total_stats['info']}")
    print(f"  warning: {total_stats['warning']}")
    print(f"  error: {total_stats['error']}")
    print(f"{'='*60}")


def show_stats(filepath: Path) -> None:
    """Show detailed statistics for a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        detector = LoggerFStringDetector()
        detector.visit(tree)
        
        if not detector.findings:
            print(f"✅ No logger f-strings found in {filepath}")
            return
        
        print(f"\n📊 Logger F-String Analysis: {filepath}")
        print(f"{'='*60}")
        print(f"Found {len(detector.findings)} logger calls with f-strings:\n")
        
        for line_no, method, _ in detector.findings:
            # Get the actual line
            lines = content.split('\n')
            if line_no <= len(lines):
                line = lines[line_no - 1].strip()
                print(f"Line {line_no}: logger.{method}()")
                print(f"  {line[:80]}...")
                print()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == '--scan' and len(sys.argv) > 2:
        directory = Path(sys.argv[2])
        scan_directory(directory)
    elif command == '--stats' and len(sys.argv) > 2:
        filepath = Path(sys.argv[2])
        show_stats(filepath)
    else:
        filepath = Path(command)
        if filepath.is_file():
            show_stats(filepath)
        else:
            print(f"File not found: {filepath}")
