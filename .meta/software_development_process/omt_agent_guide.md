# OMT++ Agent Guide v2.0 (compressed)

> **Purpose:** Complete OMT++ methodology for coding agents. Every rule actionable. No exceptions.
> **Target:** AI coding agents | **Based on:** OMT++ v2.0

---

## 1. OMT++ Mindset (6 Principles)

| # | Principle | Agent Meaning |
|---|-----------|---------------|
| 1 | Practical over theoretical | Write working code. Skip patterns adding complexity without value. |
| 2 | Adaptable | Bug fix ≠ new feature ≠ new project. Adjust approach per task. |
| 3 | Complete coverage | Full cycle: understand → design → implement → test. Never skip to coding. |
| 4 | Visible artifacts | Every phase produces tangible output (use case, diagram, test plan). Not bureaucracy — deliverables. |
| 5 | Controlled process | Plan → execute in phases → verify. No rushing, no half-done work. |
| 6 | Architecture first | Good architecture enables late changes. Bad architecture = endless fixes. |

**First thought on any request:** *"Which OMT++ phase am I in?"*
- Vague/conceptual → **Analysis** (clarify, write use cases)
- Clear feature → **Design** (plan architecture, interfaces)
- Implementation task → **Programming** (verify design exists first)
- Fix/verification → **Testing** (reproduce, isolate, fix, verify)

---

## 2. Phase Model (A → D → P → T)

```
Feasibility (Pre-Phase): Go/no-go, effort estimate, preliminary design
         │
         ▼
ANALYSIS: WHAT problem? WHAT users need? → Use cases, analysis class diagram, UI spec
         │
         ▼
DESIGN:   HOW to implement? → Component diagram, design class diagram, sequence diagrams
         │
         ▼
PROGRAMMING: Write code → Classes, methods, unit tests
         │
         ▼
TESTING:  Does it work? → Test reports, defect logs, verified system
```

### Phase Rules (Absolute)
1. **Identify phase explicitly** before acting: *"This puts me in Analysis — I need requirements first."*
2. **Iterate, never skip**: Missing requirement in Programming → back to Analysis. Design flaw in Testing → back to Design.
3. **Each phase produces visible artifact** — if nothing to show, you're not done.
4. **Phase products freeze at project end** (historical record). Only architecture doc + code maintained long-term.

### Valid Transitions
| Current | Valid Next | Invalid |
|---------|------------|---------|
| Analysis | Design (normal), Testing (prototyping only) | Programming (skip design = chaos) |
| Design | Programming, Analysis (gaps found) | Testing (no code yet) |
| Programming | Testing, Design (design fails), Analysis (reqs shift) | Done (must test first) |
| Testing | Analysis (reqs wrong), Design (design wrong), Programming (bug found) | Done (only when all tests pass) |

---

## 3. Two Parallel Paths (Static + Functional) — **Always Model Both**

```
STATIC (Structural)          FUNCTIONAL (Behavioral)
ANALYSIS:  Analysis class diag  │  ANALYSIS:  Use cases, operation specs
           Data dictionary       │
DESIGN:    Component diagram     │  DESIGN:    Sequence diagrams
           Design class diagram  │             Collaboration scenarios
PROGRAMMING: Class impl + files  │  PROGRAMMING: Method impl + control flow
TESTING:   Component/interface   │  TESTING:   Use case/workflow tests
```

**Why both:**
- Static alone = isolated code that doesn't connect
- Functional alone = messy structure, no ownership

**For every task:**
1. Sketch static structure (what components/classes/files)
2. Sketch functional flow (step-by-step interaction)
3. Then code

---

## 4. Feasibility Study (Pre-Phase, Mandatory)

**4 Questions:**
| Question | Action |
|----------|--------|
| 1. Understand requirements? | If no → ask user. Never guess. |
| 2. Scope clear? | One-sentence "done" definition? If no → unclear. |
| 3. Know codebase location? | Exact files to touch. If no → explore first. |
| 4. Risk level? | High = new feature/screen/data model. Low = bug fix/minor extension. |

