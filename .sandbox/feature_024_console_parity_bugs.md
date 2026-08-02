# feature_024.no_tui_full_features — Bug Analysis & Fix Alternatives

> **Date:** 2026-08-02  
> **Workflow:** `feature_fix.md` (steps 1-3: inspect → identify → propose alternatives)  
> **Status:** Analysis complete, awaiting user decision (step 4)

---

## 1. Executive Summary

The feature_024 implementation (console parity for ReAct, Coding, Models, Agent, Fast Agent) **passes all 37 unit tests** but **does not work as expected at runtime**. The tests use `MagicMock()` for controllers, so they only verify the VIEW side calls `controller.send_message()`. They never exercise the real controllers or the actual wiring path (`MainController.show_agent()` → `AgentAdapter.create_agent()` → `ConsoleAgentView` → `AgentController.send_message()` → `run_cycle()`).

**Five categories of bugs** were found through end-to-end characterization tests:

---

## 2. Bugs Found

### Bug #1: `ConsoleAgentView` / `ConsoleFastAgentView` violate `IAgentViewPartner` contract (m9 isinstance check fails)

**Location:** `src/agentx/ui/screens/agent/agent_view.py`, `src/agentx/ui/screens/fast_agent/fast_agent_view.py`

**Details:**
- `IAgentViewPartner` (in `agentx.agent.interfaces`) declares 6 abstract methods:
  `show_status`, `show_reflection_log`, `show_memory_view`, `show_policy_editor`, `refresh_goal_tree`, `show_message`
- Console views implement 5 of 6 — **missing `show_memory_view`**
- `AgentAdapter._wire_view()` and `AgentAdapter.create_fast()` perform **m9 `isinstance(screen, IAgentViewPartner)` check** — raises `TypeError` if False
- Console code path uses `controller.set_view(cast("IAgentViewPartner", agent_view))` — the `cast` is a **NO-OP at runtime**, silently swallowing the contract violation

**Impact:** If any code path calls `controller.show_memory_view()` (or the view is ever checked with `isinstance`), it crashes with `AttributeError` or `TypeError`.

**Evidence:**
```python
>>> isinstance(ConsoleAgentView(controller), IAgentViewPartner)
False
>>> [m for m in IAgentViewPartner.__abstractmethods__ if not hasattr(ConsoleAgentView, m)]
['show_memory_view']
```

---

### Bug #2: `ReactController` / `CodingController` do NOT implement the console partner ABCs (`IConsoleReactViewPartner` / `IConsoleCodingViewPartner`)

**Location:** `src/agentx/ui/screens/react/react_controller.py`, `src/agentx/ui/tui/screens/coding/coding_controller.py`

**Details:**
- Console partner ABCs (`agentx.ui.interfaces`) declare:
  - `IConsoleReactViewPartner`: `process_user_message`, `cancel`, `is_running`, `get_history`, `close`, `start_new_conversation`
  - `IConsoleCodingViewPartner`: same
- **Real controllers implement `send_message` NOT `process_user_message`** (they inherit `IReactViewPartner` / `ICodingViewPartner` which declare `send_message`)
- The console views (`ConsoleReactView.show()` line 30, `ConsoleCodingView.show()`) call `self.controller.send_message(user_input)` — this works by duck-typing (`Any`) but **violates the declared interface**

**Impact:** The declared ABCs are meaningless; `isinstance(react_controller, IConsoleReactViewPartner)` returns `False`. The architecture has a **design-vs-implementation drift** where the interface says one method name but implementations use another.

**Evidence:**
```python
>>> [m for m in IConsoleReactViewPartner.__abstractmethods__ if not hasattr(ReactController, m)]
['process_user_message']
>>> isinstance(ReactController(), IConsoleReactViewPartner)
False
```

---

### Bug #3: `ConsoleReactView` / `ConsoleCodingView` lack streaming callback methods — token streaming silently no-ops

**Location:** `src/agentx/ui/screens/react/react_view.py`, `src/agentx/ui/tui/screens/coding/coding_view.py` (console views)

**Details:**
- `ReactController._run_agent()` passes 7 streaming callbacks to `service.stream_agent()`:
  `on_reasoning` → `show_thinking`
  `on_tool_call` → `show_tool_call`
  `on_tool_result` → `show_tool_result`
  `on_answer` → `show_answer_chunk`
  `on_done` → `show_answer_final`
  `on_error` → `show_error`
- All use `getattr(view, "show_X", lambda *_: None)` — **silent no-op fallback**
- TUI screens (`ReactTUIScreen`, `CodingTUIScreen`) implement ALL these methods
- Console views (`ConsoleReactView`, `ConsoleCodingView`) implement **NONE** of them
- Only `show_partial_message` (maps to `show_answer_chunk`) exists via `IReactView`/`ICodingView` interface — but the callback names differ

