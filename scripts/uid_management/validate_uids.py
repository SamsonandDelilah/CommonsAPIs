#!/usr/bin/env python3

"""
Validates UID references across YAML files

Usage:
    python validate_uids.py --registry ./data/meta/version_control/uid_registry.yaml --file physics/mechanics/classical/kinematics/formulas/free_fall.yaml
"""

import yaml
import sys
import argparse
from pathlib import Path

# --- UIDValidator class ---
class UIDValidator:
    def __init__(self, registry_file: Path):
        with open(registry_file) as f:
            self.registry = yaml.safe_load(f)['entries']

    def validate_file(self, filepath: Path):
        with open(filepath) as f:
            content = yaml.safe_load(f) or {}
        errors = []

        # Validate file's own UID
        file_uid = self._get_file_uid(filepath)
        if file_uid not in self.registry:
            errors.append(f"Missing registry entry for {file_uid}")

        # Validate $refs (split UID and fragment)
        for ref in self._find_references(content):
            if '#' in ref:
                base_uid, fragment = ref.split('#', 1)
            else:
                base_uid, fragment = ref, None

            # Check if base UID exists
            if base_uid not in self.registry:
                errors.append(f"Invalid reference: {ref}")
                continue

            # Check if fragment exists in the referenced file
            if fragment:
                ref_file = self.registry[base_uid]['file']
                ref_path = Path("data") / ref_file
                if not self._fragment_exists(ref_path, fragment):
                    errors.append(f"Fragment '{fragment}' not found in {base_uid}")
        return errors

    def _fragment_exists(self, ref_path: Path, fragment: str) -> bool:
        """Check if a nested fragment exists (e.g., 'constants.g')."""
        with open(ref_path) as f:
            content = yaml.safe_load(f) or {}
        keys = fragment.split('.')
        data = content
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return False
        return True

    def _get_file_uid(self, filepath: Path) -> str:
        """Generate UID matching init_uid_registry.py logic."""
        nested_path = filepath.relative_to(Path("data")).parent.as_posix().replace("/", ":")
        concept = filepath.stem
        with open(filepath) as f:
            content = yaml.safe_load(f) or {}
        version = content.get("metadata", {}).get("version", "0.0.0")
        return f"{nested_path}:{concept}@{version}"

    def _find_references(self, content: dict) -> list:
        """Recursively find all $ref fields in nested YAML content."""
        refs = []
        def _scan(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == '$ref':
                        refs.append(value)
                    _scan(value)
            elif isinstance(data, list):
                for item in data:
                    _scan(item)
        _scan(content)
        return refs

# --- Main script logic ---
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

    print(f"UID references valid in {args.file}")

    # --- Prompt user for full validation ---
    while True:
        user_input = input("Do you want to validate all YAML files in /data? (y/n): ").strip().lower()
        if user_input in ("y", "yes"):
            print("\nValidating all YAML files in /data ...\n")
            all_ok = True
            for yaml_file in Path("data").rglob("*.yaml"):
                errs = validator.validate_file(yaml_file)
                if errs:
                    print(f"\nErrors in {yaml_file}:")
                    print("\n".join(errs))
                    all_ok = False
            if all_ok:
                print("\nAll UID references valid in all files.")
                sys.exit(0)
            else:
                sys.exit(1)
        elif user_input in ("n", "no"):
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid input. Please enter y/n.")