**Output (state to user before coding):**
```
Feasibility:
- Phase: Design (clear feature)
- Files affected: main_controller.py, commands.py
- Risk: Low (adds one command, no new screens)
- Effort: ~15 min impl, ~15 min test
```

**When to say "No/Not Yet":**
| Situation | Response |
|-----------|----------|
| Vague requirements | "Need to clarify X before designing. Tell me more about..." |
| Scope too large | "Touches multiple screens + new data model. Split into increments." |
| Missing deps | "Need to know how X works before Y. Researching first." |
| Effort underestimated | "This is 3+ hours. Outlining plan first." |

---

## 5. Core Architecture: MVC++ (Absolute Layer Rules)

```
CONTROLLER: App logic, orchestration, dispatch | Knows: View+Model | Seen by: View(Partner)
VIEW:       UI render, input capture           | Knows: Controller(Partner only)
MODEL:      Domain logic, biz rules, data      | Knows: nothing about UI
```

| What | Controller | View | Model |
|------|-----------|------|-------|
| Imports Model? | ✅ | ❌ Never | N/A |
| Imports View? | ✅ | N/A | ❌ Never |
| Imports Controller? | N/A | ❌ Partner only | ❌ Never |
| Contains UI code? | ❌ Never | ✅ | ❌ Never |
| Contains biz logic? | ✅ Orchestration | ❌ Never | ✅ Core |
| Contains SQL? | ❌ Never | ❌ Never | ✅ DP classes only |
| Lifecycle | Creates View + accesses Model | Exists only when controller creates it | UI-independent |

### File Naming
```
<layer>/<screen>/<screen>_<layer>.py
ui/screens/main/main_controller.py
ui/screens/main/main_view.py
model/session/session.py          # model omits suffix
```

### Anti-Patterns (Never Do)
| Anti-pattern | Violation |
|--------------|-----------|
| Fat View with logic | View = untestable |
| Anemic Model (getters/setters only) | Model must have domain logic |
| Controller with SQL | Use DP classes |
| View creates Controller | Constructor injection only |
| Model references View | Circular dependency |

---

## 6. Abstract Partner Pattern (Only View↔Controller Contract)

### Contract (ABC — never plain class)
```python
from abc import ABC, abstractmethod

class IScreenPartner(ABC):
    @abstractmethod
    def on_user_input(self, user_input: str) -> None: ...
    @abstractmethod
    def get_prompt(self) -> str: ...
```

### Absolute Rules
1. **Always `ABC` + `@abstractmethod`** — no exceptions
2. **Name: `I*`** — `IMainViewPartner`, `IChatViewPartner`, `IRagViewPartner`
3. **Defined in View file** — top, before View class
4. **View receives partner in constructor** — never creates controller
5. **Controller implements interface** — `class MyController(IMyViewPartner)`
6. **Partner methods = complete API** — no back channels

### Wiring (Constructor Injection)
```python
# View file
class MyView:
    def __init__(self, partner: IMyViewPartner):
        self._partner = partner
        self._console = UIConsole(partner.get_prompt())
    def show(self):
        while True:
            inp = self._console.capture_input()
            self._partner.on_user_input(inp)

# Controller file
class MyController(IMyViewPartner):
    def __init__(self):
        self._view = MyView(self)  # Pass self as partner
    def on_user_input(self, user_input: str): ...
    def get_prompt(self) -> str: return "(my-screen)"
```

### Testing
```python
class MockPartner(IMyViewPartner):
    def on_user_input(self, inp): ...
    def get_prompt(self): return "(test)"

def test_view_delegates():
    partner = MockPartner()
    view = MyView(partner)
    # simulate input → partner.on_user_input invoked
```

