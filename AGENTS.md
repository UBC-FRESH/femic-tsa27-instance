# AGENTS.md

This file is the working contract for coding agents in FEMIC TSA 27 Revelstoke Instance.

Public FEMIC deployment instance and WS4 model case for the Revelstoke TSA (TSA 27), with a reproducible TSR evidence base and a caribou-policy modelling pipeline.

Keep this file short. Each rule below either checks itself or points to the page that explains it.
The workflow rules come from the UBC-FRESH dev workflow, which this project was seeded from. Project-
specific rules go at the end, each with its reason.

## Session start

Before you change anything, read in this order:

1. This file.
2. `ROADMAP.md`: the active phase and its "Detailed Next Steps Notes".
3. The latest entries in `CHANGE_LOG.md`.
4. The notes your task names, in `notes/`.
5. The docs pages that govern your task, in `docs/`.

Cite the pages you relied on in your report.

## Working principles

- **Evidence over trust.** Cite command output, diffs, commit hashes, and URLs.
- **One bounded move at a time.** Stop and report after each one.
- **No oracle, no capability.** A new agent-facing capability needs a validator that can fail.
- **Workflow as scaffold.** Create the parent issue, the branch, and the roadmap entry before the work.
- **Structured handoff.** Issues, the roadmap, notes, and the changelog carry the state.
- **Preserve uncertainty.** Say what you did not verify, and why.
- **Scope discipline.** Stay inside the active phase and task.
- **Sanitized output.** Keep private data, credentials, raw transcripts, and personal paths out of
  tracked files.

## The green dashboard rule

`python scripts/dashboard.py` runs every quality gate: lint, format, strict types, tests with a coverage
gate, the workflow validator, and the docs build with warnings as errors.

- Every commit leaves the dashboard green.
- Any change from green is investigated and fixed immediately. There are no exceptions.
- A failure you did not cause is still yours to fix, or to report with evidence before you continue.
- Do not weaken a gate to make it pass. A gate changes only with a changelog entry that explains why.
- Record the dashboard result in the changelog entry for each task that you close.

## Typing and docstrings

- Every function, method, and test has complete type annotations. `mypy --strict` must pass.
- Every public function has a numpy-style docstring. Its parameters and return value match its annotations.
- Do not use `Any`, `# type: ignore`, or `cast` without a comment that says why. A suppression names its error code.

## Testing policy

- Every function you write or change gets unit tests in the same change set. Tests must be able to
  fail, and each one asserts a specific behavior.
- Keep the layers: unit tests for each function, contract tests for public interfaces, integration
  tests for the command-line tools, property tests for invariants, and the self-check.
- The coverage gate is 95 percent branch coverage of `scripts/`. Aim near 100 percent, with tests that
  assert something.

## Embedded agent capabilities

If this project ships complicated software, it may offer agents validated capabilities instead of
documentation alone. A capability is a prompt, a validator over real state, and a bounded retry
budget. No oracle, no capability. Each capability needs offline tests with a fake provider, and it
must say what its validator checks and what it does not.

## CI and merges

- CI runs every gate on every pull request, and on every push to `main`.
- No pull request merges while CI is red.
- A merge happens only as part of an approved phase close-out. Queue the pull request, write the report in `notes/reports/`, and wait for the maintainer's approval.

## Planning workflow

- One phase is one GitHub parent issue and one feature branch, `feature/p<n>-<slug>`.
- One task is one child issue, linked to the parent as a sub-issue.
- A subtask is a checklist item in the child issue body. Three levels at most.
- Keep `ROADMAP.md`, `CHANGE_LOG.md`, `notes/`, issue bodies, and PR descriptions in step.

## Approval gates

You may, within the active phase: create and commit to its branch, push that branch, open and update
its issues and pull requests, and run local checks.

After the maintainer approves a phase close-out, carry out what the report recommends: squash-merge the pull request, delete its branch, close the parent issue, and launch the next phase. Name every settings change, tag, release, or external account in the report, with its exact command, and wait for approval of each one.

You must wait for an explicit approval before you: create a tag or a release; change repository visibility, settings, or branch protection; create an external account, repository, or server; touch private data or credentials; or delete anything beyond the branch that an approved report names.

## GitHub hygiene

- Audit read-only first: `gh issue list`, `gh issue view <n>`, `gh pr list`.
- Write bodies and comments to files, and post them with `--body-file`. Never build them from escaped strings.
- Read back every comment or edit with `gh issue view` before you report it as posted.
- Post a progress comment when a task or phase milestone completes, and a closeout comment before you close an issue.

## Formatting

- Put section labels on their own lines, such as `Phase identifier: P0`.
- Use real task-list syntax, one item per line.
- Wrap branch names, paths, commands, and commit hashes in backticks.
- Start commit messages with the task ID, for example `P0.1 add license`.

## Verification

Run the dashboard before you report a change as done:

```bash
python scripts/dashboard.py
```

Record the result in the changelog entry for the milestone.

## Public safety

- No private data, credentials, raw transcripts, unpublished documents, or machine-specific paths in
  tracked files.
- Use placeholders, repository-relative paths, or environment variables in examples.

## Project-specific rules

- **The TSR record is the policy source of truth.** Cite the document, cycle, and PDF page from
  `reports/tsa27-tsr-corpus-analysis.md` before changing a caribou or land-base assumption.
  Reason: the model must be traceable to the legal and analytical record, not to memory.
- **Do not collapse caribou to one netdown.** The TSR record contains seral constraints, a
  spatial reserve netdown, a legal LHLB exclusion, a core/matrix recovery constraint, and an
  80-year immature deferral. Keep them as separate, switchable layers in WS4. Reason: the
  question is the attribution of the AAC effect, not just a land-base subtraction.
- **No raw data or TSR PDFs in git.** Fetch public data and documents into ignored paths with
  `scripts/fetch_tsr_corpus.py` and the public-data mirror. Track only metadata, curated tables,
  and short evidence excerpts. Reason: the repository is public and the source documents have
  their own licences.
- **No personal or machine-specific paths in tracked files.** Use repo-relative paths,
  `${FEMIC_EXTERNAL_DATA_ROOT}`, or placeholders. Reason: the instance is public and portable.
- **Every model run records its dataset manifest, scenario config, seed, WS4 version, and run
  ID.** Reason: the AAC attribution must be reproducible.
- **Validate against the TSR before claiming a result.** The 2010 TSR4 sensitivities are the
  quantitative benchmark; the 2022 TSR5 analysis is unpublished, so any 2022-style result is a
  documented best guess. Reason: preserve the uncertainty rather than inventing a validation.
- **Cross-repository state lives in GitHub issues.** Read the open issues in `UBC-FRESH/ws4`,
  `UBC-FRESH/femic`, and this repository at session start and before closing a phase. Reason:
  the instance is linked into FEMIC and consumed by WS4; the maintainer should not have to relay.
- **The instance is standalone first.** It must install, validate, and document itself without a
  parent checkout; the `femic/external` submodule is a link, not a build dependency. Reason:
  students and collaborators clone the instance directly.
