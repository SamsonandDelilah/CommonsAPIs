#!/usr/bin/env python3

"""
Validates that all terms used in YAML files are registered in terminology.yaml
with appropriate domain assignments.
"""

import yaml
import argparse
from pathlib import Path
import sys
import re
from typing import Dict, List, Set

# --- Constants ---
TERM_FIELDS = ['name', 'variables.*.name']  # Only validate explicit term fields
DEFAULT_DOMAIN = 'general'  # Fallback domain if none found

class TerminologyValidator:
    def __init__(self, terminology_file: Path, root_dir: Path):
        self.root_dir = root_dir
        self.terms: Dict[str, Set[str]] = {}
        self.domains: Set[str] = set()
        
        # Load and validate terminology
        with open(terminology_file) as f:
            data = yaml.safe_load(f)
            self._load_terminology(data)
            self._validate_terminology()

    def _load_terminology(self, data: dict):
        """Load terminology data and domain directories"""
        self.terms = {term: set(info['domain']) for term, info in data['terms'].items()}
        
        # Get valid domains from directory structure
        self.domains = {d.name for d in self.root_dir.iterdir() if d.is_dir()}
        self.domains.add(DEFAULT_DOMAIN)

    def _validate_terminology(self):
        """Check terminology internal consistency"""
        # Check for duplicate terms
        duplicates = [term for term, domains in self.terms.items() if len(domains) < 1]
        if duplicates:
            raise ValueError(f"Terms without domains: {', '.join(duplicates)}")
            
        # Check all domains exist as directories
        invalid_domains = set()
        for domains in self.terms.values():
            invalid_domains.update(d for d in domains if d not in self.domains)
        
        if invalid_domains:
            raise ValueError(f"Invalid domains in terminology: {', '.join(invalid_domains)}")

    def _get_file_domain(self, filepath: Path) -> str:
        """Extract domain from file path (data/<domain>/...)"""
        try:
            return filepath.relative_to(self.root_dir).parts[0]
        except ValueError:
            return DEFAULT_DOMAIN

    def _extract_terms(self, content: dict) -> Set[str]:
        """Extract terms only from specified fields, ignoring paths/URLs."""
        terms = set()
        
        def _scan(data, path: str):
            if isinstance(data, dict):
                for k, v in data.items():
                    current_path = f"{path}.{k}" if path else k
                    # Check if current path matches any term field pattern
                    if any(p in current_path for p in TERM_FIELDS):
                        if isinstance(v, str):
                            # Skip paths/URLs (customize this regex as needed)
                            if not re.search(r'\.yaml$|/', v):
                                terms.add(v.strip().lower())
                    _scan(v, current_path)
            elif isinstance(data, list):
                for item in data:
                    _scan(item, path)
        
        _scan(content, "")
        return terms


    def validate_file(self, filepath: Path) -> List[str]:
        """Validate terms in a single YAML file"""
        errors = []
        
        with open(filepath) as f:
            content = yaml.safe_load(f) or {}
        
        domain = self._get_file_domain(filepath)
        terms = self._extract_terms(content)
        
        for term in terms:
            # Check term existence
            if term not in self.terms:
                errors.append(f"Term '{term}' not registered")
                continue
            
            # Check domain permission
            if domain not in self.terms[term]:
                allowed = ", ".join(self.terms[term])
                errors.append(f"Term '{term}' not allowed in domain '{domain}' (allowed: {allowed})")
        
        return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--terminology', required=True, help="Path to terminology.yaml")
    parser.add_argument('--root-dir', default='./data', help="Root directory to scan")
    parser.add_argument('--file', required=True, help="File to validate")
    args = parser.parse_args()

    try:
        validator = TerminologyValidator(
            Path(args.terminology), 
            Path(args.root_dir)
        )
    except Exception as e:
        print(f"Terminology validation failed: {str(e)}")
        sys.exit(2)

    errors = validator.validate_file(Path(args.file))
    
    if errors:
        print(f"\nTerminology errors in {args.file}:")
        print("\n".join(f"  - {e}" for e in errors))
        sys.exit(1)
    
    print("All terms valid and domain-compliant")

if __name__ == '__main__':
    main()