### Common Mistakes
```
❌ class IMainViewPartner:          # no ABC
❌ class MainView(MainController):  # View inherits Controller
❌ def __init__(self): self.controller = MainController()  # View creates Controller
✅ class IMainViewPartner(ABC): ...  # ABC + @abstractmethod
✅ class MainView: def __init__(self, partner: IMainViewPartner): ...
```

---

## 7. Screen MVC Triad Rules

### New Screen Creation
1. Folder: `ui/screens/<screen_name>/`
2. Three files:
   - `<screen>_controller.py` — implements `I<Screen>ViewPartner`
   - `<screen>_view.py` — defines `I<Screen>View(ABC)` + `I<Screen>ViewPartner(ABC)`
   - `__init__.py`

### Screen Lifecycle
```
ParentController.show_child():
  1. child = ChildController()    # Create triad
  2. child.show()                 # Takes over REPL
  3. # User interacts...          # Child loop runs
  4. # User quits → return        # Parent resumes
```
- Sub-screens **don't** leak parent references
- Sub-screens **don't** need parent structure knowledge
- Parent resumes own loop on sub-screen exit

### Input Components (Mini MVC Triads)
```
ui/common/input/<input_type>/
  input_<input_type>_controller.py
  input_<input_type>_view.py
```
- Same Abstract Partner pattern
- Controller exposes public result property (`controller.url`, `controller.selected_option`)
- Parent creates input controller → `.show()` → reads result property

---

## 8. Command Pattern (Main Screen Only)

### Structure
```
ui/screens/main/commands/
  commands_base.py    # Command(ABC)
  commands.py         # Concrete commands
  commands_parser.py  # CommandParser + CommandData
```

### Command ABC
```python
class Command(ABC):
    def __init__(self, key: str, controller: "MainController"):
        self.key = key
        self._controller = controller
    @abstractmethod
    def run(self, arguments: str) -> None: ...
```

### Rules
- One class per command in `commands.py`
- Constructor: `(key: str, controller: MainController)`
- `run()` executes operation — may create sub-screens (Chat, RAG)
- Registered in `MainController.load_commands()`
- Commands **don't** call View directly — call Controller, which calls View

### Flow
```
Input → CommandParser.parse() → CommandData(key, args)
  → MainController.run_command()
    → Look up command by key in dict
    → command.run(arguments)
```

### Command vs Screen
| Scenario | Action |
|----------|--------|
| Keyword → response | New `Command` class |
| Keyword → new interface | New `Command` + new `Screen MVC triad` |
| Keyword → modifies data | New `Command` + new `Operation` in Model |
| Keyword → shows list | New `Command` + existing View methods |

---

## 9. Model Layer Patterns

### Persistent Objects (Standard CRUD)
```python
class Session:
    def __init__(self):
        self.oid: int = None      # Unique across all instances
        self.name: str = ""
        self.directory: str = ""
    def create(self) -> bool: ...     # INSERT
    def load(self, oid: int) -> "Session": ...  # SELECT by OID
    def update(self) -> bool: ...     # UPDATE
    def delete(self) -> bool: ...     # DELETE
```

### Database Partner (DP) Pattern — **All SQL in DP Classes**
| File | Contains |
|------|----------|
| `model/session/session_db.py` | `DP_Session` — all session CRUD |
| `model/rag/rag_db.py` | `DP_Rag` — all RAG CRUD |

```python
class DP_Session:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
    def insert(self, session: Session) -> int:
        cur = self.conn.execute("INSERT INTO sessions (name, directory) VALUES (?, ?)",
                                 (session.name, session.directory))
        return cur.lastrowid
    def load(self, oid: int) -> Session:
        row = self.conn.execute("SELECT oid, name, directory FROM sessions WHERE oid = ?", (oid,)).fetchone()
        if not row: raise ValueError(f"Session {oid} not found")
        s = Session(); s.oid, s.name, s.directory = row; return s
    def update(self, session: Session) -> None:
        self.conn.execute("UPDATE sessions SET name = ?, directory = ? WHERE oid = ?",
                          (session.name, session.directory, session.oid))
    def delete(self, oid: int) -> None:
        self.conn.execute("DELETE FROM sessions WHERE oid = ?", (oid,))
```

