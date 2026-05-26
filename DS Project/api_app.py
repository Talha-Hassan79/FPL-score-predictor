# Wrapper to expose FastAPI app for Vercel
# Import the actual app from its original location (which includes spaces in the directory name)
# This file lives at the repository root where Vercel can import it cleanly.

from "DS Project.DS Project.api.app" import app  # type: ignore
