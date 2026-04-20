#!/usr/bin/env python3
"""
Test: Lazy Loading Approach Validation

This test verifies that the optimized META.md files:
1. Contain all critical information
2. Use proper references to centralized docs
3. Follow the lazy loading pattern
4. Maintain readability and usability
"""

import os
import re
from pathlib import Path

class TestLazyLoading:
    """Test suite for lazy loading optimization"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test_centralized_files_exist(self):
        """Test: Centralized documents created"""
        print("\n✓ Test: Centralized files exist")
        
        files = [
            '.meta.project_development/DIRECTIVES.md',
            '.meta.project_development/WORKFLOWS.md',
        ]
        
        for f in files:
            path = self.base_path / f
            assert path.exists(), f"Missing: {f}"
            print(f"  ✓ {f}")
        
        self.passed += 1
    
    def test_references_to_centralized(self):
        """Test: Files reference centralized docs"""
        print("\n✓ Test: References to centralized docs")
        
        # Check META_HARNESS.md references DIRECTIVES.md
        meta_harness = self.base_path / 'META_HARNESS.md'
        content = meta_harness.read_text()
        
        assert 'DIRECTIVES.md' in content, "Missing reference to DIRECTIVES.md"
        assert 'WORKFLOWS.md' in content, "Missing reference to WORKFLOWS.md"
        print("  ✓ META_HARNESS.md references centralized docs")
        
        self.passed += 1
    
    def test_core_directives_present(self):
        """Test: All 6 core directives documented"""
        print("\n✓ Test: Core directives complete")
        
        directives_file = self.base_path / '.meta.project_development/DIRECTIVES.md'
        content = directives_file.read_text()
        
        required = [
            'NEVER commit',
            'NEVER add',
            'NEVER modify',
            'ALWAYS check',
            'uv',
            'pyproject.toml'
        ]
        
        for req in required:
            assert req.lower() in content.lower(), f"Missing: {req}"
        
        print(f"  ✓ All 6 directives present")
        self.passed += 1
    
    def test_workflow_patterns(self):
        """Test: All workflow patterns documented"""
        print("\n✓ Test: Workflow patterns complete")
        
        workflows_file = self.base_path / '.meta.project_development/WORKFLOWS.md'
        content = workflows_file.read_text()
        
        workflows = ['Workflow A', 'Workflow B', 'Workflow C', 'Workflow D', 'Workflow E']
        
        for wf in workflows:
            assert wf in content, f"Missing: {wf}"
        
        print(f"  ✓ All 5 workflow patterns present (A-E)")
        self.passed += 1
    
    def test_lazy_loading_structure(self):
        """Test: Files follow lazy loading pattern"""
        print("\n✓ Test: Lazy loading structure")
        
        # Check that files are concise
        meta_files = [
            'META_HARNESS.md',
            '.meta.project_development/META.md',
            '.meta.sandbox/META.md',
            '.meta.experiments/META.md',
            '.meta.tests_sandbox/META.md',
            '.meta.development_tools/META.md'
        ]
        
        for mf in meta_files:
            path = self.base_path / mf
            if path.exists():
                lines = len(path.read_text().split('\n'))
                assert lines < 200, f"{mf} too long: {lines} lines"
                print(f"  ✓ {mf}: {lines} lines (OK)")
        
        self.passed += 1
    
    def test_quality_gates_preserved(self):
        """Test: Quality gates maintained"""
        print("\n✓ Test: Quality gates preserved")
        
        meta_harness = self.base_path / 'META_HARNESS.md'
        content = meta_harness.read_text()
        
        required = [
            'Quality Gates',
            'git log',
            'TDD',
            'tests pass',
            'documented',
            'workspace clean'
        ]
        
        for req in required:
            assert req.lower() in content.lower(), f"Missing: {req}"
        
        print("  ✓ All quality gates present")
        self.passed += 1
    
    def test_no_redundant_content(self):
        """Test: Eliminated redundant repetitions"""
        print("\n✓ Test: No redundant content")
        
        # Count occurrences of core directives in META_HARNESS
        meta_harness = self.base_path / 'META_HARNESS.md'
        content = meta_harness.read_text()
        
        # Should reference directives, not repeat them multiple times
        assert content.count('NEVER commit') <= 2, "Redundant content detected"
        
        print("  ✓ No significant redundancy found")
        self.passed += 1
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("Testing Lazy Loading Optimization")
        print("=" * 60)
        
        tests = [
            self.test_centralized_files_exist,
            self.test_references_to_centralized,
            self.test_core_directives_present,
            self.test_workflow_patterns,
            self.test_lazy_loading_structure,
            self.test_quality_gates_preserved,
            self.test_no_redundant_content,
        ]
        
        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"  ✗ FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                self.failed += 1
        
        print("\n" + "=" * 60)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("=" * 60)
        
        return self.failed == 0

if __name__ == '__main__':
    tester = TestLazyLoading()
    success = tester.run_all_tests()
    exit(0 if success else 1)
