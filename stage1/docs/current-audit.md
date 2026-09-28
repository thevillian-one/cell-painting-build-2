# Stage 1 data audit: current checkpoint

Date: 2026-09-28 UTC. Authorized scope: Stage 1 only.

## Status

**Stage 0: PASSED on review of its returned external-run evidence.**

**Stage 1: BLOCKED pending external acquisition and subsequent cohort qualification.**
This is a partial executed Stage 1 checkpoint, not the completed scientific gate.
No cohort is yet accepted for the final comparison or held-out evaluation.

## What Stage 1 means

This stage checks the ingredients of the experiment before calculating its results:
what each well contains, how much compound was used, which wells are controls,
which plates can be compared, and whether repeats are genuinely separate experiments.

## 1. Stage 0 integrity re-verification

Input archive: `stage0-evidence(1).zip`.
Archive SHA-256: `bf894d58f2b8ebd678cc214d9d2581f2bdf667c81080b6084b921fbe68ed2eed`.
All 78 entries in the archive's `CHECKSUMS.sha256` matched their actual bytes.
The returned import and browser reports are successful, the three AP fixture answers
match their expected values, the recorded pip check exited zero, and the XML test
report contains 30 tests with zero failures/errors/skips.

These are verified records of a GitHub runner's execution, not new local imports of
its scientific packages. The runtime environment does not transfer merely because
its logs or a dataset were uploaded.

Evidence: `evidence/stage0-integrity.json`, `evidence/stage0-review.json`,
`inputs/stage0/evidence/`, and the original run logs.

## 2. Executed raw-profile structural audit

File: `inputs/stage0/data/BR00117015.csv`.
Source: `cpg0000-jump-pilot/source_4/workspace/backend/2020_11_04_CPJUMP1/BR00117015/BR00117015.csv`.

- Complete file size: 42,181,927 bytes.
- SHA-256: `66e809b0ab20cba2020b255b7c7c3f0fd10819430c17c2e21bff3ef2ff863839`.
- 384 rows, 384 unique plate/well identities, all 384 expected A01-P24 positions present.
- 5,794 columns: two metadata columns and 5,792 recognized compartment measurements.
- Compartment counts: Cells 1,938; Cytoplasm 1,923; Nuclei 1,931.
- No inconsistent row widths, duplicate headers, duplicate wells, missing numeric values,
  infinite numeric values, or nonnumeric measurement cells were found in this file.

This checks file integrity, shape, identity and missingness. It does not establish
correct segmentation, useful biological features, control quality, absence of spatial
artifacts, or that a compound is active. Some recognized measurement columns are
position/identifier-like; the provisional dictionary flags them for later review.
No model feature mask has been selected.

Evidence: `evidence/pilot-profile-audit.json`, `manifests/pilot-wells-unannotated.tsv`,
`manifests/feature-missingness.tsv`, and `manifests/feature-dictionary-provisional.tsv`.

## 3. Pilot candidate design

The returned, hash-verified experiment metadata at source revision
`56845c7d4dc322652952783d91dae0ffef47829f` contains exactly one matching row per
candidate in the specified batch. All four candidates agree on:

- Batch `2020_11_04_CPJUMP1`.
- Plate map `JUMP-Target-1_compound_platemap`.
- A549, Parental, compound perturbation, 48-hour exposure.
- Density code `100`, meaning baseline percentage, not 100 cells per well.
- Antibiotics absent, delay `Day0`, times imaged `1`, listed anomaly `none`.

| Plate | Raw matrix available here | Source image count | Current qualification |
|---|---:|---:|---|
| BR00117015 | Yes | 49144 | Structurally verified, biological annotation still pending |
| BR00117016 | No | 49152 | Metadata identity only |
| BR00117017 | No | 49144 | Metadata identity only |
| BR00117019 | No | 49152 | Metadata identity only |

The eight-image count difference is flagged, not explained away or assumed to be a
missing well/channel. Actual image-reference rows and acquisition information must
resolve it. No image pixels were opened or interpreted.

The matrices contain `Metadata_Plate` and `Metadata_Well`, but not compound IDs,
doses or negative-control labels. Consequently the local audit cannot yet verify
control counts, compound counts, exact concentration or biological replicate groups.
These quantities remain unknown in the manifests rather than filled from a generic
library layout. The four plates share one batch label; this does not demonstrate
independent-batch or interlaboratory generalization.

## 4. Public-source research, separate from acquired data

The following are documentation observations, not completed file-level audits:

1. The JUMP-Target repository distinguishes version-1 and version-2 layouts/sample IDs.
   It recommends InChIKey for cross-version identity matching. Using a similar name,
   a stripped sample-ID prefix, or the wrong platemap can silently misassign treatments. [W1]
