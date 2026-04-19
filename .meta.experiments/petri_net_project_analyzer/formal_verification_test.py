#!/usr/bin/env python3
"""
Formal Mathematical Verification Test for Petri Net Analyzer

This test verifies the mathematical correctness of the Petri net analyzer
by testing it against Petri nets with known properties.
"""

import sys
import unittest
from typing import Dict, List, Tuple
from collections import deque, defaultdict

# Import the Petri net implementation from our analysis script
sys.path.append("/home/oikumo/develop/projects/agent-x/experiments")
from petri_net_analysis_simple import (
    PetriNet,
    Place,
    Transition,
    Marking,
    analyze_petri_net,
)


class TestPetriNetFormalVerification(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        pass

    def test_trivial_petri_net_properties(self):
        """Test a trivial Petri net with one place and no transitions"""
        net = PetriNet("Trivial Net")
        place = net.add_place("p1", tokens=1)

        initial_marking = Marking(tokens=(1,), place_names=("p1",))

        results = analyze_petri_net(net, initial_marking)

        # Should be bounded (max tokens = 1)
        self.assertTrue(results["boundedness"])
        self.assertEqual(results["bound"], 1)

        # Should be safe (1-bounded)
        self.assertTrue(results["safeness"])

        # Should be deadlock-free (no transitions means vacuously true?
        # Actually, with no transitions, there are no enabled transitions in any state)
        # But our implementation considers a marking deadlock if it has 0 enabled transitions
        self.assertFalse(results["deadlock_freedom"])  # No transitions enabled

        # Not live (no transitions can fire)
        self.assertFalse(results["liveness"])

        # Reachable states should be 1 (just the initial marking)
        self.assertEqual(results["reachable_states"], 1)

    def test_simple_bounded_net(self):
        """Test a simple bounded Petri net"""
        net = PetriNet("Simple Bounded Net")
        p1 = net.add_place("p1", tokens=1)
        p2 = net.add_place("p2", tokens=0)

        # Transition: p1 -> p2
        t1 = net.add_transition("t1")
        t1.inputs = {"p1": 1}
        t1.outputs = {"p2": 1}

        initial_marking = Marking(
            tokens=(1, 0),  # p1=1, p2=0
            place_names=("p1", "p2"),
        )

        results = analyze_petri_net(net, initial_marking)

        # Should be bounded (max tokens in any place = 1)
        self.assertTrue(results["boundedness"])
        self.assertEqual(results["bound"], 1)

        # Should be safe (1-bounded)
        self.assertTrue(results["safeness"])

        # Should NOT be deadlock-free (after firing t1, we get p1=0, p2=1 with no enabled transitions)
        self.assertFalse(results["deadlock_freedom"])

        # Should NOT be live (t1 can only fire once)
        self.assertFalse(results["liveness"])

        # Should have 2 reachable states: (1,0) and (0,1)
        self.assertEqual(results["reachable_states"], 2)

    def test_safe_net(self):
        """Test a Petri net that is provably safe"""
        net = PetriNet("Safe Net")
        p1 = net.add_place("p1", tokens=1)
        p2 = net.add_place("p2", tokens=0)
        p3 = net.add_place("p3", tokens=0)

        # Transition t1: p1 -> p2
        t1 = net.add_transition("t1")
        t1.inputs = {"p1": 1}
        t1.outputs = {"p2": 1}

        # Transition t2: p2 -> p3
        t2 = net.add_transition("t2")
        t2.inputs = {"p2": 1}
        t2.outputs = {"p3": 1}

        initial_marking = Marking(
            tokens=(1, 0, 0),  # p1=1, p2=0, p3=0
            place_names=("p1", "p2", "p3"),
        )

        results = analyze_petri_net(net, initial_marking)

        # Should be bounded
        self.assertTrue(results["boundedness"])
        self.assertEqual(results["bound"], 1)

        # Should be safe (1-bounded)
        self.assertTrue(results["safeness"])

        # Should NOT be deadlock-free (final state p1=0,p2=0,p3=1 has no enabled transitions)
        self.assertFalse(results["deadlock_freedom"])

        # Should NOT be live (transitions can only fire in sequence, then stop)
        self.assertFalse(results["liveness"])

        # Should have 3 reachable states: (1,0,0), (0,1,0), (0,0,1)
        self.assertEqual(results["reachable_states"], 3)

    def test_unbounded_net(self):
        """Test an unbounded Petri net"""
        net = PetriNet("Unbounded Net")
        p1 = net.add_place("p1", tokens=1)  # Initial token
        p2 = net.add_place("p2", tokens=0)

        # Transition t1: p1 -> p1 + p2 (creates a token in p2 while keeping p1)
        # This is modeled as: consumes 1 from p1, produces 1 to p1 and 1 to p2
        t1 = net.add_transition("t1")
        t1.inputs = {"p1": 1}
        t1.outputs = {"p1": 1, "p2": 1}

        initial_marking = Marking(
            tokens=(1, 0),  # p1=1, p2=0
            place_names=("p1", "p2"),
        )

        results = analyze_petri_net(net, initial_marking)

        # Should be unbounded (p2 can get arbitrarily many tokens)
        self.assertFalse(results["boundedness"])
        # Our BFS is limited to 10000 states, so we might still see it as bounded in practice
        # But theoretically it's unbounded

        # Should NOT be safe
        self.assertFalse(results["safeness"])

        # Should be deadlock-free (t1 is always enabled as long as p1>=1, which it always is)
        self.assertTrue(results["deadlock_freedom"])

        # Should be live (t1 can always fire)
        self.assertTrue(results["liveness"])

    def test_deadlock_free_net(self):
        """Test a Petri net that is provably deadlock-free"""
        net = PetriNet("Deadlock-Free Net")
        p1 = net.add_place("p1", tokens=1)
        p2 = net.add_place("p2", tokens=0)

        # Transition t1: p1 -> p2
        t1 = net.add_transition("t1")
        t1.inputs = {"p1": 1}
        t1.outputs = {"p2": 1}

        # Transition t2: p2 -> p1
        t2 = net.add_transition("t2")
        t2.inputs = {"p2": 1}
        t2.outputs = {"p1": 1}

        initial_marking = Marking(
            tokens=(1, 0),  # p1=1, p2=0
            place_names=("p1", "p2"),
        )

        results = analyze_petri_net(net, initial_marking)

        # Should be bounded (each place gets at most 1 token)
        self.assertTrue(results["boundedness"])
        self.assertEqual(results["bound"], 1)

        # Should be safe (1-bounded)
        self.assertTrue(results["safeness"])

        # Should be deadlock-free (always either t1 or t2 enabled)
        self.assertTrue(results["deadlock_freedom"])

        # Should be live (both transitions can fire repeatedly)
        self.assertTrue(results["liveness"])

        # Should be reversible (can get back to initial state)
        self.assertTrue(results["reversibility"])

        # Should have 2 reachable states: (1,0) and (0,1)
        self.assertEqual(results["reachable_states"], 2)

    def test_live_net(self):
        """Test a Petri net that is provably live"""
        # This is the same as the deadlock-free net above
        net = PetriNet("Live Net")
        p1 = net.add_place("p1", tokens=1)
        p2 = net.add_place("p2", tokens=0)

        # Transition t1: p1 -> p2
        t1 = net.add_transition("t1")
        t1.inputs = {"p1": 1}
        t1.outputs = {"p2": 1}

        # Transition t2: p2 -> p1
        t2 = net.add_transition("t2")
        t2.inputs = {"p2": 1}
        t2.outputs = {"p1": 1}

        initial_marking = Marking(
            tokens=(1, 0),  # p1=1, p2=0
            place_names=("p1", "p2"),
        )

        results = analyze_petri_net(net, initial_marking)

        # Should be live
        self.assertTrue(results["liveness"])

    def test_reversible_net(self):
        """Test a Petri net that is provably reversible"""
        # Same as deadlock-free/live net
        net = PetriNet("Reversible Net")
        p1 = net.add_place("p1", tokens=1)
        p2 = net.add_place("p2", tokens=0)

        # Transition t1: p1 -> p2
        t1 = net.add_transition("t1")
        t1.inputs = {"p1": 1}
        t1.outputs = {"p2": 1}

        # Transition t2: p2 -> p1
        t2 = net.add_transition("t2")
        t2.inputs = {"p2": 1}
        t2.outputs = {"p1": 1}

        initial_marking = Marking(
            tokens=(1, 0),  # p1=1, p2=0
            place_names=("p1", "p2"),
        )

        results = analyze_petri_net(net, initial_marking)

        # Should be reversible
        self.assertTrue(results["reversibility"])


def run_mathematical_verification():
    """Run the formal mathematical verification tests"""
    print("=" * 70)
    print("FORMAL MATHEMATICAL VERIFICATION OF PETRI NET ANALYZER")
    print("=" * 70)
    print()

    # Create a test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPetriNetFormalVerification)

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ ALL MATHEMATICAL VERIFICATION TESTS PASSED")
        print(
            "   The Petri net analyzer is mathematically correct for the tested properties."
        )
    else:
        print("❌ SOME MATHEMATICAL VERIFICATION TESTS FAILED")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")

        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")

        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")

    print("=" * 70)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_mathematical_verification()
    sys.exit(0 if success else 1)
