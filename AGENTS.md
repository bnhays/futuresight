# AGENTS.md

## Repository Instructions For Codex

These instructions apply to the entire repository.

## Planning And Approval

- Always create a specific implementation plan before making code or documentation changes.
- Ask the user for approval before beginning implementation.
- Do not begin editing files until the user has approved the plan.
- If the requested change is ambiguous, ask clarifying questions before planning.
- Ask questions about anything unclear or ambiguous before beginning implementation.

## Testing Policy

- Do not run tests, builds, linters, formatters, package installs, dev servers, or other verification commands.
- Instead, provide the exact commands the user can run themselves.
- If a change would normally require testing, clearly state which checks are recommended and why.
- Do not install dependencies or start local services unless the user explicitly asks for that in the current conversation.

## Implementation Style

- Keep changes scoped to the user's approved request.
- Prefer existing project patterns and technology choices.
- Avoid adding storage, validation, statistics, versioning, or other extra features unless the user explicitly asks for them.
- Summarize changed files and recommended manual verification steps when finished.
