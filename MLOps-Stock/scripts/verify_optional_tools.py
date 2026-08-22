from __future__ import annotations

import importlib
import importlib.util


MODULES = ("optuna", "shap", "boto3")


for module_name in MODULES:
    module = importlib.import_module(module_name)
    print(f"{module_name}={getattr(module, '__version__', 'unknown')}")

s3fs_spec = importlib.util.find_spec("s3fs")
if s3fs_spec is None:
    raise RuntimeError("s3fs module is not discoverable")
print("s3fs=installed")
print("optional-tooling: ok")
