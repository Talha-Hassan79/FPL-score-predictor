import importlib.util
import pathlib

# Resolve the path to the actual FastAPI app file (contains spaces in directories)
module_path = pathlib.Path(__file__).parent / "DS Project" / "DS Project" / "api" / "app.py"

spec = importlib.util.spec_from_file_location("api_app", module_path)
api_app = importlib.util.module_from_spec(spec)
assert spec.loader is not None, "Failed to load spec for api/app.py"
spec.loader.exec_module(api_app)

# Expose the FastAPI app instance expected by Vercel
app = api_app.app
