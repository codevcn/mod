"""
Standardized Version & Metadata Management for Mod CLI.
"""

__version__ = "0.1.0"
APP_NAME = "Mod CLI"
APP_ALIAS = "mod"
APP_DESCRIPTION = "A modular automation and developer productivity CLI tool."


def get_version_tag() -> str:
    """Returns version tag (e.g. 'v0.1.0')."""
    return f"v{__version__}"


def get_version_info() -> str:
    """Returns full formatted version string with short English description."""
    return f"{APP_NAME} ({APP_ALIAS}) {get_version_tag()} - {APP_DESCRIPTION}"
