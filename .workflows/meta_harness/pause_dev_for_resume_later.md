Pause your current work in progress development properly to be resumed later in a new opencode session. You must at least update the WORK.md file task and other artifacts that can be resumed seamlessly.

# Rules
1. Do not follow the omt methodology, focus on session housekeeping
2. Use omt think everywhere omt feature to put knowledge in the source code itself
3. Create automated unit test whenever is possible to verify if part of the implementation is wrong, use mocks
4. Try to use sub agents for parallel analysis whenever is possible and useful
5. The pause is reversible and idempotent — re-running it on the same session state must produce the same resumption artifacts, not duplicate them

# Pause strategy
1. Read the current WORK.md and identify the in-progress task (marked `[~]`) and any of its subtasks that are in progress
2. Read any other in-progress artifacts the current task touches (sandbox files under `.sandbox/`, PROJECT.md, test reports) and list what is left to do
3. Write a resumption document in ./sandbox/pause_<YYYY-MM-DD>.md that records: the active task id + name, what was completed so far, what is the immediate next step, any blockers, and the paths of the artifacts a future session needs to read first
4. Ask the user to confirm the resumption document is accurate and whether anything else must be saved before pausing
5. Update WORK.md: mark the in-progress task as `[~]` paused (or `[!]` if blocked) with a one-line DONE-style pointer to the pause_<YYYY-MM-DD>.md file in the same indented row the task already occupies
6. Update the results in the same file of step 3, ./sandbox/pause_<YYYY-MM-DD>.md, recording that WORK.md was updated and the session is safe to close

# Result (optional)
«filled in after execution: a one-line "paused at <step>, resume by reading <pause file>" so a new opencode session can pick up»
