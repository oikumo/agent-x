The META HARNESS must help to the human user to mechanize to the coding agent opencode software development  
following a clear path, guided by rules and constraint that allow to improve the process performance during the development 
tasks execution. Must evolve, gathering knowledge and improving the META HARNESS and the source code itself.

The META HARNESS current state has features and characteristics that force the coding agent to follow a methodology
to develop software, but always can be improved, so the improvements must be found by you. The improvement strategy is bellow.

# Improvement strategy rules
1. Do not consider previous iterations history, make each improvement loop iteration with a fresh start
2. Focus in future coding agent token consumption minimization usage
2. The main goal is to improve the coding agent performance, not human-readable artifacts, suggest the creation of a DSL for META HARNESS whenever is possible
3. Any possible refactor opportunities must be considered when it is found
4. Focus on META HARNESS flexibility for future changes

# Improvement strategy
1. Understand deeply what is META HARNESS using the META HARNESS artifacts available **DO NOT SEARCH THE SOURCE CODE**
2. Understand the current structure and behavior of META HARNESS in the whole workspace **USING META HARNESS TOOLBOX** 
3. Summarize your current knowledge about the META HARNESS state in a temporary file in the ./sandbox/meta/improvement<ID>/CURRENT_STATE.md
4. Create a list of all the possible improvement in a file ./sandbox/meta/improvement<ID>/IMPROVEMENT_OPTIONS.md
5. Ask the user to select one of the options in ./sandbox/meta/improvement<ID>/IMPROVEMENT_OPTIONS.md
6. Execute the improvement options selected by the user and follow the execution path mandated for him
7. Update only the ./meta/META_HARNESS.md file with the META HARNESS new state