### Navigation via OID References
```python
class LibraryUser:
    def __init__(self):
        self.oid: int = None
        self.room_oid: int = None  # FK to Room
    def get_resides_in(self) -> Room:
        if self.room_oid: return Room.load(self.room_oid)
        return None
```

### SQLite ↔ Class Mapping
| OMT++ Concept | SQLite |
|---------------|--------|
| Class → Table | `CREATE TABLE session (oid INTEGER PRIMARY KEY, ...)` |
| Object → Row | One row per instance |
| Attribute → Column | One column per attribute |
| Association → FK | `resides_in INTEGER REFERENCES room(oid)` |
| Inheritance → 1 table | Single table, NULLable subclass columns |

### Collections
```python
class CommandHistory:
    def __init__(self): self.entries: list[HistoryEntry] = []
    def add(self, entry: HistoryEntry): self.entries.append(entry)
    def get_all(self) -> list[HistoryEntry]: return self.entries
```

---

## 10. Operation Specifications

Every public Controller method handling user operations needs this docstring:

```python
def send_message(self, recipient: str, message: str) -> bool:
    """
    Operation: Send a message to a recipient.

    Preconditions:
      - Message length <= 160 characters
      - Recipient exists in contact list

    Exceptions:
      - Message too long: trim or reject with error
      - Network unavailable: queue for later delivery
      - Unknown recipient: return error to user

    Postconditions:
      - Message stored in sent_messages table
      - Recipient receives message (async)
    """
```

### Rules
1. **Every** user-facing Controller method needs this
2. **Preconditions** — what must be true before start
3. **Exceptions** — everything that can go wrong + handling
4. **Postconditions** — guaranteed true after
5. Concise — one sentence per item

### Source
Extracted from Use Cases in Analysis:
```
Use Case: "Sending a Short Message"
  1. User writes message
  2. User adds signature
  3. User selects recipients
  4. User sends message

→ Operations:
  - write_message(content)
  - add_signature()
  - select_recipients(list)
  - send_message()
Each → Controller method with Operation Specification
```

---

## 11. Testing Strategy — Three Stages

### Stage 1: Unit/Component
| What | Details |
|------|---------|
| Who | You |
| What | One class, isolated |
| How | Mock Abstract Partner (Views), Mock DP (Models) |
| Coverage | >80% branches |

```python
class MockMainPartner(IMainViewPartner):
    def __init__(self): self.commands = []
    def on_user_input(self, inp): self.commands.append(inp)
    def get_prompt(self): return "(test)"

def test_view_captures_input():
    partner = MockMainPartner()
    view = MainView(partner)
    # simulate input...
    assert partner.commands == ["/help"]
```

### Stage 2: Integration
| What | Details |
|------|---------|
| Who | You |
| What | Component interactions |
| Scenarios | Controller+View (real View, mock Model), Controller+Model (real Model, mock View), DP+real SQLite (in-memory) |

```python
def test_command_execution():
    controller = MainController()
    view = MockView()
    controller.view = view
    controller.run_command("quit")
    assert view.was_closed()
```

### Stage 3: System
| What | Details |
|------|---------|
| Who | You |
| What | Full workflows vs Use Cases |
| Approach | Follow use case steps as test script |

```python
def test_sending_message_use_case():
    app.start()
    app.write_message("Hello")
    app.add_signature()
    app.select_recipient("John")
    app.send()
    assert app.confirmation_shown()
```

### Test Planning (Before Writing Tests)
```
Component Test Plan for "SendMessage":
  Normal:
    - Valid message → sent, confirmation shown
  Exceptions:
    - Empty message → error, no send attempted
    - No recipient → error shown
    - Network failure → queued, user notified
```

---

## 11.4 TDD Workflow (feature_016)

**Auto-activates for `major_feature` / `new_screen` in Programming phase.**

