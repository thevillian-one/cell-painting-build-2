# Next agent: finish Stage 1B, never jump to Stage 2

## Read and verify

Read `docs/execution-plan.md` in full, `BUILD_STATUS.md`, `BLOCKERS.md`, `DECISIONS.md`, `reports/data-audit.md`, `configs/cohorts.yaml` and `configs/targeted-acquisition.json`.

The user authorized the assistant to build the project and currently authorizes Stage 1B only. The historical planning-only line in the unmodified v3 plan is not a reversal of the current explicit Stage 1B authorization. No user authorization for Stage 2 exists.

Required recovery parent: `stage1-acquisition.zip`, SHA-256 `e435e4bf38fdb5b7fd8ebf7d46f1d71b16adc8b1c8711686a58f5cbeb050fd24`. Its 693 manifest entries and 588 source records were reverified here. The prior small Stage1A review archive is optional for rerunning the main cohort audit, but needed for the separate receipt-review command that verifies its 16 entries.

Keep raw input archives separate from the public build repository. The Stage 1B checkpoint deliberately excludes the large parent inputs; verify its own CHECKSUMS.sha256 before trusting code/configuration.

## Immediate account handoff

The update ZIP contains `COPY_CONTENTS_INTO_EXISTING_REPO/.github` and `stage1b`. Merge both into the existing local `cell-painting-build-2` repository using GitHub Desktop on Windows, commit and push. Do not replace/delete the existing `.github` directory. It gets one new `workflows/stage1b.yml`. No Stage 0/1 source files or integrity records are changed.

Run `Stage 1B - targeted cohort acquisition`, branch main, with the required no-paid-usage confirmation. Return artifact `stage1b-targeted-acquisition`. The assistant has not launched that remote run. Do not say the targeted profiles are already downloaded.

## Review returned evidence

Verify all archive checksums and target receipt sizes/hashes, Git pointer hashes, LFS content hashes and S3 listing ETags. Inspect actual logs and failures. Join each raw/annotated profile to the packaged frozen layout; reconcile embedded sample metadata disagreements. Inspect source metadata only, not phenotype scores.

Resolve applied protocol compound dose, scope treatment duration/material aliases, Reagent1 unnormalized processing stage and source aggregation mismatch. Compare feature headers, extraction pipelines and metadata semantics. Scope group labels are provisional, not proven physical plate identities. Eight anonymous MOA labels are not public chemical cross-study matches. Nominal 1,000/2,000-cell conditions are distinct. Keep pilot positional and one-batch limits prominent.

Define actual eligible compound-condition groups and physically independent comparisons. If evidence remains insufficient, request another minimal precisely specified source rather than fabricate acceptance. Full Stage 1 requires justified cohort roles and a feasible independent evaluation design, or explicit approval of a narrower claim. Do not promote a green acquisition to a scientific pass.

## Local reproduction of this review

Extract the parent ZIP into `inputs/acquisition` without changing source bytes, then run:

```sh
python scripts/qualify_cohorts.py --input inputs/acquisition --output .
python scripts/build_targets.py --input inputs/acquisition --output .
python scripts/prepare_reference_data.py --input inputs/acquisition --output .
python -m unittest discover -s tests -v
```

The audit does raw pilot finite-value checks, metadata joins and combinatorial pair counts only. No scientific analysis package is required for these commands. The later Stage 0 scientific environment must be re-established/pinned for Stage 2, not assumed installed locally.

## Checkpoint handoff

Update all manifests, cohort config, audit report, status, blockers, decisions, run manifest and hashes. State separately what is verified, implemented but not run, or limited by design. Save outputs with relative paths. Never edit a checked file without regenerating and verifying the relevant checksum manifest. End with a simple TL;DR and minimal exact user actions. Stop at the Stage 1 acceptance gate.
