The agentx feature do not work as expected, the implementation must be inspected and then be fixed.

# Rules
1. Follow omt methodology
2. Use omt think everywhere omt feature to put knowledge in the source code itself
3. Create automated unit test whenever is possible to verify if part of the implementation is wrong, use mocks
4. Try to use sub agents for parallel analysis whenever is possible and useful

# Fix strategy
1. Read the feature documentation: requirements, analysis and design artifacts
2. Understand the current implementation and try to find gaps between the core idea of the feature versus the current implementation
3. Identify the issues if it exits, and propose fix alternatives in a new document or update one document in ./sandbox/feature_<NNN>_<FIX_BRIEF_DESCRIPTION>.md
4. Ask the user what alternatives have to perform the fix
5. Execute the fix alternative chosen by the user
6. Update the results in the same file of step 3, ./sandbox/feature_<NNN>_<FIX_BRIEF_DESCRIPTION>.md