### Five-Tool Cycle (Mandatory Order)
```
omt_tdd{op: testlist → red → green → refactor → done}
  (plan)         (write        (write code   (improve code    (verify
                  failing       to pass        keeping tests     full suite)
                  test)         the test)      green)
```

| Tool | State | Hat | Action |
|------|-------|-----|--------|
| `omt_tdd{op:testlist}` | TESTLIST | — | List behaviors (test names) to implement |
| `omt_tdd{op:red}` | RED | test | Write ONE failing test in `tests/`. Gate verifies true RED (AST + pytest). |
| `omt_tdd{op:green}` | GREEN | code | Minimum `src/` code to pass test. |
| `omt_tdd{op:refactor}` | REFACTOR | code | Improve code. Tests must stay green. **Auto-revert if tests break.** |
| `omt_tdd{op:done}` | DONE | — | Full suite + checklist pass. Phase exit validated. |

### Two-Hats Gate (Mechanical Enforcement)
| State | `tests/` edits | `src/` edits |
|-------|----------------|--------------|
| RED | ✅ Allowed | ❌ Blocked |
| GREEN | ❌ Blocked | ✅ Allowed |
| REFACTOR | ❌ Blocked | ✅ Allowed (reverted if tests break) |

Wrong layer edit → gate tells you which hat to switch to.

### True-RED Verification
`omt_tdd{op:red}` runs pytest + AST analysis. Test must:
1. Import/reference target source module (inferred from test path)
2. Fail because behavior missing (not import error/typo)

### REFACTOR Auto-Revert
Gate snapshots file pre-edit. Post-edit runs tests. If any fail:
1. File **auto-reverted** to pre-edit state
2. Edit blocked: "REFACTOR broke tests — edit reverted"
3. Try different refactor approach

### Coverage Gap Analysis (on `omt_tdd{op:done}` / `omt_complete`)
`tdd_check.py validate-exit`:
- Finds all public methods in your `src/` modules
- Checks test coverage (AST-extracted test calls)
- Reports **coverage gaps** — public methods with no test calling them
- Reports **dangling reds** — tests declared RED but never GREEN
- Phase exit blocked until gaps filled or `omt_skip` override

### TDD CLI (`scripts/omt/tdd_check.py`)
```
uv run scripts/omt/tdd_check.py testlist --behaviors "..." --feature feature_NNN
uv run scripts/omt/tdd_check.py start --test-node tests/... --target-src src/... --feature feature_NNN
uv run scripts/omt/tdd_check.py green --test-node tests/... --feature feature_NNN
uv run scripts/omt/tdd_check.py refactor --test-node tests/... --feature feature_NNN
uv run scripts/omt/tdd_check.py done --feature feature_NNN
uv run scripts/omt/tdd_check.py gate --path <rel> --session <id>
uv run scripts/omt/tdd_check.py after-edit --path <rel> --session <id>
uv run scripts/omt/tdd_check.py status --session <id>
uv run scripts/omt/tdd_check.py validate-exit --feature feature_NNN
```

---

## 12. Essential vs. Optional — Artifact Decision Guide

| Artifact | Bug Fix | Minor Feature | Major Feature | New Screen | New Project |
|----------|---------|---------------|---------------|------------|-------------|
| Feasibility statement | ✅ Quick | ✅ Quick | ✅ Yes | ✅ Yes | ✅ Yes |
| Use case | ❌ | ❌ | ✅ Yes | ✅ Yes | ✅ Yes |
| Operation list | ❌ | ✅ Quick | ✅ Yes | ✅ Yes | ✅ Yes |
| Analysis class diagram | ❌ | ❌ | ✅ If new concepts | ✅ If new concepts | ✅ Yes |
| Dialog diagram | ❌ | ❌ | ❌ | ✅ Yes | ✅ Yes |
| Component diagram | ❌ | ❌ | ❌ | ✅ If new deps | ✅ Yes |
| Design class diagram | ❌ | ✅ Quick | ✅ Yes | ✅ Yes | ✅ Yes |
| Sequence diagram | ❌ | ❌ | ✅ Complex flows | ✅ Complex flows | ✅ Yes |
| Operation spec | ❌ | ✅ Quick | ✅ Yes | ✅ Yes | ✅ Yes |
| Unit tests | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Integration tests | ❌ | ✅ If new deps | ✅ Yes | ✅ Yes | ✅ Yes |
| System tests | ❌ | ❌ | ✅ Yes | ✅ Yes | ✅ Yes |

