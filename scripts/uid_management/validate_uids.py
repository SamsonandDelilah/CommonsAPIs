#!/usr/bin/env python3
"""
Validates UID references across YAML files
Usage: python validate_uids.py --registry ./data/_meta/uid_registry.yaml --file physics/kinematics/free_fall.yaml
"""

import yaml
import sys
from pathlib import Path

class UIDValidator:
    def __init__(self, registry_file: Path):
        with open(registry_file) as f:
            self.registry = yaml.safe_load(f)['entries']
            
    def validate_file(self, filepath: Path):
        with open(filepath) as f:
            content = yaml.safe_load(f) or {}
            
        errors = []
        # Check if file has valid UID
        file_uid = self._get_file_uid(filepath)
        if file_uid not in self.registry:
            errors.append(f"Missing registry entry for {file_uid}")
            
        # Check all $refs
        for ref in self._find_references(content):
            if ref not in self.registry:
                errors.append(f"Invalid reference: {ref}")
                
        return errors
    
    def _get_file_uid(self, filepath: Path) -> str:
        # Implementation matching init_uid_registry.py
        pass
        
    def _find_references(self, content: dict) -> list:
        # Recursively find all $ref fields
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--registry', required=True)
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    
    validator = UIDValidator(Path(args.registry))
    errors = validator.validate_file(Path(args.file))
    
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print("All UID references valid")