**Impact:** ReAct and Coding agents in console mode **do not stream tokens** — the user sees nothing until the full answer arrives (or nothing at all if answer is only sent via `show_answer_final`).

**Evidence:**
```python
>>> hasattr(ConsoleReactView, "show_thinking")
False
>>> hasattr(ConsoleReactView, "show_answer_chunk")
False
```

---

### Bug #4: `AgentController.is_running` returns `True` after one `send_message` cycle completes — breaks REPL exit logic

**Location:** `src/agentx/agent/controller/agent_controller.py` line 209

**Details:**
```python
@property
def is_running(self) -> bool:
    return self._agent.state != AgentState.PERCEIVING
```

After `send_message` submits a goal and runs one cycle, `agent.state` returns to `PERCEIVING` (line 282, 305, 339, 407 in agent.py). So `is_running` returns `False` immediately after the cycle. **This is correct behavior** — but the console view REPL loops (`ConsoleAgentView.show()`, `ConsoleFastAgentView.show()`) only exit on **empty user input**, they don't check `is_running`. This is fine for the REPL pattern, but the `is_running` property is semantically inverted compared to React/Coding where `is_running` means "agent thread is alive".

**Impact:** Low — console REPLs work correctly. But the `is_running` property has different semantics than `IReactViewPartner.is_running` (thread-alive vs not-idle), violating Liskov if any code treats them polymorphically.

---

### Bug #5: `IConsoleAgentViewPartner` / `IConsoleFastAgentViewPartner` are never actually implemented by `AgentController` as ABCs

**Location:** `src/agentx/agent/controller/agent_controller.py`

**Details:**
- `AgentController` has all the methods: `send_message`, `cancel`, `is_running`, `get_history`, `close`, `start_new_conversation` (+ `get_cycle_summary` for fast-agent)
- But it **does not inherit** from `IConsoleAgentViewPartner` or `IConsoleFastAgentViewPartner`
- `isinstance(controller, IConsoleAgentViewPartner)` returns `False`
- The `cast` in `MainController.show_agent()` / `show_fast_agent()` hides this

**Impact:** Same as Bug #2 — the ABCs are dead code, no runtime enforcement.

---

## 3. Fix Alternatives

### Alternative A: Fix the Interface Drift (Recommended — minimal, surgical)

**Scope:** Align the console partner ABCs with reality. The views already call `send_message`; the real controllers already implement `send_message`. The ABCs are wrong.

**Changes:**
1. **Delete `IConsoleReactViewPartner` and `IConsoleCodingViewPartner`** from `interfaces.py` — they declare the wrong method (`process_user_message`) and no real class implements them.
2. **Update `ConsoleProvider.create_react_view` / `create_coding_view`** to accept `IReactViewPartner` / `ICodingViewPartner` (the TUI-side ABCs that correctly declare `send_message`).
3. **Update `ConsoleReactView` / `ConsoleCodingView`** type hints to use `IReactViewPartner` / `ICodingViewPartner` (the real implemented ABC).
4. **Add missing streaming callbacks** to `ConsoleReactView` / `ConsoleCodingView`: `show_thinking`, `show_tool_call`, `show_tool_result`, `show_answer_chunk`, `show_answer_final`, `show_error`. Map to `console.stream_write` / `console.info` / `console.error` appropriately.
5. **Add `show_memory_view`** to `ConsoleAgentView` / `ConsoleFastAgentView` (can be no-op or display memory query results).
6. **Register `AgentController` as virtual subclass** of `IConsoleAgentViewPartner` / `IConsoleFastAgentViewPartner` (or delete those ABCs and use `IAgentViewPartner` with a superset interface — see Alt B).

**Pros:** Minimal diff; fixes the actual runtime contract violations; streaming works; m9 checks pass.
**Cons:** Requires adding 6 streaming methods to each console view; some ABC churn.

---

### Alternative B: Unify the Partner Hierarchy (Cleaner architecture)

**Scope:** Redesign the partner interfaces so console and TUI share the same ABCs where possible.

