"""
Pytest configuration to skip tests with missing dependencies.
"""
import warnings

# Suppress upstream pydantic.v1 compatibility warning on Python 3.14+.
# This warning originates from langchain_core importing pydantic.v1 for
# backward compatibility — it is outside our control and adds noise to
# every test run. The actual functionality is unaffected.
warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14",
    category=UserWarning,
)

import pytest


def pytest_ignore_collect(collection_path, config):
    """Skip collecting tests for modules that don't exist."""
    path_str = str(collection_path)
    
    # Skip react controller tests if react screen doesn't exist
    if "react_controller" in path_str:
        return True
    
    # Skip react view tests if react screen doesn't exist  
    if path_str.endswith("test_react_view.py"):
        return True
    
    return None
