"""Tests for kb_ast_extract.py — AST skeleton extractor (feature_kb_akb P0).

Conventions mirror test_kb_compiler.py: sys.path.insert scripts/omt, lazy
imports (module may not exist in RED), tmp_path fixtures, class-per-behavior.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "omt"))


def _write_tree(tree: dict[str, str], tmp_path: Path) -> tuple[Path, Path]:
    """Write a fake src tree under tmp_path; return (src_root, repo_root)."""
    repo_root = tmp_path
    src_root = tmp_path / "src" / "agentx"
    for rel, content in tree.items():
        f = src_root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    return src_root, repo_root


def _by_id(records: list[dict]) -> dict[str, dict]:
    return {r["id"]: r for r in records}


SPEC_PY = '''\
"""Tool specs + sensor/actuator contracts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolSpec:
    """Unified tool descriptor."""

    tool_id: str
    name: str


class ISensor(ABC):
    """Read-from-environment contract."""

    id: str

    @abstractmethod
    def sense(self):
        """Read."""

    @abstractmethod
    def get_sensor_schema(self):
        """Schema."""


class IActuator(ABC):
    """Act-on-environment contract."""

    @abstractmethod
    def act(self, command):
        """Execute."""
'''

FILESYSTEM_TOOL_PY = '''\
from agentx.agent.model.tools.spec import ISensor, IActuator


class FileSystemTool(ISensor, IActuator):
    """Hybrid sandboxed file CRUD."""

    def sense(self): ...
    def get_sensor_schema(self): ...
    def act(self, command): ...
'''

REGISTRY_PY = '''\
from agentx.agent.interfaces import IToolRegistryPartner


class ToolRegistry(IToolRegistryPartner):
    """Tool catalog."""

    def list_sensors(self): ...
'''

INTERFACES_PY = '''\
from abc import ABC, abstractmethod


class IToolRegistryPartner(ABC):
    """Registry contract seen by controller/TUI."""

    @abstractmethod
    def list_sensors(self): ...
'''

AGENT_PY = '''\
from agentx.agent.model.tools.registry import ToolRegistry
from agentx.agent.model.memory.manager import MemoryManager


class Agent:
    """Facade."""

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.memory: MemoryManager = MemoryManager()
        self.count: int = 0
        self.name = "agent"
'''

MANAGER_PY = '''\
class MemoryManager:
    """Memory."""
