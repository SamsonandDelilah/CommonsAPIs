#!/usr/bin/env python3
"""
Scans YAML files and generates initial UID registry
Usage: python init_uid_registry.py --root-dir ./data --output ./data/meta/version_control/uid_registry.yaml
"""

import yaml
import os
import hashlib
from pathlib import Path
import argparse

def generate_uid(filepath: Path, content: dict, root_dir: Path) -> str:
    """Generate UID from nested path and metadata."""
    nested_path = filepath.relative_to(root_dir).parent.as_posix().replace('/', ':')
    concept = filepath.stem
    version = content.get('metadata', {}).get('version', '0.0.0')
    return f"{nested_path}:{concept}@{version}"

def file_checksum(content: str) -> str:
    """SHA-256 checksum of file content"""
    return hashlib.sha256(content.encode()).hexdigest()

def scan_yaml_files(root_dir: Path) -> dict:
    registry = {}
    for yaml_file in root_dir.rglob('*.yaml'):
        if '.git' in yaml_file.parts or 'meta' in yaml_file.parts:
            continue
        with open(yaml_file, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            content = yaml.safe_load(raw_content) or {}
            # Pass root_dir to generate_uid
            uid = generate_uid(yaml_file, content, root_dir)
            registry[uid] = {
                'file': yaml_file.relative_to(root_dir).as_posix(),
                'checksum': file_checksum(raw_content),
                'dependencies': find_dependencies(content)
            }
    return registry

def find_dependencies(content: dict) -> list:
    """Extract $ref fields from YAML content"""
    refs = []
    def _scan(data):
        if isinstance(data, dict):
            for k, v in data.items():
                if k == '$ref':
                    refs.append(v)
                _scan(v)
        elif isinstance(data, list):
            for item in data:
                _scan(item)
    _scan(content)
    return refs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scan YAML files and generate initial UID registry.")
    parser.add_argument('--root-dir', default='./data', help='Root directory to scan')
    parser.add_argument('--output', required=True, help='Output YAML file for UID registry')
    args = parser.parse_args()
    
    registry = scan_yaml_files(Path(args.root_dir))
    with open(args.output, 'w') as f:
        yaml.dump({'entries': registry}, f, sort_keys=True)