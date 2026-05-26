# vercel_app.py
"""Vercel entry point wrapper.
Loads the FastAPI app located in a directory path that contains spaces.
The actual app is defined in "DS Project/DS Project/api/app.py" as variable `app`.
"""
import importlib.util
import pathlib

# Resolve the path to the actual app module
module_path = pathlib.Path(__file__).parent / "DS Project" / "DS Project" / "api" / "app.py"
spec = importlib.util.spec_from_file_location("api_app", module_path)
api_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to load spec for API module"
spec.loader.exec_module(api_module)

# Re‑export the FastAPI instance so Vercel can discover it
app = api_module.app
