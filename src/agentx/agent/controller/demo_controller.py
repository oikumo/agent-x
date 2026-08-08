"""DemoController — demo-scenario loading and display info (feature_010).

Extracted from ``agent_controller.py`` to keep that file under the 300-LOC
god-controller limit (feature_024 regression).  Mirrors the thin-controller
pattern of :class:`SessionController` / :class:`ToolController`: holds an
``Agent`` and an optional :class:`IAgentViewPartner`, delegates to the
:class:`IAgentModelPartner` facade, no SQL, no direct Model internals access
beyond the contract.
"""

from __future__ import annotations

from typing import Any

from agentx.agent.interfaces import IAgentViewPartner
from agentx.agent.model.agent import Agent
from agentx.agent.types import (
    ActionType,
    Goal,
    GoalType,
    PolicyAction,
    PolicyRule,
    RuleMetadata,
    RuleSource,
    SuccessCriteria,
)


class DemoController:
    """Handles demo-scenario seeding and display info (operation_spec §demo)."""

    def __init__(self, agent: Agent, view: IAgentViewPartner | None = None) -> None:
        self._agent = agent
        self._view = view

    def set_view(self, view: IAgentViewPartner | None) -> None:
        self._view = view

    def load_demo_scenario_by_name(self, name: str) -> bool:
        """Load + apply a named demo scenario (operation_spec §load_demo_scenario_by_name).

        Clears state, seeds sandbox files, submits the scenario goal, and installs
        the scenario policy rules.  Returns ``True`` when the goal was installed.
        """
        import uuid

        from agentx.agent.demo.scenarios import get_scenario, seed_sandbox_files

        scenario = get_scenario(name)
        if scenario is None:
            if self._view:
                self._view.show_message(
                    f"Unknown demo scenario: {name!r} (use 'a' or 'b')"
                )
            return False
        try:
            self._agent.clear_state()
            seed_sandbox_files(scenario, self._agent.sandbox_root)  # L16 (feature_015)
        except Exception as exc:  # noqa: BLE001 — surface to the view, do not crash
            if self._view:
                self._view.show_message(f"Demo seed failed: {exc}")
            return False

        # --- scenario goal ---
        goal_spec = scenario.goal
        goal = Goal(
            id=str(uuid.uuid4()),
            description=goal_spec.description,
            type=GoalType.USER_OBJECTIVE,
            priority=goal_spec.priority,
            success_criteria=SuccessCriteria(
                kind=goal_spec.success_kind,
                expression=goal_spec.success_expression,
                tool_id=goal_spec.success_tool_id,
            ),
        )
        self._agent.submit_goal(goal)

        # --- scenario rules (skip any that fail to compile/conflict) ---
        for rule_spec in scenario.rules:
            try:
                action_type = ActionType(rule_spec.action_type)
            except ValueError:
                continue
            rule = PolicyRule(
                id=str(uuid.uuid4()),
                condition_expr=rule_spec.condition_expr,
                action=PolicyAction(type=action_type, parameters=dict(rule_spec.parameters)),
                priority=rule_spec.priority,
                metadata=RuleMetadata(source=RuleSource.USER_DEFINED, created_by="demo"),
            )
            self._agent.update_policy(rule)

        if self._view:
            self._view.show_message(f"Demo scenario loaded: {scenario.name}")
            self._view.show_status(self._agent.get_status())
            self._view.refresh_goal_tree()
        return True

    def get_demo_scenario_info(self, name: str) -> dict[str, Any] | None:
        """Return display info for a scenario as a plain dict (View must not import Model).

        Returns ``None`` for an unknown key.  Keys: ``key``, ``name``,
        ``description``, ``files``.
        """
        from agentx.agent.demo.scenarios import get_scenario

        scenario = get_scenario(name)
        if scenario is None:
            return None
        return {
            "key": scenario.key,
            "name": scenario.name,
            "description": scenario.description,
            "files": list(scenario.files),
        }