**Legend:** ✅ = produce | ❌ = safe to skip | "Quick" = 1-2 line summary

### Rule of Thumb
- **One existing file?** → Skip analysis, write tests
- **2-3 files?** → Quick operation list + design sketch
- **New files/screens?** → Full artifact set for that screen
- **New project/feature?** → Full methodology, all phases

---

## 13. Artifact Production Checklist (Every Task)

### Before Starting (Feasibility)
- [ ] Requirements understood (if not, asked user)
- [ ] Scope clear ("done" = one sentence)
- [ ] Exact files to touch identified
- [ ] Risk assessed (low/medium/high)
- [ ] Phase declared

### Analysis Phase
- [ ] Use case written (if new screen/major feature)
- [ ] Operations listed from use case
- [ ] Key domain concepts (classes) identified
- [ ] UI dialog structure specified (if UI changes)

### Design Phase
- [ ] Affected components/screens identified
- [ ] Interfaces defined (Abstract Partners)
- [ ] Class structures designed (classes, methods)
- [ ] Data persistence planned (if new entities)
- [ ] Operation specs written for new methods

### Programming Phase
- [ ] All Abstract Partners = `ABC`
- [ ] View receives partner via constructor injection
- [ ] View has zero Model knowledge
- [ ] Controller orchestrates View + Model
- [ ] SQL in DP classes only
- [ ] `*_controller.py`/`*_view.py` in correct directories

### Testing Phase
- [ ] Unit tests per new class (>80% coverage)
- [ ] Tests mock interface, not concrete class
- [ ] Integration tests for component interactions
- [ ] System tests mapped to use cases (if applicable)
- [ ] All tests pass

---

## 14. Quick Reference — Do/Don't

### Do
| Want to... | Do this |
|------------|---------|
| Route user command | Command Pattern (main screen only) |
| Display output | `self._view.print_something()` from controller |
| Read user input | View captures → `partner.on_user_input()` |
| Access database | `DP_*` class, never raw SQL in controller |
| Create new screen | Folder + 3 files (controller, view, ABC) |
| Pass data between screens | Controller reads sub-controller's public properties |
| Test UI | Mock Abstract Partner interface |
| Add new command | Class in `commands.py`, register in `load_commands()` |
| Persist object | `create/load/update/delete` + DP class |
| Model collection | Typed `list[...]` or `dict[str, ...]` |
| Navigate objects | OID references, not direct pointers |
| Start new feature | Identify phase first → produce phase artifacts |
| Handle vague reqs | Switch to Analysis, write use case, ask user |

### Never Do
| Never do this | Why |
|---------------|-----|
| Import Model in View | Violates MVC++ — View must not know Model |
| Import View in Model | Circular dependency, breaks reusability |
| Plain class as Abstract Partner | Must be `ABC` + `@abstractmethod` — no exceptions |
| Business logic in View | Makes logic untestable |
| UI code in Controller | Controller becomes untestable |
| SQL in Controller | Scatters persistence logic |
| Circular dependencies | Impossible to test/refactor |
| Skip a phase | Analysis→Design→Programming→Testing. Never jump idea→code. |
| Code without file structure knowledge | Explore first. Never write blindly. |
| Skip tests for new feature | Untested = broken. Tests not optional. |

---

## 15. File Tree Template

