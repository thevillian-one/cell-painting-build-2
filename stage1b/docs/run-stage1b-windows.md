# Run the prepared Stage 1B update on Windows

No repository restart, code editing, checksum calculation, Python installation or paid tool purchase is needed.

1. Download `Cell_Painting_Stage1B_Targeted_Update.zip`. In File Explorer, right-click it, choose **Extract All**, then open `COPY_CONTENTS_INTO_EXISTING_REPO`.
2. You should see exactly two folders: `.github` and `stage1b`. Copy both folders, not their loose files and not the outer folder.
3. In GitHub Desktop select your existing `cell-painting-build-2` repository, then **Repository > Show in Explorer**. Paste the two copied folders into that repository root. Let Windows merge `.github` with the existing directory; do not delete the old directory. The new `stage1b` folder must sit alongside the existing `stage1` folder, not inside it.
4. Confirm these exact paths exist before committing:
   - `.github\workflows\stage1b.yml`
   - `stage1b\configs\targeted-acquisition.json`
   - `stage1b\scripts\collect_targeted.py`
   - `stage1b\PACKAGE_CHECKSUMS.sha256`
5. In GitHub Desktop enter **Add Stage 1B targeted cohort acquisition** in the Summary box. Click **Commit to main**, then **Push origin** (or Publish branch if this branch is not yet published). Existing Stage 0/1 files should not show as changed. Do not edit them.
6. On GitHub open **Actions**, select **Stage 1B - targeted cohort acquisition** on the left, click **Run workflow**, keep **main**, and select the authorization checkbox only after confirming your public account's no-paid-overage setting. Click the green **Run workflow**. Start a new run, not "Re-run jobs" on an older workflow.
7. When this new run finishes, open its **Summary**. Download the artifact **stage1b-targeted-acquisition** and upload that ZIP to the chat. Return it even if the job failed. Its configured retention is seven days. If no artifact exists, return the failed step's log; do not make guessed code changes.

## What this run does

Fetches 15 selected profile files and precise metadata/pipeline evidence. It verifies original bytes and layouts, exports identity metadata, and records failures. It does not normalize, rank compounds, perform image analysis or start Stage 2. Full Stage 1 acceptance follows scientific review of the returned evidence.

The 11 listed S3 profiles total 284,524,641 bytes. Four LFS profile sizes are resolved from verified pointers at run time. Total transfer cap is 768 MiB, collector deadline 30 minutes, job limit 45 minutes. No GPU, paid packages or external API bill is requested. The workflow is restricted to a public repository on a standard Ubuntu runner; account storage quotas and billing controls remain your account settings.

## Why previous repairs are not repeated

This is an additive `.github` plus `stage1b` package. It does not modify old scripts, the earlier Latin-1 edit, root attributes, or STAGE1_CHECKSUMS.sha256. Its own integrity file is generated from the included bytes. New file attributes preserve exact line endings. No manual hash editing is required.

Use the downloaded ZIP, not a copy/paste of source code from chat. Preserve `stage1-acquisition.zip` and the Stage 1B checkpoint locally. Do not upload either large artifact ZIP to the repository.
