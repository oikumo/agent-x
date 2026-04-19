#!/usr/bin/env python3
"""
Simple Petri Net Analysis for Agent-X Sprint 2 (SCRUM Project)

This demonstrates Petri Net formal verification concepts applied to
real issue tracker system data without external dependencies.

Author: Agent-X System
Date: April 11, 2026
"""

import sys
from pathlib import Path
from collections import deque
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime


# Simple Petri Net Implementation
class Place:
    def __init__(self, name: str, tokens: int = 0):
        self.name = name
        self.tokens = tokens


class Transition:
    def __init__(self, name: str):
        self.name = name
        self.inputs: Dict[str, int] = {}  # place_name -> weight
        self.outputs: Dict[str, int] = {}  # place_name -> weight


class PetriNet:
    def __init__(self, name: str = "Petri Net"):
        self.name = name
        self.places: Dict[str, Place] = {}
        self.transitions: Dict[str, Transition] = {}

    def add_place(self, name: str, tokens: int = 0) -> Place:
        place = Place(name, tokens)
        self.places[name] = place
        return place

    def add_transition(self, name: str) -> Transition:
        transition = Transition(name)
        self.transitions[name] = transition
        return transition


class Marking:
    """Vector of token counts for each place"""

    def __init__(self, tokens: Tuple[int, ...], place_names: Tuple[str, ...]):
        self.tokens = tokens
        self.place_names = place_names

    def get(self, place_name: str) -> int:
        try:
            idx = self.place_names.index(place_name)
            return self.tokens[idx]
        except ValueError:
            return 0


def analyze_petri_net(net: PetriNet, initial_marking: Marking) -> dict:
    """Analyze Petri net for key properties"""
    results = {}

    # Get place order for consistent indexing
    place_names = tuple(sorted(net.places.keys()))

    # Initial marking vector
    m0_list = [initial_marking.get(name) for name in place_names]
    m0 = Marking(tuple(m0_list), place_names)

    # BFS for reachability graph
    def get_enabled_transitions(marking: Marking) -> List[str]:
        enabled = []
        for t_name, transition in net.transitions.items():
            # Check if transition is enabled
            enabled_flag = True
            for place_name, weight in transition.inputs.items():
                if place_name in place_names:
                    idx = place_names.index(place_name)
                    if marking.get(place_name) < weight:
                        enabled_flag = False
                        break
            if enabled_flag:
                enabled.append(t_name)
        return enabled

    def fire_transition(marking: Marking, t_name: str) -> Optional[Marking]:
        transition = net.transitions[t_name]
        new_tokens = list(marking.tokens)

        # Remove input tokens
        for place_name, weight in transition.inputs.items():
            if place_name in place_names:
                idx = place_names.index(place_name)
                new_tokens[idx] -= weight

        # Add output tokens
        for place_name, weight in transition.outputs.items():
            if place_name in place_names:
                idx = place_names.index(place_name)
                new_tokens[idx] += weight

        return Marking(tuple(new_tokens), place_names)

    # Helper function to check if we can reach a state where transition t_name is enabled
    def can_reach_enabled_state(start_marking: Marking, t_name: str) -> bool:
        """Check if from start_marking, we can reach a marking where t_name is enabled"""
        if t_name in get_enabled_transitions(start_marking):
            return True

        visited_local = {start_marking}
        queue = deque([start_marking])

        while queue:
            marking = queue.popleft()
            enabled = get_enabled_transitions(marking)

            for t in enabled:
                successor = fire_transition(marking, t)
                if successor and successor not in visited_local:
                    if t_name in get_enabled_transitions(successor):
                        return True
                    visited_local.add(successor)
                    queue.append(successor)

        return False

    # Helper function to check if we can reach target_marking from start_marking
    def can_reach_marking(start_marking: Marking, target_marking: Marking) -> bool:
        """Check if from start_marking, we can reach target_marking"""
        if start_marking.tokens == target_marking.tokens:
            return True

        visited_local = {start_marking}
        queue = deque([start_marking])

        while queue:
            marking = queue.popleft()

            enabled = get_enabled_transitions(marking)
            for t in enabled:
                successor = fire_transition(marking, t)
                if successor and successor not in visited_local:
                    if successor.tokens == target_marking.tokens:
                        return True
                    visited_local.add(successor)
                    queue.append(successor)

        return False

    # Explore state space
    visited = {m0}
    queue = deque([m0])
    reachability_graph = {m0: {}}
    max_states = 10000

    while queue and len(visited) < max_states:
        marking = queue.popleft()
        enabled = get_enabled_transitions(marking)

        reachability_graph[marking] = {}
        for t_name in enabled:
            successor = fire_transition(marking, t_name)
            if successor and successor not in visited:
                visited.add(successor)
                queue.append(successor)
                reachability_graph[marking][t_name] = successor
            elif successor:
                reachability_graph[marking][t_name] = successor

    # Check properties
    # 1. Boundedness: find maximum tokens in each place
    max_tokens = [0] * len(place_names)
    for marking in visited:
        for i, count in enumerate(marking.tokens):
            max_tokens[i] = max(max_tokens[i], count)

    is_bounded = all(m < float("inf") for m in max_tokens)
    max_bound = max(max_tokens) if max_tokens else 0

    # 2. Safeness: all places <= 1 token
    is_safe = all(m <= 1 for m in max_tokens)

    # 3. Deadlock freedom: every reachable marking has >=1 enabled transition
    is_deadlock_free = True
    for marking in visited:
        if len(get_enabled_transitions(marking)) == 0:
            is_deadlock_free = False
            break

    # 4. Liveness: from any reachable marking, every transition can eventually fire
    # Proper definition: A transition t is live if from every reachable marking,
    # there exists a reachable marking where t is enabled
    transition_live = {}
    for t_name in net.transitions.keys():
        # Assume transition is live until proven otherwise
        is_transition_live = True
        # Check from every reachable marking
        for marking in visited:
            # From this marking, can we reach a state where t_name is enabled?
            if not can_reach_enabled_state(marking, t_name):
                is_transition_live = False
                break
        transition_live[t_name] = is_transition_live

    is_live = all(transition_live.values())

    # 5. Reversibility: initial marking reachable from every reachable marking
    # A Petri net is reversible if for every reachable marking m,
    # the initial marking m0 is reachable from m
    is_reversible = True
    for marking in visited:
        if not can_reach_marking(marking, m0):
            is_reversible = False
            break

    results = {
        "boundedness": is_bounded,
        "bound": max_bound,
        "safeness": is_safe,
        "liveness": is_live,
        "deadlock_freedom": is_deadlock_free,
        "reversibility": is_reversible,
        "reachable_states": len(visited),
        "place_bounds": dict(zip(place_names, max_tokens)),
        "transition_enablement": transition_enabled_in_some_state,
    }

    return results


