from __future__ import annotations

import importlib


MODULES = ("optuna", "shap")


for module_name in MODULES:
    module = importlib.import_module(module_name)
    print(f"{module_name}={getattr(module, '__version__', 'unknown')}")

print("optional-research-tools: ok")
