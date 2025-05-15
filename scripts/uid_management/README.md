# UID Management Scripts

- `init_uid_registry.py`: Initial scan of YAML files
- `validate_uids.py`: CI/CD and pre-commit validation

Usage:
```bash
python3 init_uid_registry.py --root-dir ../data --output ../data/_meta/uid_registry.yaml