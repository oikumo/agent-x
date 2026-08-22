# Registers the hermetic `env` fixture for the re-exported golden classes
# (fixtures don't travel through plain imports — conftest plugin namespace does).
from tests.scripts.omt.test_project_lifecycle import env  # noqa: F401
