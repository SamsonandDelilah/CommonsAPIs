#!/usr/bin/env python3

"""
Automatically adds new terms from YAML files to terminology.yaml
while preserving existing structure and comments.
"""

import yaml
from pathlib import Path
#!/usr/bin/env python3

"""
Automatically adds new terms from YAML files to terminology.yaml
with domains inferred from their file paths.
"""

import yaml
from pathlib import Path
import argparse
from typing import Dict, List, Set
import re

# Configuration
TERM_FIELDS = ['**']  # Scan all fields but filter in extraction logic
EXCLUDE_DIRS = {'meta'}  # Directories to ignore

class TerminologyUpdater:
    def __init__(self, terminology_file: Path, root_dir: Path):
        self.terminology_file = terminology_file
        self.root_dir = root_dir
        self.terms: Dict[str, Dict] = {}  # {term: {'domain': List[str]}}
        self.domains: Set[str] = set()
        
        # Load existing terminology
        self._load_terminology()
        self._find_domains()

    def _load_terminology(self):
        """Load existing terminology and normalize all keys."""
        if self.terminology_file.exists():
            with open(self.terminology_file) as f:
                data = yaml.safe_load(f) or {}
                self.terms = data.get('terms', {})
                # Normalize all keys
                normalized_terms = {}
                for term, info in self.terms.items():
                    normalized = term.strip().lower().replace(' ', '_')
                    normalized_terms[normalized] = info
                self.terms = normalized_terms

    def _find_domains(self):
        """Get valid domains from directory structure"""
        self.domains = {d.name.lower() for d in self.root_dir.iterdir() 
                       if d.is_dir() and d.name not in EXCLUDE_DIRS}

    def _get_domain(self, filepath: Path) -> str:
        """Extract domain from file path (data/<domain>/...)"""
        try:
            rel_path = filepath.relative_to(self.root_dir)
            return rel_path.parts[0].lower()
        except ValueError:
            return 'general'

    def _extract_terms(self, content: dict) -> Set[str]:
        """Extract terms and normalize to underscores."""
        terms = set()
        
        def _scan(data, path: str):
            if isinstance(data, dict):
                for k, v in data.items():
                    current_path = f"{path}.{k}" if path else k
                    if re.search(r'\.name$', current_path):
                        if isinstance(v, str):
                            normalized = v.strip().lower().replace(' ', '_')
                            if '/' not in normalized:
                                terms.add(normalized)
                        _scan(v, current_path)
            elif isinstance(data, list):
                for item in data:
                    _scan(item, path)
        
        _scan(content, "")
        return terms

    def update(self, dry_run: bool = False):
        """Main update workflow"""
        new_terms = 0
        
        for yaml_file in self.root_dir.rglob('*.yaml'):
            if EXCLUDE_DIRS & set(yaml_file.parts):
                continue

            with open(yaml_file) as f:
                content = yaml.safe_load(f) or {}
                
            domain = self._get_domain(yaml_file)
            terms = self._extract_terms(content)
            
            for term in terms:
                term = term.strip()
                if not term:
                    continue
                
                # Initialize new term
                if term not in self.terms:
                    self.terms[term] = {'domain': [domain]}
                    new_terms += 1
                # Update existing term
                elif domain not in self.terms[term]['domain']:
                    self.terms[term]['domain'].append(domain)
                    new_terms += 1

        if not dry_run and new_terms > 0:
            self._save_terminology()
            
        return new_terms

    def _save_terminology(self):
        """Save with consistent YAML structure"""
        formatted = {"terms": {term: info for term, info in sorted(self.terms.items())}}
        
        with open(self.terminology_file, 'w') as f:
            yaml.dump(formatted, f, sort_keys=False, default_flow_style=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--terminology', required=True, 
                       help="Path to terminology.yaml")
    parser.add_argument('--root-dir', default='./data', 
                       help="Root directory to scan")
    parser.add_argument('--dry-run', action='store_true',
                       help="Show changes without saving")
    args = parser.parse_args()

    updater = TerminologyUpdater(
        Path(args.terminology),
        Path(args.root_dir)
    )
    
    changes = updater.update(dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"Would add/update {changes} terms")
    else:
        print(f"Successfully updated {changes} terms")

if __name__ == '__main__':
    main()
