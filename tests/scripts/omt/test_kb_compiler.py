"""Tests for kb_compiler.py — Application Knowledge Base compiler."""

import json
import sys
from pathlib import Path

# Add scripts/omt to path for importing kb_compiler
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "omt"))


def _make_minimal_kb_omt(tmp_dir: Path) -> Path:
    """Write a minimal .kb.omt source file for testing."""
    src = tmp_dir / "test.kb.omt"
    src.write_text("""\
@version akb_hdl n=1
@var kb_paths : .meta/doc/omt++
@var kb_index : .meta/.omt/kb.index.jsonl

@doc arch.mvcpp tags="ARCH_MVCPP,TIER_CORE" refs="arch.partner,flow.boot" tier=core : MVC++: View←Model BLOCK, Model←View BLOCK, Controller≤300, SQL∉DP, print∉Controller
@doc arch.partner tags="ARCH_PARTNER,TIER_CORE" tier=core : Partner=ABC+abstractmethod, Console↔TUI via IUIProvider, AgentController→virtual subclass
@flow boot tags="FLOW_BOOT,TIER_CORE" refs="arch.mvcpp" tier=core : main→AppModel→MainScreen→CommandRegistry→Agent.run_cycle
@xref arch_mvcpp tags="XREF_ARCH.MVCPP" : MVC++ layer rules: View←Model BLOCK, Model←View BLOCK, Controller≤300, SQL∉DP, print∉Controller
""")
    return src


