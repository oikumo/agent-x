# STRUCTURE.md — Application Architecture (compressed)

**ARCH:** MVC++ + Abstract Partner + Command + DP
**LAYERS:**
```
entry: main.py → ProviderRegistry → [TUIProvider|ConsoleProvider]
ctrl:  ui/screens/*/  implements: [IMainView|IRagView|IChatView]Partner
view:  ui/screens/*/ + ui/tui/adapters/  implements: [IMainView|IRagView|IChatView]
iface: ui/interfaces.py (ABCs) + providers.py
model: model/{ai,rag,session}/  NO ui imports
dp:    model/*/*_db.py (DP_Session, DP_Rag) — ALL SQL here
```
**DI:** ProviderRegistry.get("tui"|"console") → create_*_view(controller)
**SESSION:** local_sessions/<ts>_<name>/{session.db, rag/<repo>/{db,docs}}
**TESTS:** tests/{unit/{model,ui}, automated/tui/} — 205+ isolated

---

## Layer Rules (Hard)

| Layer | Imports Model | Imports View | Imports Controller | Contains UI | Contains Biz Logic | Contains SQL |
|-------|---------------|--------------|-------------------|-------------|-------------------|--------------|
| Controller | ✅ | ✅ | N/A | ❌ | Orchestration only | ❌ |
| View | ❌ | N/A | ❌ (via Partner ABC) | ✅ | ❌ | ❌ |
| Model | N/A | ❌ | ❌ | ❌ | ✅ Core | ✅ DP only |

---

## Key Patterns

| Pattern | Rule |
|---------|------|
| **Abstract Partner** | `I*View(ABC)` in view file → `*Controller implements I*ViewPartner` |
| **Command (main only)** | `Command(ABC, key, controller).run(args)` — dispatch via `commands[key]` |
| **Data Provider** | `DP_*{insert,load,update,delete}` — all SQL in `*_db.py` |
| **Entity CRUD** | `create/load/update/delete` on persistent objects |

---

## Directory Map (src/agentx/)

```
main.py
model/
  ai/          # LLM providers (AIService facade)
  rag/         # Rag, RagRepository, query/, rag_db.py
  session/     # Session, SessionManager, session_db.py
ui/
  interfaces.py    # IMainView, IRagView, IChatView, IUIProvider (all ABC)
  providers.py     # ProviderRegistry
  common/          # Shared UI (ui_console.py, input/*)
  screens/
    main/   main_controller.py, main_view.py, commands/
    chat/   chat_controller.py, chat_view.py
    rag/    rag_controller.py, rag_view.py, rag_chat_*, rag_repo_selection_*
  tui/
    adapters/      # TUIAdapter, TUIRagAdapter, TUIChatAdapter
```

---

## Config & Enforcement

| File | Role |
|------|------|
| `opencode.jsonc` | Deny: git commit/push, bare python/pip/pytest, .env, README/uv.lock/LICENSE |
| `.opencode/plugins/omt_enforcer.ts` | Gate: `omt_phase` before src/, MVC++ lint after, TDD two-hats |
| `AGENTS.md` | Agent rules |
| `.env` | Secrets (gitignored) |

---

## OMT++ Tools
`omt_phase` · `omt_skip` · `omt_complete` · `omt_testlist` · `omt_red` · `omt_green` · `omt_refactor` · `omt_done` · `omt_status`
`mvc_check.py` · `new_feature.py` · `tdd_check.py`

---

## Refs
- Behavior: `../behavior/BEHAVIOR.md`
- Methodology: `../../omt_agent_guide.md`
- Feature designs: `./features/feature_*/design_*.md`