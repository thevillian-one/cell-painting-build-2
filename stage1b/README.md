# Stage 1B targeted cohort acquisition

Read [Windows directions](docs/run-stage1b-windows.md).

Run only the new **Stage 1B - targeted cohort acquisition** workflow. This is an additive update, not a restart and not Stage 2. The full scientific gate is still pending.

The prepared collector uses standard-library Python, frozen source paths, exact source integrity checks and metadata-only profile inspection. It does not use replacement text decoding or fit phenotype analyses. The returned artifact must be reviewed.

Source design findings: [cohort audit](docs/cohort-audit.md). Handoff: [next agent](docs/NEXT_AGENT.md). Tool choice: [Codex](docs/CODEX_HANDOFF.md).

Use `python stage1b/scripts/update_package_checksums.py` from the repository root only after an intentional reviewed code change. Do not disable verification. The included integrity manifest is already current.
