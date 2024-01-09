"""Default config values for creep"""

import os

# The remote URL where to download the packages registry file
# This can be overridden with an environment variable for testing, e.g.
# export CREEP_REMOTE_URL=http://creep-packages.lvh.me/packages.json
CANONICAL_REMOTE_URL = "http://quantalideas.com/mcpackages/packages.json"
REMOTE_URL = os.getenv("CREEP_REMOTE_URL", CANONICAL_REMOTE_URL)

# The default target minecraft version for which to search/install mods
# This is overwritten by the user's options file in ~/.creep/options.json, but
# is here as a fallback
DEFAULT_TARGET = "1.20.1"