```
src/agentx/
├── main.py                          # Entry: MainController → run()
├── model/                           # MODEL — NO ui imports
│   ├── ai/                          #   LLM providers + facade
│   │   ├── service.py               #   AIService (facade/factory)
│   │   └── providers.py             #   LLMProvider ABC + impls
│   ├── rag/                         #   RAG domain logic
│   │   ├── rag.py                   #   Rag orchestrator
│   │   ├── rag_db.py                #   DP_Rag — all RAG SQL
│   │   ├── rag_provider.py          #   Repository listing
│   │   ├── rag_repository.py        #   RagRepository dataclass
│   │   └── query/                   #   Query engine
│   └── session/
│       ├── session.py               #   Session entity (CRUD)
│       ├── session_manager.py       #   Session manager (NOT "Controller")
│       └── session_db.py            #   DP_Session — all session SQL
├── ui/                              # VIEW + CONTROLLER
│   ├── common/
│   │   ├── ui_console.py            #   Terminal renderer
│   │   └── input/                   #   Mini MVC triads (reusable)
│   │       ├── text_list/           #     InputTextListController + View
│   │       ├── url_entry/           #     InputUrlController + View
│   │       ├── options/             #     InputOptionsController + View
│   │       └── create_folder/       #     InputCreateFolderController + View
│   └── screens/                     #   Screen MVC triads
│       ├── main/                    #   ── MAIN SCREEN ──
│       │   ├── main_controller.py   #     Implements IMainViewPartner
│       │   ├── main_view.py         #     IMainViewPartner(ABC) here
│       │   └── commands/            #     Command pattern
│       │       ├── commands_base.py #       Command ABC
│       │       ├── commands.py      #       Concrete commands
│       │       └── commands_parser.py
│       ├── chat/                    #   ── CHAT SCREEN ──
│       │   ├── chat_controller.py   #     Implements IChatViewPartner
│       │   └── chat_view.py         #     IChatViewPartner(ABC) here
│       └── rag/                     #   ── RAG SCREEN ──
│           ├── rag_controller.py
│           ├── rag_view.py
│           ├── rag_chat_controller.py
│           ├── rag_chat_view.py
│           ├── rag_web_ingestion_controller.py
│           ├── rag_web_ingestion_view.py
│           ├── rag_repository_selection_controller.py
│           └── rag_repostitory_selection_view.py
└── utils/                           # Cross-cutting
    ├── constants.py
    ├── utils.py
    └── utils_directories.py
```

---

## 16. Common Mistakes to Catch (grep Patterns)

| # | Mistake | Detect | Fix |
|---|---------|--------|-----|
| 1 | View imports Model | `grep -r "from.*model" ui/screens/*/view.py` | Move logic to Controller |
| 2 | Controller has UI code | `grep -r "console\|print" ui/screens/*/controller.py` | Move to View |
| 3 | Model imports UI | `grep -r "from.*ui" model/` | Invert dependency |
| 4 | Plain class Abstract Partner | Check `ABC` inheritance | Add `(ABC)`, `@abstractmethod` |
| 5 | SQL in Controller | `grep -r "execute\|SELECT\|INSERT\|UPDATE\|DELETE" ui/screens/*/controller.py` | Move to DP class |
| 6 | Circular screen refs | Child holds parent controller ref | Remove; use return value |
| 7 | God Controller (>300 lines) | `wc -l *controller.py` | Extract sub-controllers |
| 8 | Missing operation spec | Check public methods for pre/post docstring | Add specification |
| 9 | `*Controller` in model/ | `ls model/**/*controller*` | Rename to `*Manager`/`*Service` |
| 10 | View creates Controller | `grep -r "Controller()" ui/screens/*/view.py` | Must inject via constructor |
| 11 | Phase skipping | Idea → code without design? | Produce phase artifact first |
| 12 | No tests for new feature | `grep -r "test.*yournewclass" tests/` | Write unit + integration tests |

---

*End of OMT++ Agent Guide v2.0 — all rules here. No other reference needed.*