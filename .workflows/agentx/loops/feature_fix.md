An agentx feature does not work as expected (the **fix** branch) OR was implemented and the implementation must be reviewed completely before any fix is applied (the **review** branch). In both cases the loop stops at the approval gate and applies a fix only after the user explicitly picks one alternative. The trigger picks the branch:

- Trigger says the feature is *broken / wrong / doesn't work* → **fix branch** (steps 1–2 then 3fix).
- Trigger says the feature *works but should be reviewed / audited / verified* → **review branch** (steps 1–2 then 3review).

# Rules

1. Follow omt methodology (declare `omt_phase` before any `src/` edit; consult `omt_kb_nav` before `src/` edits; `omt_think{op:list}` consult on TA-carrying files).
2. Use `omt_think` everywhere a feature exists in source — read existing thoughts with `op: list`/`op: suggest` BEFORE proposing changes, and add new findings with `op: add` AFTER applying a fix.
3. Create automated unit tests (with mocks) whenever a behavior can be verified mechanically; prefer a failing test that pins the bug before the fix, then a passing test after.
4. Use sub-agents (opencode `task` tool) for parallel analysis whenever the work fans out — dispatch them in a single message, never serially.
5. Minimize future agent token consumption: prefer `omt_nav`/`omt_kb_nav` over grep/glob for docs, prefer read-only `omt_q` over scanning the ledger by hand, and do NOT re-derive state the harness already exposes.

# Fix & review strategy

> Use `todowrite` to track steps 1–6 as you walk the loop (one in_progress at a time). Update statuses in real time so the user sees progress.

1. **Read the feature documentation and the current implementation in parallel.**
   - Dispatch in one message:
     - `omt_nav{op:nav, query:"«feature slug»"}` + `omt_kb_nav{op:nav, query:"CLASS_|CONTRACT_|DEP_"}` for arch/contract context;
     - `task(explore, subagent_type:"explore", "Find the feature's design artifacts under 4.design/features/«feature slug»/ and the FEATURE.md / requirements doc, return their paths and a one-paragraph summary of each")` ;
     - `read` of the feature's primary source file(s) once the subagent returns paths.
   - Do NOT glob/scan the whole repo — that is the most expensive discovery path.

2. **Find gaps between the feature's core idea vs the current implementation.**
   - Use `omt_q{op:drift}` as the first pass — it returns, against a pinned commit, the cross-ledger view of phase decrees / skip reasons / tdd position / known suite failures. Many "the feature is wrong" cases are *already drifted* in the ledger and `drift` surfaces that in one call.
   - Use `omt_think{op:list, path:"«primary src file»"}` + `omt_think{op:suggest, path:«src», top:5}` to read what past sessions already flagged on the source — do not re-derive findings a thought already recorded.
   - Optionally fan out: `task(explore)` per subsystem (e.g. one subagent per UI/controller/service layer) if the feature spans >3 files; merge their findings yourself.

3. **Branch by trigger.** Read the trigger again:

   - **3fix** (trigger = broken/wrong) — Identify the issues and propose fix alternatives. Each alternative states: what to change, which `src/` files, which failing test pins the bug, and the rollback note.

   - **3review** (trigger = review/audit) — Verify the implementation against the design intent, section by section. For each section, classify as *matches intent* / *partial* / *drift*, and propose a corrective alternative only when drift is found. A review that finds no drift documents that fact and stops — there is no obligation to invent a fix.

   Either branch writes its output to `./sandbox/feature_<NNN>_<FIX_BRIEF_DESCRIPTION>.md` (the **flat** output pattern — single document per invocation). Both branches land in the same file shape so a later session resumes either one identically.

4. **Approval gate — STOP.** Present the alternatives drafted in step 3 to the user via the `question` tool (structured picker), one question with one option per alternative plus a "Type your own" line. Do NOT call `edit`/`write` to source, do NOT commit, until the user has explicitly picked one alternative. This step is non-negotiable per `.workflows/META.md` §4.3.

5. **Execute the chosen alternative.** Declare `omt_phase{task_type:"bug_fix"|"minor_feature"|"refactor"|"test", scope:"«one sentence»"}` before any `src/` edit (or `omt_tdd` red→green→refactor→done for `major_feature`/`new_screen`, which auto-activates). Apply the change. Add an `omt_think{op:add, ...}` note at the anchor that documents *why* the fix matches the feature's intent (category: `why` or `xref` to the feature design doc).

6. **Update the results in the same file as step 3** (`./sandbox/feature_<NNN>_<FIX_BRIEF_DESCRIPTION>.md`) — append a `# Result` section: what was done, which artifacts/files changed, which tests were added/turned green, and what is left to resume. This is the resumption contract; a later session reads only this sandbox file to continue.

# Result (optional — filled in after execution)

<!-- what was done, what artifacts were created/changed, what is left to resume — enables later-session resume -->
