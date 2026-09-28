# Cell Painting: Stage 0 bootstrap

This is an infrastructure check, not the finished portfolio project.
No compound analysis or biological benchmark runs here. The full plan is in `docs/execution-plan.md`.

## What this checks

A Python 3.12 Linux runner resolves an official source revision, downloads the experiment metadata and exactly one officially listed unnormalized pilot aggregate, checks its source bytes/header/three sample rows, installs the planned scientific dependencies in an isolated environment, checks imports, runs three tiny known-answer AP fixtures, and starts an infrastructure-only Streamlit fixture in a real Chromium browser.

The raw profile's final object key, actual size and hash are intentionally not invented in this package. The script discovers them from the public S3 listing and records them at runtime. It stops rather than substituting a normalized file, changing plates, or generating biological data.

## Upload once, then run

1. Create a NEW public GitHub repository called `cell-painting-build`. Keep automatic README, .gitignore and license creation OFF. This is a temporary development/bootstrap repository, not a completed scientific portfolio entry.
2. Extract this ZIP. Open the folder containing this README. In Finder press **Command + Shift + period (.)** to show `.github` and `.gitignore`. Upload ALL contents at the repository root in ONE upload. Keep the `scripts`, `tests`, `configs`, `docs`, and `.github/workflows` paths intact. Do not upload the ZIP or the outer folder itself. Commit as `Add Stage 0 access and runtime checks`.
3. Check that `.github/workflows/stage0.yml` is present. Keep paid Actions overages disabled. If you have not added a payment method, GitHub blocks usage that would exceed included allowances. If billing is already enabled, verify that it blocks paid overages before proceeding. The assistant cannot see or certify your account's billing settings.
4. Open **Actions**, enable workflows if prompted, select **Stage 0 - access and runtime**, then **Run workflow** on the default branch. Check the required no-paid-usage confirmation box, then click Run workflow. This workflow is manual-only and refuses to run in a private repository.
5. When the run finishes, open its run summary. Under **Artifacts**, download **stage0-evidence**. Upload that ZIP to the chat, even if a test failed. The artifact is retained for three days. If the job fails before an artifact is available, return its error/log instead. Do not pay to unblock a quota without discussing it first.

You do not need to install Python, packages, AWS tools, or Git on your Mac. Do not supply tokens or passwords. The workflow fetches only public files and needs read-only repository permissions.

## Expected upload structure

```text
.github/
    workflows/stage0.yml
.gitignore
AUTHORIZATION.md
BOOTSTRAP_CHECKSUMS.sha256
README.md
requirements-stage0.in
configs/stage0.json
docs/execution-plan.md
scripts/
    preflight_support.py
    run_stage0.py
    smoke.py
    smoke_streamlit_app.py
tests/
    conftest.py
    test_preflight.py
```

Files must be uploaded without editing them: the workflow verifies `BOOTSTRAP_CHECKSUMS.sha256` before running. If a file is missing, fix that upload, not the integrity check. Legitimate development commits are normal. One prepared initial upload is possible; the workflow itself does not commit generated outputs.

## Output and interpretation

The artifact includes actual commands, runtime/resource information, HTTP status/headers, source revision, one raw aggregate, the complete header and three-row preview, a resolved dependency report and hashed wheel lock, import/test logs, a browser screenshot, the plan, code snapshot, RUN_MANIFEST.json and CHECKSUMS.sha256.

A runner success means the technical checks executed there. Stage 0 remains open until the assistant verifies the returned artifact. It is not evidence that the future scientific analysis is correct. No Stage 1 work begins automatically.

`requirements-stage0.in` is a proposed discovery specification, not a tested lockfile. Core choices are Pycytominer 1.7.1 and copairs 0.5.4. The latter requires Python <3.13, so the prepared runner uses 3.12. Transitive dependencies are resolved once into `environment/requirements-linux-py312.lock.txt` in the output. That lock records actual downloaded wheel hashes and targets that runtime; reference-method reproduction and any legacy environment are Stage 2 work.

Only binary wheels are accepted. A missing compatible wheel is reported as a blocker, not bypassed by ignoring version constraints or silently replacing packages. All expensive commands have timeouts. Downloads are bounded to 256 MiB for one profile, 1 GiB uncompressed and a small number of metadata/listing files. A 4 GiB free-disk floor is checked before starting. The entire job has a 40-minute safety timeout, not a completion-time prediction. No large-image download, GPU, paid AI API or cloud server is requested.

The code/configuration and fixture tests were checked locally. The network acquisition, Python 3.12 dependency installation and Streamlit browser check have NOT yet been verified end to end. They require this external run.

## Return prompt

> Review this returned Stage 0 artifact against the included version 3 plan. Verify its checksums, source bytes/provenance, dependency reports, actual logs, known-answer tests and Streamlit browser result. Complete or debug Stage 0 only. Do not begin Stage 1; report the gate status and any remaining blocker.

## Primary references

- Data and pipeline: https://github.com/jump-cellpainting/2024_Chandrasekaran_NatureMethods_CPJUMP1
- Public dataset access: https://registry.opendata.aws/cellpainting-gallery/
- Package specifications: https://pypi.org/project/pycytominer/ and https://pypi.org/project/copairs/
- Manual runs: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- Artifacts: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
- Runner resources: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- Billing/quotas: https://docs.github.com/en/billing/concepts/product-billing/github-actions

Standard hosted compute is free in public repositories; artifact quotas/account billing still need attention. No account spending has been verified or authorized by the assistant.
