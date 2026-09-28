# Stage 1A: update the existing Windows/GitHub Desktop repository

This is an acquisition substage, not a completed Stage 1 cohort approval.
Do not create another repository and do not rerun Stage 0.
Use the existing public `cell-painting-build-2` repository and the separate account you already used.

## Exact steps

1. Download `Cell_Painting_Stage1_Runner_Update.zip` and right-click it in File Explorer > Extract All.
2. Open the extracted `COPY_CONTENTS_INTO_EXISTING_REPO` folder. Its top level contains
   `.github`, `stage1`, `.gitattributes`, `STAGE1_README.md`, `STAGE1_CHECKSUMS.sha256`, and `VERIFY_STAGE1.cmd`.
3. Open GitHub Desktop. In Current repository select `cell-painting-build-2`.
   Choose Repository > Show in Explorer (or the Show in Explorer button).
4. Copy the CONTENTS from step 2 into the repository folder opened by Desktop.
   Keep the `.github` and `stage1` folders intact. Let Windows merge the `.github` folder.
   Do not copy the outer `COPY_CONTENTS_INTO_EXISTING_REPO` folder itself.
   Existing Stage 0 files remain unchanged. On a repeated copy of this same update, choose Replace for these new files only.
5. In that repository folder, verify these exact nested paths exist:
   `.github\workflows\stage1.yml`
   `stage1\configs\acquisition.json`
   `stage1\scripts\collect_stage1.py`
   `stage1\tests\test_stage1.py`
   If Windows hides dot-prefixed folders, enable View > Show > Hidden items.
6. Double-click `VERIFY_STAGE1.cmd`. This READ-ONLY local check uses Windows PowerShell
   to verify every new file path and checksum. It does not install anything or connect to the internet.
   Continue only if it says `PASS`. If Windows blocks this helper, do not disable security controls;
   verify the four paths in step 5 and let the workflow run its own full checksum check.
   The helper was reviewed but cannot be claimed as executed on Windows in this Linux session.
7. Return to GitHub Desktop. Check all files in Changes. The change list must include
   `.github/workflows/stage1.yml` and `stage1/scripts/collect_stage1.py`, not flattened basenames.
   Enter `Add Stage 1 cohort acquisition` into Summary, click Commit to main, then Push origin.
8. Click View on GitHub. Open Actions. In the LEFT sidebar choose
   `Stage 1A - cohort acquisition`. Click Run workflow, leave branch `main`, tick the
   confirmation ONLY after confirming paid overages are disabled or no payment method exists, and click Run workflow.
9. Open the new run. Once it finishes, select Summary at the upper left if you are in job logs.
   On the run summary use Ctrl+F and search `stage1-acquisition`; select its entry in Artifacts to download.
   Download within three days. Send the resulting ZIP back to this chat even if the run failed.
   If no artifact was produced, return the failed-step error text instead.

## What this does

- Uses standard Python on a standard public Ubuntu runner; no scientific packages are installed for this acquisition-only job.
- Reacquires the pinned experiment metadata and four complete raw pilot plate CSVs.
- Collects actual source metadata, annotation tables, source revisions and image-reference filenames.
- Inventories raw/profile objects for the protocol and scope data without choosing cohorts by treatment performance.
- Limits source downloads to 768 MiB total and 128 MiB per raw pilot file.
- Uses a 45-minute collector timeout within a 55-minute job; reports errors rather than dropping inputs silently.
- Does not normalize, score compounds, interpret images or advance to Stage 2.

A green workflow means this acquisition substage succeeded. The assistant must still
check dose/control/compound joins, independence, feature compatibility and actual
comparison counts, and may need one further targeted Stage 1 acquisition of external
profiles after the metadata review. Stage 1 is NOT passed by a green workflow alone.

## Cost and privacy

This workflow targets standard public-repository compute only. It refuses acquisition without
explicit confirmation. No paid runner, cloud purchase, patient information, or secret key is required.
No expense is authorized by this package. Artifact allowance and account billing controls still apply.
The public data may total hundreds of megabytes; the artifact includes four raw pilot CSVs and compact metadata,
not raw microscopy images or the entire gallery. Keep the existing Stage 0 archive separately.

## Avoid the previous problems

Do not use the website's file picker to upload individually selected nested files.
Do not edit or rename paths in the browser. Use Desktop with the actual folder structure.
The new `.gitattributes` preserves this update's exact bytes across Windows/Linux Git settings.
It affects ONLY the new Stage 1 files, not Stage 0's existing checksum-protected files.

A second useful commit in this build repository is expected. Do not restart to remove it.

## Official instructions

https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
