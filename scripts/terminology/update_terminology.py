#!/usr/bin/env python3

"""
Automatically generates/updates terminology.yaml with:
- Structural keys from all YAML files
- Values from 'name' fields
- Semantic versioning
"""

import yaml
from pathlib import Path
import argparse
from typing import Dict, List, Set
import re

# Configuration
EXCLUDE_DIRS = {'meta'}
DEFAULT_METADATA = {
    'version': '1.0.0',
    'description': 'Centralized terminology for CommonsAPIs'
}

class TerminologyManager:
    def __init__(self, terminology_file: Path, root_dir: Path):
        self.terminology_file = terminology_file
        self.root_dir = root_dir
        self.metadata = DEFAULT_METADATA.copy()
        self.terms: Dict[str, Dict] = {}
        self.changes_made = False
        
        self._load_existing()
        self._scan_data_files()

    def _load_existing(self):
        """Load existing terminology with metadata preservation"""
        if self.terminology_file.exists():
            with open(self.terminology_file) as f:
                data = yaml.safe_load(f) or {}
                self.metadata = {**DEFAULT_METADATA, **data.get('metadata', {})}
                self.terms = data.get('terms', {})

    def _get_domain(self, filepath: Path) -> str:
        """Extract domain from file path"""
        try:
            return filepath.relative_to(self.root_dir).parts[0].lower()
        except ValueError:
            return 'general'

    def _normalize_term(self, term: str) -> str:
        """Standardize term formatting"""
        return term.strip().lower().replace(' ', '_').replace('-', '_')

    def _process_structure(self, data: dict, domain: str):
        """Recursively extract keys and name fields from YAML structure"""
        if isinstance(data, dict):
            for key, value in data.items():
                # Add structural keys as terms
                norm_key = self._normalize_term(key)
                self._add_term(norm_key, domain)
                
                # Process nested structures
                self._process_structure(value, domain)
                
                # Add name field values
                if key == 'name' and isinstance(value, str):
                    norm_name = self._normalize_term(value)
                    self._add_term(norm_name, domain)
        elif isinstance(data, list):
            for item in data:
                self._process_structure(item, domain)

    def _add_term(self, term: str, domain: str):
        """Add term with domain validation"""
        if not term or '/' in term:
            return
        
        existing = self.terms.get(term, {'domain': []})
        if domain not in existing['domain']:
            self.terms[term] = {'domain': sorted(existing['domain'] + [domain])}
            self.changes_made = True

    def _scan_data_files(self):
        """Process all YAML files in the data directory"""
        for yaml_file in self.root_dir.rglob('*.yaml'):
            if any(part in EXCLUDE_DIRS for part in yaml_file.parts):
                continue

            with open(yaml_file) as f:
                content = yaml.safe_load(f) or {}
                domain = self._get_domain(yaml_file)
                self._process_structure(content, domain)

    def _increment_version(self):
        """Bump patch version number"""
        try:
            major, minor, patch = self.metadata['version'].split('.')
            self.metadata['version'] = f"{major}.{minor}.{int(patch)+1}"
        except:
            self.metadata['version'] = '1.0.0'

    def save(self):
        """Persist changes to terminology.yaml"""
        if self.changes_made:
            self._increment_version()
            
        output = {
            'metadata': self.metadata,
            'terms': {k: v for k, v in sorted(self.terms.items())}
        }
        
        self.terminology_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.terminology_file, 'w') as f:
            yaml.dump(output, f, sort_keys=False, default_flow_style=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--terminology', required=True, 
                       help="Path to terminology.yaml")
    parser.add_argument('--root-dir', default='data', 
                       help="Root directory to scan")
    args = parser.parse_args()

    manager = TerminologyManager(Path(args.terminology), Path(args.root_dir))
    manager.save()
    print(f"Terminology updated to version {manager.metadata['version']}")

if __name__ == '__main__':
    main()