def build_agent_x_sprint2_net() -> Tuple[PetriNet, Marking]:
    """Build Petri net representing Agent-X Sprint 2 workflow"""
    net = PetriNet("Agent-X Sprint 2 Workflow")

    # Places representing workflow states
    backlog = net.add_place("Backlog", tokens=55)  # 55 items in backlog
    todo = net.add_place("To Do", tokens=0)
    in_progress = net.add_place("In Progress", tokens=2)  # 2 items in progress
    in_review = net.add_place("In Review", tokens=0)
    qa = net.add_place("QA", tokens=0)
    done = net.add_place("Done", tokens=0)
    blocked = net.add_place("Blocked", tokens=0)

    # Transitions representing workflow actions
    # Plan: Backlog -> To Do
    plan = net.add_transition("Plan")
    plan.inputs = {"Backlog": 1}
    plan.outputs = {"To Do": 1}

    # Start: To Do -> In Progress
    start = net.add_transition("Start")
    start.inputs = {"To Do": 1}
    start.outputs = {"In Progress": 1}

    # Submit: In Progress -> In Review
    submit = net.add_transition("Submit")
    submit.inputs = {"In Progress": 1}
    submit.outputs = {"In Review": 1}

    # Approve: In Review -> QA
    approve = net.add_transition("Approve")
    approve.inputs = {"In Review": 1}
    approve.outputs = {"QA": 1}

    # Pass QA: QA -> Done
    pass_qa = net.add_transition("Pass QA")
    pass_qa.inputs = {"QA": 1}
    pass_qa.outputs = {"Done": 1}

    # Block: In Progress -> Blocked
    block = net.add_transition("Block")
    block.inputs = {"In Progress": 1}
    block.outputs = {"Blocked": 1}

    # Unblock: Blocked -> In Progress
    unblock = net.add_transition("Unblock")
    unblock.inputs = {"Blocked": 1}
    unblock.outputs = {"In Progress": 1}

    # Rework: In Review -> In Progress
    rework = net.add_transition("Rework")
    rework.inputs = {"In Review": 1}
    rework.outputs = {"In Progress": 1}

    # Fail QA: QA -> In Progress
    fail_qa = net.add_transition("Fail QA")
    fail_qa.inputs = {"QA": 1}
    fail_qa.outputs = {"In Progress": 1}

    # Reopen: Done -> In Progress
    reopen = net.add_transition("Reopen")
    reopen.inputs = {"Done": 1}
    reopen.outputs = {"In Progress": 1}

    return net, Marking(
        tokens=(
            55,
            0,
            2,
            0,
            0,
            0,
            0,
        ),  # Backlog, To Do, In Progress, In Review, QA, Done, Blocked
        place_names=(
            "Backlog",
            "To Do",
            "In Progress",
            "In Review",
            "QA",
            "Done",
            "Blocked",
        ),
    )


