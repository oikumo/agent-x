# architecture.md — MVC++ Architecture (compressed)

# SECTION:META — File Identity (grep:SECTION_META)
# FILE:architecture.md | SCOPE:Layering, dependency rules, patterns, stack, enforcement

# SECTION:SCOPE — What This Covers (grep:SCOPE_)
Layering, dependency rules, core patterns, tech stack, configuration & enforcement.

---

# SECTION:MVCPP — MVC++ Layer Rules (Hard) (grep:MVCPP_)

```
CONTROLLER: App logic, orchestration, dispatch | knows: View+Model | seen by: View(Partner)
VIEW:       UI render, input capture           | knows: Controller(Partner only)
MODEL:      Domain logic, biz rules, data      | knows: nothing about UI
```

| What | Controller | View | Model |
|------|-----------|------|-------|
| Imports Model | ✅ | ❌ | N/A |
| Imports View | ✅ | N/A | ❌ |
| Imports Controller | N/A | ❌ (Partner only) | ❌ |
| Contains UI code | ❌ | ✅ | ❌ |
| Contains biz logic | Orchestration | ❌ | ✅ Core |
| Contains SQL | ❌ | ❌ | ✅ DP only |

> Enforced: `uv run scripts/omt/mvc_check.py` (0 errors baseline)

---

# SECTION:PARTNER — Abstract Partner Pattern (grep:PARTNER_)

```
View ──calls──▶ I*ViewPartner(ABC) ◀──implements── Controller
Controller ──calls──▶ I*View(ABC) ◀──implements── View
```

**Rules:** ABC + @abstractmethod only | Name: `I*ViewPartner` | Defined in `ui/interfaces.py` / `agent/interfaces.py`

| Interface | Controller | View |
|-----------|------------|------|
| `IMainViewPartner` | `MainController` | `IMainView` |
| `IChatViewPartner` | `ChatController` | `IChatView` |
| `IRagViewPartner` | `RagController` | `IRagView` |
| `IAgentViewPartner` | `AgentController` | `IAgentView` |
| ... | 7 more in `agent/interfaces.py` |

> Textual screens: register as virtual subclass: `IAgentViewPartner.register(MyScreen)`

---

# SECTION:FAST_AGENT — Fast Agent (feature_011) Modal UX (grep:FAST_)

| Aspect | Detail |
|--------|--------|
| Entry | `f` key / `⚡ Fast Agent` button |
| Flow | GoalModal → RunningModal → ReflectionModal → ResultModal (ModalScreen stack) |
| Engine | Reuses feature_007 `Agent` + `AgentController` |
| Auto-run | `call_after_refresh` chain; pauses only on reflection proposals |
| Goal completion | Manual (`SuccessCriteria(kind="manual")`) |
| No-op partner | `FastAgentTUIView` swallows UI callbacks during `run_cycle()` |
| Existing Agent | Relabeled `⚙️ Advanced Agent` |

---

# SECTION:PROVIDER — Provider / Adapter Pattern (Console ⇄ TUI) (grep:PROVIDER_)

```
main.py:
  default      → ProviderRegistry.get("console")        # console default
  --tui (+TTY) → ProviderRegistry.get_default()         # = TUIProvider
  ├─ TUIProvider → TUIAdapter → MainTUIScreen (IMainView)
  └─ ConsoleProvider → MainView (IMainView)
```
- `ProviderRegistry` (`ui/providers.py`) holds providers; `tui` auto-registers as registry default (used by `get_default()` and TUI tests)
- `main.py` selects console by default; `--tui` opts into TUI (registry default); `--no-tui` accepted as no-op
- Adapters: thin delegates; `TUIChatAdapter`/`TUIRagAdapter` wired via `set_screen()`
- Fallback: TUI exception → ConsoleProvider

---

# SECTION:COMMAND — Command Pattern (Main Screen Only) (grep:COMMAND_)

```
ui/screens/main/commands/
  commands_base.py   # Command(ABC): __init__(key, controller); run(args)
  commands_parser.py # CommandParser → CommandData(key, args)
  commands.py        # 10 concrete commands
```
Flow: `Input → Parser → MainController.run_command() → commands[key].run(args)`

---

# SECTION:DP — Database Partner (DP) Pattern (grep:DP_)

**All SQL in `DP_*` classes only** (enforced by `mvc_check.py:SQL_OUTSIDE_DP`)

| DP Class | File | DB |
|----------|------|-----|
| `SessionDatabase` (`DP_Session`) | `model/session/session_db.py` | `session.db` |
| `RagDatabase` (`DP_Rag`) | `model/rag/rag_db.py` | `rag.db` |
| `SessionDatabase` (agent) | `agent/persistence/agent_db.py` | `agent_session.db` |

All: stdlib `sqlite3`, idempotent `CREATE TABLE IF NOT EXISTS`, no ORM/Alembic.

---

# SECTION:STACK — Tech Stack (grep:STACK_)

| Concern | Tech |
|---------|------|
| Language | Python via `uv` (bare python/pip/pytest denied) |
| TUI | Textual (Screen, widgets, pilot tests) |
| LLM | LangChain (BaseChatModel, retrieval chains) |
| Providers | OpenRouter (default), OpenAI, Gemini, Ollama, llama.cpp |
| Vector | Chroma (local), Pinecone (cloud) |
| Web | Tavily (Map + Extract) |
| Persistence | stdlib sqlite3 |
| Enforcement | opencode + `.opencode/plugins/omt_enforcer.ts` |

**Env:** `.env` (gitignored) — `OPENROUTER_API_KEY` prompted at boot | console by default; `--tui` (requires TTY) → TUI; `--no-tui` accepted as no-op

---

# SECTION:CONFIG — Config & Enforcement (grep:CONFIG_)

| File | Purpose |
|------|---------|
| `opencode.jsonc` | Deny: git commit/push, bare python/pip/pytest, .env; bash default ask |
| `.opencode/plugins/omt_enforcer.ts` | OMT++ gate: blocks src/ w/o `omt_phase`; blocks tests/ w/o approval; runs mvc_check |
| `AGENTS.md` | Agent rules |
| `scripts/omt/mvc_check.py` | MVC++ linter (View↔Model leaks, non-ABC partners, SQL outside DP, god controllers) |
| `scripts/omt/new_feature.py` | Feature scaffolder |

**Process:** `omt_phase` before `src/` edits → design doc for new_screen/major_feature → artifacts per phase → `omt_complete` to advance.

---

# SECTION:DECISIONS — Key Design Decisions (grep:DECISIONS_)

- **No ORM/Alembic** — stdlib sqlite3 + explicit DDL
- **Agent persistence = snapshot** — `SessionSnapshot` captures config, volatile memory, policy, goal tree root, reflection log position
- **Single-active goal** — `GoalManager` activates one goal; completion promotes next
- **Reflection AI-optional** — skipped when no AI service wired (N11)