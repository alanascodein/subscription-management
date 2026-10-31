Create a Markdown file named `TEAM_CHANGELOG.md` in the root of the existing project to track changes made by teammates and coding agents.

## Objective

My team works independently using separate Git branches and does not use agent-to-agent communication. I need a reliable way for my coding agent to identify changes made by teammates, understand their purpose, and integrate with their work without overwriting existing implementations.

## 1. Inspect the Repository First

Before creating the file:

- Inspect the Git repository and its branch structure.
- Check the existing `AGENTS.md`, `TASKS.md`, and `API_CONTRACT.md` files if they exist.
- Examine recent Git commits and the current working-tree status.
- Do not modify application code or existing commits.
- Do not assume that every commit belongs to a different teammate.

## 2. Create TEAM_CHANGELOG.md

Include these sections:

### Project Information
- Repository name
- Current branch
- Last updated timestamp

### Recent Teammate Changes

For each relevant change, record:

- Contributor name or Git author
- Commit hash
- Commit message
- Branch name, if known
- Date and time
- Files added
- Files modified
- Files deleted
- Summary of the changes
- Purpose of the changes
- Dependencies or prerequisites
- API endpoints, database models, shared interfaces, or configuration affected
- Tests performed and their results
- Known issues or incomplete work
- Potential integration conflicts
- Integration status: Pending, Reviewed, Integrated, or Blocked

### Important Changes for Other Agents

Summarize the information another coding agent needs before starting work:

- New functions, components, modules, or services
- Changed function signatures or interfaces
- New dependencies
- Database schema changes
- API contract changes
- Environment variables introduced
- Files that other agents should avoid modifying
- Outstanding integration requirements

### Pending Integration Tasks

List changes that exist on teammate branches but have not yet been integrated into the current branch, provided this can be verified.

For each item, record:
- Branch
- Commit hash
- Summary
- Dependencies
- Recommended next action

### Current Integration State

Record:
- Current branch
- Latest known commit
- Whether the working tree has uncommitted changes
- Known merge conflicts
- Outstanding tests
- Next recommended action

## 3. Record Changes Automatically Through Git Inspection

Do not rely solely on manually written descriptions.

Use Git commands to inspect commits and file changes, including:

- `git status`
- `git log`
- `git show --stat`
- `git diff`

Compare relevant branches where appropriate.

Distinguish between:
1. Changes committed on the current branch.
2. Changes committed on other locally available branches.
3. Changes already merged into the current branch.
4. Changes that exist remotely but have not been fetched.
5. Uncommitted local changes.

Do not claim to have inspected remote branches unless their information is available locally or has been fetched.

If a remote branch has not been fetched, record that its latest state is unknown rather than inventing information.

Do not treat a commit as integrated merely because it exists in the repository. Verify its relationship to the current branch.

## 4. Update the Changelog After Every Task

After implementing a task, update `TEAM_CHANGELOG.md` with:

- What you changed
- Why you changed it
- Which files you modified
- The commit hash, if committed
- Tests performed and their results
- Any new dependencies or interfaces
- Integration requirements for teammates
- Any unfinished work

Do not fabricate commit hashes, test results, contributor identities, or timestamps.

If the task has not been committed, explicitly state that the changes are uncommitted.

## 5. Instructions for the Next Coding Agent

Add a section at the top of the file containing this workflow:

Before making any code changes:

1. Read `AGENTS.md`, `TASKS.md`, `API_CONTRACT.md`, and `TEAM_CHANGELOG.md` when present.
2. Inspect `git status` to identify uncommitted changes.
3. Inspect recent commits and the current branch.
4. Review the changelog for changes that affect your assigned task.
5. Verify whether relevant teammate branches are available locally or remotely.
6. Inspect actual code before relying on a changelog description.
7. Avoid overwriting teammates' work.
8. Follow the existing API contracts and architecture.
9. If required changes are missing, document the dependency instead of guessing.
10. Update `TEAM_CHANGELOG.md` when your task is completed.

## 6. Safety Rules

- Do not reset, clean, or discard another person's changes.
- Do not amend, rewrite, or force-push existing commits.
- Do not automatically merge teammate branches.
- Do not check out another branch if doing so would risk losing uncommitted work.
- Do not commit secrets, `.env` files, credentials, or generated virtual environments.
- Do not change application code just to generate the changelog.
- Preserve existing changelog history instead of replacing it on every run.
- Avoid recording the same commit repeatedly.
- Never claim that a teammate's changes are integrated until verified.

## 7. GitHub Synchronization

The changelog must be committed and pushed to the team's shared repository so other agents can access it.

However, do not push automatically unless explicitly authorized.

Explain how the team should commit and push the changelog and how another agent can retrieve it.

Remember that each Git branch has its own copy of the Markdown file. Changes made on one branch will not automatically appear on another branch until the relevant commit is shared and retrieved.

## 8. Final Output

After implementing this:

1. Show the location of `TEAM_CHANGELOG.md`.
2. Summarize its sections.
3. Explain which Git information was actually inspected.
4. List any limitations, including inaccessible remote branches.
5. Provide the commands needed to commit and push the file.
6. Do not claim automatic background monitoring. The file is updated when the workflow runs.