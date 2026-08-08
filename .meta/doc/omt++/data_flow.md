# data_flow.md — Runtime Sequences (compressed)

# SECTION:META — File Identity (grep:SECTION_META)
# FILE:data_flow.md | SCOPE:Boot, navigation, agent cycle, demo, chat, RAG ingestion/query, session, persistence

# SECTION:SCOPE — What This Covers (grep:SCOPE_)
Boot sequence, screen navigation, agent cycle, demo flow, chat streaming, RAG ingestion/query, session lifecycle, agent persistence.

---

# SECTION:BOOT — Boot Sequence (main.py) (grep:BOOT_)

```
load_dotenv() → prompt API key if missing
main():
  show() → print version
  use_tui = --tui AND stdin.isatty() AND stdout.isatty()
  provider = use_tui ? ProviderRegistry.get_default() : ProviderRegistry.get("console")
  # note: --no-tui accepted as backwards-compat no-op (console is default)
  provider.initialize()
  main_controller = MainController(provider)   # loads 10 commands
  main_view = provider.create_main_view(main_controller)
  main_controller.view = main_view
  try: main_view.show()  # TUI: run TUIApplication
  except KeyboardInterrupt → "Interrupted"
  except Exception (TUI) → fallback to ConsoleProvider
  finally: provider.shutdown()
```

---

# SECTION:NAV — TUI Screen Navigation (grep:NAV_)

```
TUIApplication.on_mount → push MainTUIScreen
  c / "chat"     → action_open_chat  → controller.show_chat() + push ChatTUIScreen + TUIChatAdapter.set_screen()
  r / "rag"      → action_open_rag   → controller.show_rag() + push RagTUIScreen + TUIRagAdapter.set_screen()
  a              → action_open_agent → controller.show_agent() (AgentAdapter.create_agent, resume=True) + push AgentTUIScreen
  typed input    → on_input_submitted → controller.run_command(text) → CommandParser → Command.run()
  escape/q       → pop_screen / quit

Agent screen → demo: d / "demo [a|b]" → action_open_demo(name) → push AgentDemoScreen(controller, name)
```

> **Dual-path fix:** `action_open_*()` pushes Textual screen AND calls `controller.show_*()` (wiring). Fixed TUI navigation freeze.

---

# SECTION:AGENT_CYCLE — Agent Cycle (Agent.run_cycle) (grep:AGENT_CYCLE_)

```
perceive()          ── PERCEIVING
  └─ for each enabled sensor: sensor.sense() → SensorReading
       store in volatile memory {"sensor": sid, "data": ...}
       environment_model = readings → confidence = mean(confidences)

decide()            ── DECIDING
  └─ ctx = PolicyContext(environment, memory(recent), active_goal, state, autonomy)
       PolicyEngine.evaluate(ctx) → PolicyDecision(selected_action, confidence, reasoning)
  command = _decision_to_command(decision)  # EXECUTE_TOOL → ActuatorCommand
       tool_id = params["tool_id"]; action = params["action"]; parameters = rest

act(command)        ── ACTING
  └─ ToolRegistry.execute_safely(command) → ActuatorResult
       store action result in memory {"actuator", "action", "success", "error"}
       if success AND active goal's success_criteria matches → complete goal

reflect(trace, ctx) ── REFLECTING (only if AI service wired, N11)
  └─ ReflectionEngine.reflect() → ReflectionEntry(critique + proposals)
       persist ReflectionEntry (refl_repo)
       proposals stay PENDING until approved (N4)

state → PERCEIVING
return CycleResult(perception, decision, action_result, reflection)
```

**Invariants:**
- Single command built once (N2) — executed & traced action share `correlation_id`
- Goal completion scoped by `SuccessCriteria.tool_id` (C6): only matching tool satisfies
- Reflection skipped without AI service (N11)

---

# SECTION:DEMO — Demo Flow (feature_010) (grep:DEMO_)

```
AgentTUIScreen: d / "demo [a|b]"
  └─ action_open_demo(name) → push AgentDemoScreen(controller, name)

AgentDemoScreen.on_mount()
  └─ controller.load_demo_scenario_by_name(name)
       ├─ agent.clear_state()  # clear goals/rules/volatile memory
       ├─ seed_sandbox_files(scenario, sandbox_root)  # write target.txt/notes.txt
       ├─ controller.submit_goal(...)  # scenario goal (ACTIVE)
       └─ controller.update_policy(...)  # scenario rules
  └─ refresh (render summary + status)
  └─ action_run_cycle()  # auto-run 1 cycle, narrate

Run Cycle (r)   → controller.run_cycle() → render decide/act/reflect in log
Reset (x)       → controller.load_demo_scenario_by_name(current)  # clear + re-seed
Back (Escape)   → app.pop_screen() → back to AgentTUIScreen
```

