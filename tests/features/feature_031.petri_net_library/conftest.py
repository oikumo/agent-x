# Registers the `net` fixture for the re-exported model test classes
# (fixtures don't travel through plain imports — conftest plugin namespace does).
from tests.model.petri_net.test_model import net  # noqa: F401
