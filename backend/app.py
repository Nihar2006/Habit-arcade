"""Compatibility entrypoint for deployment commands such as `uvicorn app:app` inside backend."""

from main import app

__all__ = ["app"]