class TestKbCompilerBuild:
    """Behavior 1: kb_compiler build produces kb.index.jsonl and kb.ir.json."""

    def test_build_produces_index_and_ir(self, tmp_path):
        """Parse a minimal .kb.omt source and verify both output files."""
        import kb_compiler  # imported lazily — kb_compiler.py may not exist yet (RED phase)

        # Arrange
        src_path = _make_minimal_kb_omt(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        index_path = out_dir / "kb.index.jsonl"
        ir_path = out_dir / "kb.ir.json"

        # Act: parse source
        text = Path(src_path).read_text()
        errors: list[str] = []
        records = kb_compiler.parse(text, errors)
        assert len(errors) == 0, f"Parse errors: {errors}"
        assert len(records) >= 4, f"Expected >=4 records, got {len(records)}"

        # Build IR
        ir = kb_compiler.build_ir(records, src_path)
        assert ir is not None
        assert "version" in ir
        assert "generated_from" in ir

        # Build index
        index_text = kb_compiler.render_kb_index(records, src_path)
        assert index_text
        index_path.write_text(index_text)

        ir_text = json.dumps(ir, indent=2, sort_keys=True)
        ir_path.write_text(ir_text)

        # Assert: index.jsonl exists with required schema
        assert index_path.exists()
        index_lines = [
            json.loads(line) for line in index_path.read_text().strip().split("\n") if line.strip()
        ]
        assert len(index_lines) >= 4, f"Expected >=4 index lines, got {len(index_lines)}"

        rec = index_lines[0]
        for key in ("id", "kind", "tags", "text", "src", "line"):
            assert key in rec, f"Missing key '{key}' in index record"

        # Assert: ir.json exists
        assert ir_path.exists()
        ir_data = json.loads(ir_path.read_text())
        assert "version" in ir_data
        assert "records" in ir_data
        assert len(ir_data["records"]) == len(records)


class TestKbCompilerStyle:
    """Behavior 2-5: Style linter, xref validation, deduplicate, budget."""

    def test_rejects_too_long_text(self, tmp_path):
        """text field >300 chars → error."""
        import kb_compiler

        errors: list[str] = []
        long_text = "a " * 310  # ~620 chars with spaces
        kb_compiler.validate_style("test_id", long_text, errors)
        assert len(errors) > 0
        assert any("exceeds" in e.lower() or "300" in e for e in errors)

    def test_rejects_stopwords(self, tmp_path):
        """Stopwords: the, must, should, ensure → flagged."""
        import kb_compiler

        errors: list[str] = []
        kb_compiler.validate_style(
            "test_id",
            "the must ensure should verify",
            errors,
        )
        assert len(errors) > 0, f"Expected stopwords error, got: {errors}"

    def test_accepts_clean_compact_text(self, tmp_path):
        """Compact text with symbols → no errors."""
        import kb_compiler

        errors: list[str] = []
        kb_compiler.validate_style(
            "test_id",
            "ARCH: View←Model BLOCK, Controller≤300, DP←SQL",
            errors,
        )
        assert len(errors) == 0

    def test_rejects_unresolved_xref(self, tmp_path):
        """ref points to nonexistent doc → error."""
        import kb_compiler

        src = tmp_path / "xref_test.kb.omt"
        src.write_text("@doc a tags=\"ARCH\" refs=\"BOGEY\" : A doc\n")
        text = src.read_text()
        errors: list[str] = []
        records = kb_compiler.parse(text, errors)
        kb_compiler.check_refs(records, errors)
        assert len(errors) > 0
        assert any("ref" in e.lower() for e in errors)

    def test_rejects_duplicate_doc_id(self, tmp_path):
        """Duplicate ID within same kind → error."""
        import kb_compiler

        src = tmp_path / "dup.kb.omt"
        src.write_text("@doc x tags=\"Tx\" : A\n@doc x tags=\"Tx\" : B\n")
        text = src.read_text()
        errors: list[str] = []
        records = kb_compiler.parse(text, errors)
        kb_compiler.check_ids(records, errors)
        assert len(errors) > 0

    def test_budget_machinery_removed(self):
        """kb_index budget removed (feature_kb_akb v2: index UNBOUNDED)."""
        import kb_compiler

        assert not hasattr(kb_compiler, "DEFAULT_BUDGETS")
        assert not hasattr(kb_compiler, "check_budget")


class TestKbCompilerCli:
    """Behavior 8: CLI build compiles multiple .kb.omt files into combined index + IR."""

    def test_build_multi_file_produces_combined_index(self, tmp_path):
        """Build from directory with multiple .kb.omt files → produces combined kb.index.jsonl + kb.ir.json."""
        import kb_compiler

        # Arrange: create three .kb.omt source files in src_dir
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        (src_dir / "arch.kb.omt").write_text("""\
@version akb_hdl n=1
@doc mvcpp tags="ARCH_MVCPP,TIER_CORE" tier=core : MVC++: View←Model BLOCK, Controller≤300
@doc partner tags="ARCH_PARTNER,TIER_CORE" tier=core : Partner=ABC+abstractmethod
""")
        (src_dir / "flow.kb.omt").write_text("""\
@version akb_hdl n=1
@flow boot tags="FLOW_BOOT,TIER_CORE" tier=core : main→AppModel→MainScreen→Agent.run_cycle
""")
        (src_dir / "features.kb.omt").write_text("""\
@feature f001 tags="FEAT_F001" tier=reference : Petri-net session goals
""")

        errors: list[str] = []
        records: list = []
        for src_file in sorted(src_dir.glob("*.kb.omt")):
            text = src_file.read_text()
            records.extend(kb_compiler.parse(text, errors, src=str(src_file)))
        assert len(errors) == 0, f"Parse errors: {errors}"
        assert len(records) == 4  # 3 files: 2 + 1 + 1 content records

        # Validate all records
        for r in records:
            kb_compiler.validate_style(r.id, r.text, errors)
        assert len(errors) == 0, f"Style errors: {errors}"

        kb_compiler.check_refs(records, errors)
        kb_compiler.check_ids(records, errors)
        assert len(errors) == 0, f"Validation errors: {errors}"

        # Build index + IR
        ir = kb_compiler.build_ir(records, str(src_dir / "*.kb.omt"))
        assert ir is not None
        assert ir["version"] == "akb_hdl.1"
        assert len(ir["records"]) == 4

        index_text = kb_compiler.render_kb_index(records, str(src_dir / "*.kb.omt"))
        index_path = out_dir / "kb.index.jsonl"
        index_path.write_text(index_text)
        ir_path = out_dir / "kb.ir.json"
        ir_path.write_text(json.dumps(ir, indent=2, sort_keys=True))

        # Assert
        assert index_path.exists()
        index_lines = [json.loads(line) for line in index_path.read_text().strip().split("\n") if line.strip()]
        assert len(index_lines) == 4
        ids = {r["id"] for r in index_lines}
        assert ids == {"doc.mvcpp", "doc.partner", "flow.boot", "feature.f001"}

        assert ir_path.exists()
        ir_data = json.loads(ir_path.read_text())
        assert len(ir_data["records"]) == 4


class TestKbCompilerBuildUnified:
    """feature_kb_akb P0: build_index = curated + AST skeleton + overlay merge."""

    def _make_tree(self, tmp_path: Path, overlay: str) -> tuple[Path, Path]:
        kb_dir = tmp_path / "kb"
        kb_dir.mkdir()
        (kb_dir / "arch.kb.omt").write_text(
            '@version akb_hdl n=1\n'
            '@doc mvcpp tags="ARCH_MVCPP,TIER_CORE" tier=core : MVC++ layers\n'
        )
        (kb_dir / "code.kb.omt").write_text(overlay)
        src_root = tmp_path / "src" / "agentx"
        (src_root / "model").mkdir(parents=True)
        (src_root / "model" / "foo.py").write_text(
            "from abc import ABC, abstractmethod\n\n\n"
            "class IBar(ABC):\n"
            "    @abstractmethod\n"
            "    def bar(self): ...\n\n\n"
            "class Foo(IBar):\n"
            "    def bar(self): ...\n\n\n"
            "class Baz:\n"
            "    pass\n"
        )
        return kb_dir, src_root

    def test_build_merges_curated_skeleton_overlay(self, tmp_path):
        """Unified entries: overlay text wins, refs union, skeleton src/line win."""
        import kb_compiler

        kb_dir, src_root = self._make_tree(
            tmp_path,
            '@version akb_hdl n=1\n'
            '@class Foo tier=code refs="contract.IBar" : Foo curated concept text\n',
        )
        entries, warnings, errors = kb_compiler.build_index(kb_dir, src_root, tmp_path)
        assert errors == [], f"errors: {errors}"
        by_id = {e["id"]: e for e in entries}

        # curated kept; skeleton comprehensive (incl. un-curated Baz)
        assert "doc.mvcpp" in by_id
        assert "contract.IBar" in by_id
        assert "class.Foo" in by_id
        assert "class.Baz" in by_id
        assert "dep.Foo_IBar" in by_id

        # overlay text wins; refs = union(skeleton, overlay)
        assert by_id["class.Foo"]["text"] == "Foo curated concept text"
        assert set(by_id["class.Foo"]["refs"]) == {"contract.IBar"}
        assert by_id["class.Foo"]["tier"] == "code"

        # skeleton src/line win over overlay bookkeeping
        assert by_id["class.Foo"]["src"] == "src/agentx/model/foo.py"

        # un-curated keeps auto-text
        assert by_id["class.Baz"]["text"] == "Baz"

    def test_overlay_not_emitted_as_curated(self, tmp_path):
        """code.kb.omt excluded from the curated glob: code ids emit exactly once."""
        import kb_compiler

        kb_dir, src_root = self._make_tree(
            tmp_path,
            '@version akb_hdl n=1\n'
            '@class Foo tier=code : Foo curated concept text\n',
        )
        entries, _, errors = kb_compiler.build_index(kb_dir, src_root, tmp_path)
        assert errors == [], f"errors: {errors}"
        ids = [e["id"] for e in entries]
        assert ids.count("class.Foo") == 1
        foo = {e["id"]: e for e in entries}["class.Foo"]
        assert foo["src"].startswith("src/agentx/")

    def test_orphan_overlay_key_warns(self, tmp_path):
        """Overlay key with no matching skeleton id -> warning, not emitted."""
        import kb_compiler

        kb_dir, src_root = self._make_tree(
            tmp_path,
            '@version akb_hdl n=1\n'
            '@class Ghost tier=code : Ghost has no matching class\n',
        )
        entries, warnings, errors = kb_compiler.build_index(kb_dir, src_root, tmp_path)
        assert any("class.Ghost" in w for w in warnings), f"warnings: {warnings}"
        assert "class.Ghost" not in {e["id"] for e in entries}