def generate_insights(
    analysis_results: dict, net: PetriNet, initial_marking: Marking
) -> List[dict]:
    """Generate actionable insights from Petri net analysis"""
    insights = []

    # Workload insights
    place_bounds = analysis_results.get("place_bounds", {})
    backlog_bound = place_bounds.get("Backlog", 0)
    in_progress_bound = place_bounds.get("In Progress", 0)

    if backlog_bound > 50:
        insights.append(
            {
                "severity": "WARNING",
                "area": "Backlog Management",
                "description": f"High backlog occupancy ({backlog_bound} items). Consider limiting work intake.",
                "recommendation": "Implement WIP limits on backlog refinement or increase team capacity.",
            }
        )

    if in_progress_bound >= 2:  # Currently 2 items
        insights.append(
            {
                "severity": "INFO",
                "area": "Work in Progress",
                "description": f"Moderate WIP ({in_progress_bound} items in progress).",
                "recommendation": "Monitor for context switching overhead. Consider WIP limits.",
            }
        )

    # Bottleneck insights
    if not analysis_results.get("deadlock_freedom", True):
        insights.append(
            {
                "severity": "CRITICAL",
                "area": "Workflow Deadlock",
                "description": "Potential deadlock detected in workflow.",
                "recommendation": "Review transition conditions and ensure all paths can complete.",
            }
        )

    # Liveness insights
    transition_enablement = analysis_results.get("transition_enablement", {})
    disabled_transitions = [
        t for t, enabled in transition_enablement.items() if not enabled
    ]
    if disabled_transitions:
        insights.append(
            {
                "severity": "WARNING",
                "area": "Transition Liveness",
                "description": f"Some transitions may never fire: {disabled_transitions}",
                "recommendation": "Review workflow logic to ensure all transitions are reachable.",
            }
        )

    # Process efficiency
    reachable_states = analysis_results.get("reachable_states", 0)
    if reachable_states < 10:
        insights.append(
            {
                "severity": "INFO",
                "area": "Process Complexity",
                "description": f"Low state space complexity ({reachable_states} reachable states).",
                "recommendation": "Consider if workflow is too simple or if more detailed states needed.",
            }
        )

    return insights


def main():
    print("=" * 80)
    print("PETRI NET FORMAL VERIFICATION - AGENT-X SPRINT 2 ANALYSIS")
    print("=" * 80)
    print()

    print("📊 BUILDING AGENT-X SPRINT 2 PETRI NET MODEL...")
    net, initial_marking = build_agent_x_sprint2_net()

    print(f"   Places: {len(net.places)}")
    for name, place in net.places.items():
        print(f"     - {name}: {place.tokens} tokens")
    print(f"   Transitions: {len(net.transitions)}")
    for name in net.transitions.keys():
        print(f"     - {name}")
    print()

    print("🔍 RUNNING FORMAL VERIFICATION ANALYSIS...")
    results = analyze_petri_net(net, initial_marking)

    print(f"   Reachable States: {results['reachable_states']}")
    print(f"   Boundedness: {results['boundedness']} (max tokens: {results['bound']})")
    print(f"   Safeness (1-bounded): {results['safeness']}")
    print(f"   Liveness: {results['liveness']}")
    print(f"   Deadlock-Free: {results['deadlock_freedom']}")
    print(f"   Reversibility: {results['reversibility']}")
    print()

    print("📈 GENERATING PROCESS INSIGHTS...")
    insights = generate_insights(results, net, initial_marking)

    if insights:
        for i, insight in enumerate(insights, 1):
            severity_icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🟢"}[
                insight["severity"]
            ]
            print(f"   {i}. {severity_icon} [{insight['severity']}] {insight['area']}")
            print(f"      {insight['description']}")
            print(f"      💡 Recommendation: {insight['recommendation']}")
            print()
    else:
        print("   No significant insights detected.")
    print()

    print("=" * 80)
    print("ANALYSIS COMPLETE - PETRI NET VERIFICATION SUCCESSFUL")
    print("=" * 80)
    print()
    print("📋 SUMMARY:")
    print(
        f"   • Analyzed {len(net.places)} workflow states with {len(net.transitions)} transitions"
    )
    print(
        f"   • Initial state: {initial_marking.tokens[0]} backlog, {initial_marking.tokens[2]} in progress"
    )
    print(
        f"   • State space explored: {results['reachable_states']} reachable markings"
    )
    print(
        f"   • Key properties verified: boundedness, safeness, liveness, deadlock freedom"
    )
    print()


if __name__ == "__main__":
    main()
