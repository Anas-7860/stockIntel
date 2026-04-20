"""
Vercel entrypoint — re-exports the FastAPI `app` instance from main.py.
Vercel recognizes app.py as a valid entrypoint (main.py is not supported).
"""

from main import app  # noqa: F401