**Scenario A (File Reader):** `goal.active → filesystem read target.txt` → goal completes in 1 cycle
**Scenario B (Knowledge Assistant):**
- Cycle 1: `goal.active → read notes.txt` (goal completes)
- Cycle 2: `memory_contains("notes.txt") AND NOT memory_contains("summary.txt") → create summary.txt`
- Cycle 3: `summary.txt` in perception → rule 2 condition false → idle

---

# SECTION:CHAT — Chat Flow (Streaming) (grep:CHAT_)

```
User types message
  └─ ChatTUIScreen → ChatController.process_user_message(msg)
       ├─ append HumanMessage to history
       ├─ for chunk in get_streaming_response(llm, history):
       │     view.show_partial_message(chunk)  # stream into growing widget
       ├─ append AIMessage to history
       └─ view.show_stream_message(final)
  └─ repeat until quit/exit (Escape pops back to Main)
```

`ChatController` builds `AIService().openrouter_llm_provider().create_llm()` in ctor. `_extract_chunk_content` handles list/None chunk content.

---

# SECTION:RAG_INGEST — RAG Ingestion Flow (grep:RAG_INGEST_)

```
RagTUIScreen: Ingest / "i"
  └─ RagWebIngestionController → InputUrlController (URL) + InputOptionsController (level)
       └─ Rag.web_ingestion(extract_level: Low|Mid|High)
            ├─ RagDatabase.insert_ingestion_entry(info)  # rag.db
            ├─ vectorstore = AIService.rag_chromadb(directory)
            ├─ WebExtract(max_depth, max_breadth, max_pages)  # TavilyMap + TavilyExtract
            ├─ WebIngestionApp.run(site_url, jsonl_path)
            │     ├─ data_ingestion()    # crawl map
            │     ├─ save_docs()         # JSONL
            │     ├─ process_documents() # RecursiveCharacterTextSplitter(4000, 200)
            │     └─ index_documents_async()  # concurrent aadd_documents → Chroma
            └─ return True/False
```

---

# SECTION:RAG_QUERY — RAG Query Flow (grep:RAG_QUERY_)

```
RagTUIScreen: question input
  └─ RagChatController → Rag.query(prompt, history: RagChatHistory)
       └─ RagQuery.ask(prompt, history)
            ├─ retriever = create_history_aware_retriever(llm, vectorstore.as_retriever(), prompt)
            ├─ chain = create_retrieval_chain(
            │           create_history_aware_retriever(...),
            │           create_stuff_documents_chain(llm, RagChatPrompts.create_rag_template())
            │         )
            ├─ result = chain.invoke({"input": prompt, "chat_history": history})
            ├─ append answer + sources
            └─ return RagChatHistory (answers + prompts + chat history)
```

---

# SECTION:SESSION — Session Lifecycle (grep:SESSION_)

```
no session (default "current" under local_sessions/)
  └─ "new [name]" → NewSessionCommand
       └─ SessionManager.create_new_session()
            ├─ backup current → current_backup_<timestamp>
            └─ create timestamped dir + init SessionDatabase (session.db)

each run_command:
  └─ session_controller.insert_history_entry(key)  # recorded in session.db history table
```

Sessions = working dir root. RAG repos under `<session>/rag/`. Agent persistence (`agent_session.db`) in session dir (or `.` if no session).

---

# SECTION:PERSISTENCE_FLOW — Agent Persistence Flow (grep:PERSISTENCE_FLOW_)

## 9. Agent Persistence

```
Agent.persist()                  ── PERSISTING
  └─ SessionSnapshot(snapshot_id, agent_id, config_version,
       volatility_data = {state, config (N7), volatile_memory (N1)},
       policy_store = [rules],
       goal_tree = {root},
       reflection_log_position = len(log))
  └─ SessionDatabase.save_snapshot_with_retry(snapshot)
  └─ state → PERCEIVING

Agent.resume_session(snapshot_id)  ── REBUILD
  └─ clear pre-existing in-memory state (N9)
     restore config (N7), policy (repo-first, N3), goal tree (honour root, N8),
     volatile memory (N1), reflection log (M2), re-register tools (C1)
     state → PERCEIVING
     (AI service non-serialisable — caller re-injects via set_ai_service, C3)
```

`AgentAdapter.create_agent(resume=True)` resumes latest snapshot on open (C5/I1).