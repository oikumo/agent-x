# Testing Sandbox - Agent X

> **Purpose**: TDD strategy for AI-assisted development  
> **Style**: Kent Beck's Test-Driven Development  
> **Target**: AI agents (opencode) working on Agent-X
> **MANDATORY** NEVER CALL CLOUD LLM MODEL, ALWAYS USE MOCKS STRATEGY

---

## Core Philosophy

> "The first step is to write a test that fails. This seems trivial, but it's the hardest step for most people."  
> — Kent Beck, *Test Driven Development: By Example*

TDD is not about testing. It's about **design**, **confidence**, and **incremental progress**.

---

## The Three Laws of TDD

1. **You may not write production code until you have written a failing test**
2. **You may not write more of a test than is sufficient to fail** (not compiling = failing)
3. **You may not write more production code than is sufficient to pass the one failing test**

---

## The Red-Green-Refactor Cycle

```
RED → Write a small test that fails
  ↓
GREEN → Make it pass as quickly as possible (even if ugly)
  ↓
REFACTOR → Clean up both test and production code
  ↓
REPEAT
```

### RED Phase Rules
- Write the **smallest possible test** that expresses one behavior
- Test should fail for the **right reason** (not a typo or setup error)
- Name tests after the **behavior** they verify, not the method
- Use `unittest.TestCase` framework in `.tests_sandbox/`

### GREEN Phase Rules
- Make the test pass **as fast as possible**
- No design thinking during GREEN - just make it work
- **Fake it** until you make it (return constants, then generalize)
- **Triangulate** with multiple tests before adding real logic

### REFACTOR Phase Rules
- Clean up **duplicates** in both test and production code
- Improve names, extract methods, simplify conditionals
- **Never change behavior** during refactoring
- Run tests after each small refactoring step

---

## Kent Beck's TDD Patterns

### Fake It ('Til You Make It)
```python
# RED
def test_sum_two_numbers(self):
    result = self.command.run(["2", "3"])
    self.assertEqual(result._message, "5")

# GREEN - Fake it
def run(self, arguments):
    return CommandResultPrint("5")

# GREEN - Triangulate with another test
def test_sum_different_numbers(self):
    result = self.command.run(["10", "20"])
    self.assertEqual(result._message, "30")

# GREEN - Now implement properly
def run(self, arguments):
    a, b = int(arguments[0]), int(arguments[1])
    return CommandResultPrint(str(a + b))
```

### Obvious Implementation
When the implementation is obvious, skip faking and write it directly. Use judgment.

### Triangulation
Write multiple tests with different values before generalizing. Forces you to prove the pattern.

### One Assert Per Concept
One assertion per test is ideal, but assert related aspects of the **same concept** together.

---

## AI Agent TDD Workflow

### Before Writing Code
1. **Understand the requirement** - What behavior is needed?
2. **Identify the smallest slice** - What's the simplest test to write first?
3. **Check existing tests** - Don't duplicate, build on them

### During Development
```
1. Write failing test in tests_sandbox/
2. Run test → RED (verify it fails)
3. Write minimal code to pass
4. Run test → GREEN
5. Refactor (remove duplication, improve names)
6. Run all tests → Still GREEN
7. Repeat with next behavior
```

### Test Naming Convention
```python
# Good - describes behavior
def test_sum_valid_numbers_returns_result(self):
def test_sum_invalid_args_returns_none(self):
def test_sum_missing_args_returns_none(self):

# Bad - describes implementation
def test_sum_method(self):
def test_run_function(self):
```

---

## tests_sandbox/ Structure Strategy

```
.tests_sandbox/
├── META.md           # This file - rules and strategy
├── features/                  # Feature-level integration tests
│   └── test_<feature>.py      # Tests for a specific feature
├── test_<module>.py           # Module-level unit tests
└── __init__.py
```

### When to Use Which Level
| Level | Purpose | Example |
|-------|---------|---------|
| `test_<module>.py` | Unit tests for single module | `test_command_parser.py` |
| `features/test_<feature>.py` | Cross-module behavior | `test_controller.py` |

---

## Kent Beck's Test Design Principles

### Test State, Not Methods
Test what the system **does**, not how it does it.

### Test Behavior, Not Implementation
Tests should survive refactoring. If a test breaks during refactoring, it's testing implementation.

### One Behavior Per Test
Each test verifies **one thing**. If you need "and" in the test name, split it.

### Tests as Documentation
Tests should tell the story of the system. Read tests to understand what the code does.

### Arrange-Act-Assert Pattern
```python
def test_help_returns_command_list(self):
    # Arrange
    mock_cmd = MagicMock()
    mock_cmd.key = "test"
    mock_cmd.description = "Test command"
    self.controller.get_commands.return_value = [mock_cmd]

    # Act
    result = self.command.run([])

    # Assert
    self.assertIsNotNone(result)
```

---

## Rules for AI Agents

### DO
- Write the **simplest failing test first**
- Run tests **frequently** (after every change)
- Commit only when **all tests pass**
- Use `unittest.TestCase` in `.tests_sandbox/`
- Keep tests **independent** and **isolated**
- Name tests after **user-visible behavior**

### DON'T
- Write production code without a failing test
- Write multiple tests at once before implementing
- Skip the RED phase
- Test private methods directly
- Use tests as an afterthought
- Leave failing tests in the codebase

### When Stuck
1. Write a **simpler test** - what's the smallest case?
2. **Fake the implementation** - return a constant
3. **Triangulate** - add another test with different values
4. **Refactor** - maybe the design is wrong, simplify it

---

## Running Tests

```bash
# Run all sandbox tests
uv run pytest .tests_sandbox/ -v

# Run specific test file
uv run pytest .tests_sandbox/test_command_parser.py -v

# Run specific test class
uv run pytest .tests_sandbox/test_commands.py::TestSumCommand -v

# Run specific test method
uv run pytest .tests_sandbox/test_commands.py::TestSumCommand::test_sum_valid_numbers -v

# Run tests matching pattern
uv run pytest .tests_sandbox/ -k "sum" -v
```

---

## Progression Example: Building a Command

```python
# Step 1: RED - Test existence
def test_command_has_key(self):
    cmd = NewCommand("new", self.controller)
    self.assertEqual(cmd.key, "new")

# Step 2: GREEN - Minimal class
class NewCommand(Command):
    def __init__(self, key, controller):
        super().__init__(key, controller)

# Step 3: RED - Test description
def test_command_has_description(self):
    cmd = NewCommand("new", self.controller)
    self.assertIn("New", cmd.description)

# Step 4: GREEN - Add description
def __init__(self, key, controller):
    super().__init__(key, controller, description="New feature")

# Step 5: RED - Test behavior
def test_run_returns_result(self):
    cmd = NewCommand("new", self.controller)
    result = cmd.run([])
    self.assertIsInstance(result, CommandResult)

# Step 6: GREEN - Implement behavior
def run(self, arguments):
    return CommandResultPrint("Done")

# Step 7: REFACTOR - Improve names, extract methods
# Step 8: Repeat with next behavior
```

---