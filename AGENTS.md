# Team Git Workflow and Push Rules

## 1. General Rules

1. `main` is the stable branch. Do not develop features directly on `main`.
2. Each developer should use a separate feature branch for independent work.
3. Team roles are flexible. No member is permanently restricted to frontend, backend, integration, testing, or documentation.
4. Before starting a task, check `TASKS.md`, `TEAM_CHANGELOG.md`, `API_CONTRACT.md`, and `AGENTS.md` when available.
5. Committing saves changes locally; pushing uploads commits to GitHub.
6. Push completed work at meaningful milestones rather than waiting until the entire project is finished.
7. Never overwrite another person's uncommitted changes.
8. Never force-push or rewrite shared commit history without explicit approval.
9. Never commit secrets, credentials, `.env` files, virtual environments, or unnecessary generated files.
10. Check the Git status before switching branches, merging, or pulling changes.

## 2. Flexible Task Assignment

Any team member may work on:
- Frontend components and UI.
- Backend APIs and business logic.
- Database models and migrations.
- Frontend/backend integration.
- Testing and debugging.
- Documentation and deployment.

Tasks should be assigned based on availability, skills, and project requirements.

Before beginning a task:
1. Check whether another person is already working on it.
2. Identify the files and modules that will be affected.
3. Review existing interfaces and API contracts.
4. Record the task owner and status in `TASKS.md`.
5. Avoid modifying files currently being changed by another teammate unless the work is coordinated through the shared task and Git workflow.

Task ownership is temporary and applies only to the assigned work. It does not permanently restrict anyone from working in that area.

## 3. Before Starting Any Task

Run:

    git status
    git fetch origin
    git switch main
    git pull origin main

Create a feature branch:

    git switch -c feature/short-task-name

If the branch already exists, switch to it rather than creating it again.

Before coding:
- Read the relevant project instructions.
- Inspect the existing implementation.
- Check the API contract and changelog.
- Understand dependencies on other features.
- Confirm which files you intend to modify.

Do not assume another AI agent's private conversation or memory is available.

## 4. Implementation Rules

Every developer and coding agent must:
- Follow the existing project architecture and coding conventions.
- Implement only the assigned task and necessary supporting changes.
- Avoid rewriting unrelated code.
- Preserve existing functionality.
- Validate user input appropriately.
- Follow agreed API endpoints and request/response formats.
- Document proposed API or database changes.
- Avoid introducing unnecessary dependencies.
- Run relevant tests before declaring the task complete.

If a dependency or interface is missing, record the blocker in `TASKS.md` or a GitHub Issue rather than inventing an incompatible implementation.

## 5. When to Commit

Commit after completing a meaningful unit of work, such as:
- A functional component or page.
- An API endpoint.
- A database change.
- A bug fix.
- A group of tests.
- A documentation update.

Use descriptive commit messages.

Examples:

    git add <specific-files>
    git commit -m "Add subscription creation form"

    git add <specific-files>
    git commit -m "Implement subscription API"

Before committing, inspect:

    git status
    git diff

Do not include unrelated files or another person's changes in your commit.

## 6. When to Push

Push when:
1. A feature is ready for review.
2. Another teammate needs your committed changes.
3. An integration milestone has been reached.
4. You are ending a work session and want your progress backed up and available.

Push the feature branch:

    git push -u origin feature/short-task-name

For subsequent pushes to the same configured branch:

    git push

Do not wait until the entire project is complete to push.

Pushing does not automatically merge changes into `main`.

## 7. Frontend and Backend Compatibility

Before implementing or changing an API:
1. Read `API_CONTRACT.md`.
2. Confirm the endpoint, HTTP method, request fields, response format, and authentication requirements.
3. Follow the agreed interface.
4. Document proposed breaking changes before implementing them.
5. Update the contract when an approved change is made.

Frontend and backend work can happen independently when their interfaces are agreed upon.

If an endpoint is unfinished, the frontend can use a temporary mock for development, but the mock must not be mistaken for a working backend integration.

## 8. Integration Workflow

When a feature is ready:

1. Push the feature branch.
2. Open a pull request on GitHub.
3. Review the changed files and commit history.
4. Check API compatibility and dependencies.
5. Run relevant tests.
6. Resolve merge conflicts carefully.
7. Merge only after the changes are reviewed and sufficiently verified.

After merging, synchronize the local branch:

    git switch main
    git pull origin main

Before starting dependent work, confirm that the required changes are actually present in the current branch.

Never automatically merge every available branch.

## 9. Team Changelog and Task Tracking

After completing a meaningful task, update `TEAM_CHANGELOG.md` with:
- Contributor or Git author, when known.
- Branch name and commit hash.
- Summary of changes.
- Files affected.
- API, database, or configuration changes.
- Tests performed and results.
- Known issues.
- Dependencies and pending integration work.

Update `TASKS.md` to reflect task status and any new blockers.

Commit and push these updates when appropriate so other team members can retrieve them.

Do not invent contributor identities, test results, or commit hashes.

## 10. Final Safety Rules

- Never push directly to `main` unless the repository explicitly permits and the team approves it.
- Never use `git push --force` to bypass a rejected push.
- Never discard uncommitted changes without authorization.
- Never commit credentials or sensitive environment files.
- Never assume a commit is available to teammates until it has been pushed.
- Never assume a clean merge means the application works.
- Test the combined application before declaring integration complete.
- Keep `main` stable and use feature branches for ongoing development.