'''


class TestExtractContract:
    """Behavior 1: ABC with @abstractmethods -> contract.<Name> record."""

    def test_abc_with_abstractmethods_emits_contract(self, tmp_path):
        import kb_ast_extract

        src_root, repo_root = _write_tree(
            {
                "agent/model/tools/spec.py": SPEC_PY,
                "agent/model/tools/filesystem_tool.py": FILESYSTEM_TOOL_PY,
            },
            tmp_path,
        )
        records, warnings = kb_ast_extract.extract(src_root, repo_root)
        by_id = _by_id(records)

        rec = by_id.get("contract.ISensor")
        assert rec is not None, f"contract.ISensor missing; ids={sorted(by_id)}"
        assert rec["kind"] == "contract"
        assert rec["tier"] == "code"
        assert rec["src"] == "src/agentx/agent/model/tools/spec.py"
        assert isinstance(rec["line"], int) and rec["line"] > 0
        assert "CONTRACT_ISENSOR" in rec["tags"]
        assert "TIER_CODE" in rec["tags"]
        assert "LAYER_MODEL" in rec["tags"]
        # auto-text carries abstractmethod names
        assert "sense" in rec["text"]
        assert "get_sensor_schema" in rec["text"]
        # refs -> realizers (pass-2 back-edge)
        assert "class.FileSystemTool" in rec["refs"]


class TestExtractClass:
    """Behavior 2: concrete class -> class.<Name> record, refs -> project bases."""

    def test_concrete_class_emits_class_record(self, tmp_path):
        import kb_ast_extract

        src_root, repo_root = _write_tree(
            {
                "agent/model/tools/spec.py": SPEC_PY,
                "agent/model/tools/filesystem_tool.py": FILESYSTEM_TOOL_PY,
            },
            tmp_path,
        )
        records, _ = kb_ast_extract.extract(src_root, repo_root)
        by_id = _by_id(records)

        # dataclass ToolSpec is a concrete class (not a contract)
        spec = by_id.get("class.ToolSpec")
        assert spec is not None
        assert spec["kind"] == "class"
        assert "CLASS_TOOLSPEC" in spec["tags"]

        # concrete realizer: refs resolve to project contracts, sorted+unique
        fst = by_id.get("class.FileSystemTool")
        assert fst is not None
        assert fst["kind"] == "class"
        assert "contract.ISensor" in fst["refs"]
        assert "contract.IActuator" in fst["refs"]
        assert fst["refs"] == sorted(set(fst["refs"]))
        # auto-text names the bases
        assert "ISensor" in fst["text"]


class TestExtractDepRealization:
    """Behavior 3: class with project-contract base -> dep.<Class>_<Target>."""

    def test_realization_edge_emitted(self, tmp_path):
        import kb_ast_extract

        src_root, repo_root = _write_tree(
            {
                "agent/interfaces.py": INTERFACES_PY,
                "agent/model/tools/registry.py": REGISTRY_PY,
            },
            tmp_path,
        )
        records, _ = kb_ast_extract.extract(src_root, repo_root)
        by_id = _by_id(records)

        dep = by_id.get("dep.ToolRegistry_IToolRegistryPartner")
        assert dep is not None, f"realization dep missing; ids={sorted(by_id)}"
        assert dep["kind"] == "dep"
        assert dep["src"] == "src/agentx/agent/model/tools/registry.py"
        assert "DEP_TOOLREGISTRY_ITOOLREGISTRYPARTNER" in dep["tags"]
        assert "TIER_CODE" in dep["tags"]
        assert set(dep["refs"]) == {
            "class.ToolRegistry",
            "contract.IToolRegistryPartner",
        }


class TestExtractDepComposition:
    """Behavior 4: self.x = ProjectClass() / self.x: ProjectClass -> dep edge."""

    def test_composition_edges_from_init(self, tmp_path):
        import kb_ast_extract

        src_root, repo_root = _write_tree(
            {
                "agent/model/agent.py": AGENT_PY,
                "agent/model/tools/registry.py": REGISTRY_PY,
                "agent/interfaces.py": INTERFACES_PY,
                "agent/model/memory/manager.py": MANAGER_PY,
            },
            tmp_path,
        )
        records, _ = kb_ast_extract.extract(src_root, repo_root)
        by_id = _by_id(records)

        # Assign form: self.tool_registry = ToolRegistry()
        dep_reg = by_id.get("dep.Agent_ToolRegistry")
        assert dep_reg is not None, f"composition dep missing; ids={sorted(by_id)}"
        assert dep_reg["kind"] == "dep"
        assert set(dep_reg["refs"]) == {"class.Agent", "class.ToolRegistry"}

        # AnnAssign form: self.memory: MemoryManager = MemoryManager()
        dep_mem = by_id.get("dep.Agent_MemoryManager")
        assert dep_mem is not None

        # non-project targets (int, str) produce NO dep edges
        assert "dep.Agent_int" not in by_id
        assert "dep.Agent_str" not in by_id

        # composed target appears in the class record's refs too
        assert "class.ToolRegistry" in by_id["class.Agent"]["refs"]


class TestLayerInference:
    """Behavior 5: path-based LAYER_* inference (PROJECT.md v2.1 table)."""

    def test_layer_table(self, tmp_path):
        import kb_ast_extract

        src_root, repo_root = _write_tree(
            {
                "agent/model/foo.py": "class FooModel:\n    pass\n",
                "model/ai/bar.py": "class BarAi:\n    pass\n",
                "agent/view/panel.py": "class Panel:\n    pass\n",
                "ui/screens/x_screen.py": "class XScreen:\n    pass\n",
                "ui/tui/app.py": "class TuiApp:\n    pass\n",
                "ui/plain/plain_view.py": "class PlainView:\n    pass\n",
                "agent/controller/run_controller.py": "class RunController:\n    pass\n",
                "agent/persistence/store.py": "class StoreDb:\n    pass\n",
                "model/ai/dp_thing.py": "class DP_Thing:\n    pass\n",
                "utils/helper.py": "class Helper:\n    pass\n",
            },
            tmp_path,
        )
        records, _ = kb_ast_extract.extract(src_root, repo_root)
        by_id = _by_id(records)

        def layer(rid):
            return [t for t in by_id[rid]["tags"] if t.startswith("LAYER_")]

        assert layer("class.FooModel") == ["LAYER_MODEL"]
        assert layer("class.BarAi") == ["LAYER_MODEL"]
        assert layer("class.Panel") == ["LAYER_VIEW"]
        assert layer("class.XScreen") == ["LAYER_VIEW"]
        assert layer("class.TuiApp") == ["LAYER_VIEW"]
        assert layer("class.PlainView") == ["LAYER_VIEW"]
        assert layer("class.RunController") == ["LAYER_CONTROLLER"]
        assert layer("class.StoreDb") == ["LAYER_DP"]
        assert layer("class.DP_Thing") == ["LAYER_DP"]  # DP_ prefix beats /model/
        assert layer("class.Helper") == ["LAYER_UTIL"]


class TestAutoText:
    """Behavior 6: auto-text = bases+abstractmethods, style-linter clean."""

    def test_auto_text_passes_style_linter(self, tmp_path):
        import kb_ast_extract
        import kb_compiler

        src_root, repo_root = _write_tree(
            {
                "agent/model/tools/spec.py": SPEC_PY,
                "agent/model/tools/filesystem_tool.py": FILESYSTEM_TOOL_PY,
                "agent/model/agent.py": AGENT_PY,
                "agent/model/tools/registry.py": REGISTRY_PY,
                "agent/interfaces.py": INTERFACES_PY,
                "agent/model/memory/manager.py": MANAGER_PY,
            },
            tmp_path,
        )
        records, _ = kb_ast_extract.extract(src_root, repo_root)
        assert records, "expected records"

        errors: list[str] = []
        for r in records:
            kb_compiler.validate_style(r["id"], r["text"], errors)
        assert errors == [], f"style errors on auto-text: {errors}"


class TestCoveragePublicOnly:
    """Behavior 7: ALL public classes emitted; _-prefixed skipped; 3 kinds only."""

    def test_public_only_and_three_kinds(self, tmp_path):
        import kb_ast_extract

        src_root, repo_root = _write_tree(
            {
                "agent/model/foo.py": (
                    "class Public:\n    pass\n\n"
                    "class _Private:\n    pass\n"
                ),
            },
            tmp_path,
        )
        records, _ = kb_ast_extract.extract(src_root, repo_root)
        by_id = _by_id(records)

        assert "class.Public" in by_id
        assert "class._Private" not in by_id
        assert {r["kind"] for r in records} <= {"class", "contract", "dep"}


class TestRefsProjectOnly:
    """Behavior 8: stdlib/3rd-party bases excluded from refs."""

    def test_non_project_bases_not_in_refs(self, tmp_path):
        import kb_ast_extract

        src_root, repo_root = _write_tree(
            {
                "agent/model/err.py": (
                    "class AgentError(Exception):\n    pass\n"
                ),
                "agent/model/kind.py": (
                    "from enum import Enum\n\n\n"
                    "class ToolKind(Enum):\n    SENSOR = 1\n"
                ),
            },
            tmp_path,
        )
        records, _ = kb_ast_extract.extract(src_root, repo_root)
        by_id = _by_id(records)

        err = by_id.get("class.AgentError")
        assert err is not None
        assert err["refs"] == []

        kind = by_id.get("class.ToolKind")
        assert kind is not None
        assert kind["refs"] == []
        # Enum base must not spawn a dep edge either
        assert "dep.ToolKind_Enum" not in by_id


class TestDuplicateNames:
    """Behavior 9: duplicate class names -> first-by-sorted-path wins, warned."""

    def test_duplicates_deduped_with_warning(self, tmp_path):
        import kb_ast_extract

        src_root, repo_root = _write_tree(
            {
                "a/thing.py": "class Thing:\n    pass\n",
                "b/thing.py": "class Thing:\n    pass\n",
            },
            tmp_path,
        )
        records, warnings = kb_ast_extract.extract(src_root, repo_root)
        ids = [r["id"] for r in records]

        assert ids.count("class.Thing") == 1
        thing = _by_id(records)["class.Thing"]
        assert thing["src"] == "src/agentx/a/thing.py"  # sorted-path first
        assert any("Thing" in w for w in warnings)


class TestRealTree:
    """Behavior 10: real src/agentx tree -> comprehensive, deterministic."""

    def test_real_tree_coverage_and_determinism(self):
        import kb_ast_extract

        src_root = _REPO_ROOT / "src" / "agentx"
        records1, warnings1 = kb_ast_extract.extract(src_root, _REPO_ROOT)
        records2, _ = kb_ast_extract.extract(src_root, _REPO_ROOT)

        # comprehensive coverage (272+ public classes measured sess 9-11)
        assert len(records1) > 250, f"only {len(records1)} records"

        by_id = _by_id(records1)
        assert "class.Agent" in by_id
        assert "contract.IToolRegistryPartner" in by_id
        assert "class.ToolRegistry" in by_id

        # every record: tier=code, TIER_CODE tag, exactly one LAYER_ tag
        for r in records1:
            assert r["tier"] == "code"
            assert "TIER_CODE" in r["tags"]
            layers = [t for t in r["tags"] if t.startswith("LAYER_")]
            assert len(layers) == 1, f"{r['id']}: layers={layers}"
            assert r["src"].startswith("src/agentx/")

        # deterministic across runs
        assert records1 == records2
