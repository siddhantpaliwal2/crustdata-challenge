"""
Browser-AI: Natural Language Browser Automation

This package provides tools to control browser actions using natural language commands.
It uses Playwright for browser automation and OpenAI for translating commands.
"""

# Make InteractAPI available directly from the package
try:
    from browser_ai.interact_api import InteractAPI
except ImportError:
    # Fall back to direct import if package structure isn't recognized
    from .interact_api import InteractAPI

__version__ = "0.1.0"

__all__ = ["InteractAPI"] 