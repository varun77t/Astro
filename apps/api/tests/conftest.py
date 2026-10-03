"""Test-wide settings, applied before the app is imported.

Tests never call real LLM providers, even when a local .env has keys, and never touch the
on-disk readings cache.
"""

import os

os.environ["VEDIC_ASTRO_IGNORE_DOTENV"] = "1"
os.environ["LLM_PROVIDERS"] = "none"
os.environ["READINGS_CACHE_PATH"] = ":memory:"