**Changes:**
1. **Merge `IReactViewPartner` and `IConsoleReactViewPartner`** → single `IReactViewPartner` with `send_message` (already correct). Same for Coding.
2. **Make `IAgentViewPartner` the single ABC for both console and TUI** — add `send_message`, `cancel`, `is_running`, `get_history`, `close`, `start_new_conversation` to it (currently it's TUI-only with `show_status`, `show_reflection_log`, `show_memory_view`, `show_policy_editor`, `refresh_goal_tree`, `show_message`). **This is the correct interface for AgentController**.
3. **Delete** `IConsoleAgentViewPartner`, `IConsoleFastAgentViewPartner`, `IConsoleReactViewPartner`, `IConsoleCodingViewPartner`.
4. **Update `ConsoleProvider` factories** to accept the unified ABCs.
5. **Update console views** to implement the TUI-side methods they need (`show_memory_view` as no-op, streaming callbacks for React/Coding).
6. **Register `AgentController` as virtual subclass of unified `IAgentViewPartner`** (it already has all methods).
7. **ReactController / CodingController already implement the unified `IReactViewPartner` / `ICodingViewPartner`** — no change needed.

**Pros:** Cleaner architecture; single source of truth; no ABC duplication; m9 checks work naturally.
**Cons:** Larger diff; touches `IAgentViewPartner` which is used by TUI screens (but they already implement the extra methods as no-ops or can be made optional with default implementations).

---

### Alternative C: Make ABCs "structural" with `@runtime_checkable` Protocol (Python 3.8+)

**Scope:** Use `Protocol` instead of `ABC` so duck-typing works and `isinstance` checks pass without inheritance.

**Changes:**
1. Convert all partner interfaces from `ABC` to `Protocol` (with `@runtime_checkable`).
2. This makes `isinstance(controller, IConsoleAgentViewPartner)` return `True` if the controller has the right methods (structural subtyping).
3. Still need to add missing methods to console views (streaming callbacks, `show_memory_view`).
4. Still need to fix React/Coding console partner method names (Protocol would need to declare `send_message`, not `process_user_message`).

**Pros:** Zero inheritance changes; `isinstance` works automatically; embraces Python's duck-typing.
**Cons:** `Protocol` is not enforced at class definition time (no `__abstractmethods__`); some team members prefer ABC for explicit contracts; adds `typing_extensions` dependency if Python < 3.8 (we're 3.14 so OK).

---

### Alternative D: Keep Current ABCs but Fix Console Views to Match (Backward-compatible with design docs)

**Scope:** Keep the design-doc-declared `process_user_message` in the ABCs; add adapter methods to real controllers.

**Changes:**
1. Add `process_user_message = send_message` alias to `ReactController`, `CodingController`, `AgentController`.
2. Add all missing streaming callbacks to `ConsoleReactView` / `ConsoleCodingView`.
3. Add `show_memory_view` to `ConsoleAgentView` / `ConsoleFastAgentView`.
4. Register real controllers as virtual subclasses of the console ABCs.
5. This keeps the design docs accurate (they declare `process_user_message` as the console partner method).

**Pros:** Design docs stay unchanged; explicit method name for console path.
**Cons:** Adds redundant aliases; `process_user_message` vs `send_message` confusion persists; more code to maintain.

---

## 4. Recommendation

**Alternative A** (Fix Interface Drift) is the best balance:
- Minimal surgical changes
- Aligns code with reality (views already call `send_message`)
- Fixes streaming (user-visible bug)
- Fixes m9 contract (architectural bug)
- Can be done in one Programming phase with TDD

**Alternative B** (Unified Hierarchy) is architecturally cleaner but larger scope — worth considering if we want to refactor the whole partner system. Since feature_024 is "done" in Testing phase, **Alt A is the pragmatic fix for the immediate bugs**.

---

## 5. Next Steps (per workflow)

1. **User chooses alternative** (A / B / C / D / other)
2. **Execute fix** via `omt_phase` + TDD
3. **Verify** with end-to-end characterization tests (real agents, not mocks)
4. **Update this document** with results

---

## 6. Related Files to Modify (for Alternative A)

| File | Change |
|------|--------|
| `src/agentx/ui/interfaces.py` | Delete `IConsoleReactViewPartner`, `IConsoleCodingViewPartner`; update `create_react_view`/`create_coding_view` factory signatures |
| `src/agentx/ui/providers.py` | Update `ConsoleProvider.create_react_view` / `create_coding_view` type hints |
| `src/agentx/ui/screens/react/react_view.py` | Add 6 streaming callbacks; type hint `IReactViewPartner` |
| `src/agentx/ui/tui/screens/coding/coding_view.py` (console) | Add 6 streaming callbacks; type hint `ICodingViewPartner` |
| `src/agentx/ui/screens/agent/agent_view.py` | Add `show_memory_view` (no-op) |
| `src/agentx/ui/screens/fast_agent/fast_agent_view.py` | Add `show_memory_view` (no-op) |
| `src/agentx/agent/controller/agent_controller.py` | Register as virtual subclass of `IConsoleAgentViewPartner`/`IConsoleFastAgentViewPartner` (or delete those) |

---

## 7. Test Strategy (TDD)

For each fix:
1. **RED**: Write characterization test that fails on current code (e.g., `isinstance(ctrl, IReactViewPartner)` or `view.show_thinking` called)
2. **GREEN**: Implement the method / fix the ABC
3. **REFACTOR**: Clean up
4. **E2E**: Run full `agentx --no-tui` simulation: `react` → type message → verify streaming tokens appear; `agent` → type message → verify response; `fast-agent` → verify cycle summary

This ensures the fix works at runtime, not just in mocked unit tests.