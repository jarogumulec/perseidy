# config.py
# API keys for perseidy project
#
# WARNING: This file should NOT contain real API keys in production!
# For local development, create a copy as config_local.py (ignored by git)
# and set your API key there.

import os

# Try to load from environment variable first
ORS_API_KEY = os.environ.get('ORS_API_KEY', '')

# Fallback to local config if env var not set
if not ORS_API_KEY:
    try:
        from config_local import ORS_API_KEY
    except ImportError:
        # No API key available - will show warnings when needed
        ORS_API_KEY = ''

if not ORS_API_KEY:
    # Silent fail - scripts will handle missing key gracefully
    pass