2. JUMP-Target's README recommends 5 uM; JUMP-MOA recommends 3 uM. Recommendations
   are not proof of the concentration actually applied in our plates. [W1, W2]
3. JUMP-MOA documents four within-plate replicates per compound and warns of the
   repeated-position confound in the JUMP-Target layout. We must verify the actual
   well maps, not infer sample sizes from the README. [W2]
4. Eight JUMP-MOA compounds have de-identified names. Their suggested same-MOA
   replacements are not necessarily the original chemicals. Do not assign an
   undisclosed compound the identity of a replacement. Exclude unresolved identities
   from exact cross-dataset chemical matches while retaining documented within-set IDs. [W2]
5. The protocol study spans many optimization experiments and provides a master table.
   Its repository links pilot data as well as protocol data. Different repository or
   accession names alone do not establish independent material. [W3]
6. Gallery documentation lists pilot/scope as v2.5 and protocol as v3 plus experiments.
   This establishes a potential protocol mismatch to audit, not a reason to reject all
   data. Direct cross-dataset profile comparison needs compatible feature semantics. [W4]
7. The scope data repository exposes metadata, load-data references and pipelines;
   its separate analysis repository provides a processed-profile location. A file in
   `profiles/` is not automatically a raw unnormalized aggregate. [W5, W6]

## 5. Cohort decisions at this stop

| Cohort | Status | Why it is not yet accepted |
|---|---|---|
| Four A549 pilot plates | LIMITED CANDIDATE | Only one raw matrix locally available; dose/control/compound joins and image references not yet acquired |
| Protocol U2OS JUMP-MOA | PENDING DATA | Coherent condition, exact plate list, controls and independent preparations not verified |
| Scope U2OS JUMP-MOA | LIMITED CANDIDATE | Possible acquisition-sensitivity panel; independent biological test role not established |

Rejected now are invalid comparison roles, not whole datasets: treating A549/U2OS as
identical conditions, treating reimaging as biological replication, assuming all
optimization protocols are interchangeable, or imputing chemical identities from MOA.

## 6. Current infrastructure result

A new ordinary HTTPS curl request to the pinned official metadata source failed with
`curl: (6) Could not resolve host: raw.githubusercontent.com`. No usable new source
bytes were downloaded locally. The dedicated download tool also did not deliver a file.
GitHub plugin discovery reports that the plugin is not installed in this session.
The established, successful route is still the user's public GitHub Actions runner.

This does not invalidate Stage 0. Stage 0 validated the external route; it did not
repair this local runtime or give this assistant authority to trigger GitHub jobs.

## 7. Next authorized substage

A prepared Stage 1A update is provided for the existing `cell-painting-build-2`
repository. It collects all four exact raw pilot aggregates, source metadata/maps,
protocol/scope design files, source revisions, pilot image references, and exact
external numerical-object inventories. It uses Python's standard library only and
does not run scientific normalization or evaluation.

External raw profiles will be selected after their metadata are inspected, not by
an arbitrary first-file choice. A further bounded acquisition within Stage 1 may be
needed. A successful acquisition workflow is not a Stage 1 acceptance decision.

## 8. Actual Stage 1 code/package checks

54 offline tests passed, including a synthetic end-to-end acquisition/bookkeeping
case and a deliberately failing transfer. These fixtures validate downloader and
manifest logic; they are not public-data acquisition or biological results.
Python compilation and embedded workflow shell syntax checks passed.
A local Git roundtrip with `core.autocrlf=true` preserved the 12 new package file
checksums and left all 14 original Stage 0 source files unchanged. This was a Linux
Git configuration test, not a Windows GUI or PowerShell execution test.

Evidence: `logs/stage1-unit-tests.stderr.txt`, `evidence/package-tests.json`.
The remote Stage 1A workflow is IMPLEMENTED_NOT_RUN. It is not presented as a
successful download or completed cohort audit.

## Sources

[W1] https://github.com/jump-cellpainting/JUMP-Target

[W2] https://github.com/jump-cellpainting/JUMP-MOA

[W3] https://github.com/carpenter-singh-lab/2023_Cimini_NatureProtocols

[W4] https://github.com/broadinstitute/cellpainting-gallery

[W5] https://github.com/jump-cellpainting/jump-scope

[W6] https://github.com/jump-cellpainting/jump-scope-analysis

Source web pages were reviewed during this turn. Apart from material already included
in Stage 0, their raw Git trees/tables have not yet been downloaded into this runtime.
URLs in this section are source references, not claims that complete raw-data retrieval succeeded.
