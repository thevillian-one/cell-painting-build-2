# Cell Painting Hit Reliability Lab
## Standalone assistant execution plan, version 3

Planning date: September 27, 2026  
Project owner: Alyan Malik  
Execution owner: the assistant, through available tools and explicitly authorized external runs  
Current authorization: **PLANNING ONLY. Do not execute Stage 0 or any later stage until the user authorizes it.**  
Current evidence: no new download, package-installation, benchmark, experiment, application build or project test was performed while preparing this revision.

This document replaces version 2 as the operational specification. It preserves its scientific stages and adds an explicit access-resolution gate, dependency strategy, predetermined-test protocol, resource and cost controls, and a memory-independent handoff. It includes the candidate plate identifiers and literature previously delegated to an earlier plan. No earlier conversation or plan is required to follow it. Unknown quantities are listed as decisions to verify, not supplied with invented values.

## Read first: instructions for a new agent

1. Read this document completely, then the latest checkpoint's `BUILD_STATUS.md`, `NEXT_AGENT.md`, `BLOCKERS.md` and `DECISIONS.md`, when available.
2. The user wants the assistant to build, execute, test and package the whole project. Do not turn it into a course, a months-long task list for the user, or a collection of unexecuted scripts presented as completed science.
3. Quality and honest evidence take priority over speed, novelty, attractive results, or minimizing commits. No personal wet-lab work or clinic/patient data is involved.
4. Do not assume prior runtime packages, network access, source files or cloud credentials persist. The historical failure below is unresolved, not proof that every future tool/runtime will fail.
5. Execute only the stage explicitly authorized by the user. Stop at that stage's acceptance gate, provide a recoverable checkpoint and a short result/blocker summary, and wait for permission to proceed. A stage may require several turns or sub-runs.
6. Ask the user only for essential account authorization, a precisely specified file/artifact transfer, or approval of a cost/scope decision. Dataset selection, methodology, code and troubleshooting remain the assistant's responsibility.
7. Do not promise unattended work after a response. External runs require explicit user authorization and a verified supported launch mechanism; do not imply that a connector has capabilities it has not exposed.
8. Never mark a stage passed because its code exists. Verify execution and inspect its output. Screenshots, generated numbers, or a successful interface startup are not a substitute for scientific validation.

## 1. Responsibility, standard and deliverables

The assistant owns literature verification, data inventory/acquisition, scientific design, implementation, experiments, debugging, testing, user interface, reports, reproducibility and publication packaging. The user need not install tools on their own Mac or learn coding first. Their device information is needed only if they explicitly choose local execution or an untested local deployment must be diagnosed.

Target the same scientific deliverables and quality gates as a carefully conducted several-month project. The earlier 195-290-hour / 5-8-month estimate described a human work schedule, not a guaranteed assistant duration. Faster code generation does not replace data qualification, genuine experimental replication, held-out analysis, or independent review. Do not guarantee equivalent external scrutiny or an error-free result.

Deliver all of the following:

- A versioned Python analysis package and a reproducible download-to-report workflow.
- Executed results from real public Cell Painting experiments, with original-source provenance and declared exclusions.
- Reference reproduction, normalization sensitivity, physical-plate influence, feature-channel ablation with matched-size controls, and appropriate held-out evaluation.
- Separate evidence for activity, replicate agreement, distinctiveness, sensitivity and generalization.
- Genuine microscopy images mapped to the analyzed wells, with reproducible display transformations.
- A Streamlit research interface and a compact static HTML evidence viewer that can be inspected without installing Python.
- A test suite, actual test/run logs, methods, limitations, data card, a scientific case study and a technical walkthrough.
- A clean GitHub-ready release, README, source notices, code/data license documentation, and high-resolution screenshots.

No paid AI API, new foundation model, wet-lab experiment, proprietary dataset or clinic information is a prerequisite. No improvement over baselines is promised. Failure to demonstrate added value is a legitimate result; failure to execute required tests must instead be labeled incomplete.

## 2. Stage 0: resolve access and establish the runtime before scientific execution

### 2.1 The unresolved blocker

**The version 2 plan reports: web research worked, but direct public-file downloads from the code-execution environment failed with a name-resolution error; a separate file-download attempt also failed.** The report additionally listed Python, NumPy, pandas, SciPy, pytest and Playwright as available then, and PyArrow, Streamlit, Pycytominer and copairs as absent.

Treat those as historical observations recorded in the user-supplied plan, not as fresh measurements or permanent platform facts. Recheck only after Stage 0 is authorized. A browsed webpage is not a raw profile file in the analysis filesystem. An uploaded dataset does not by itself solve missing dependencies, runtime limits or permissions.

**Stop/go rule:** no end-to-end biological analysis starts until both a verified raw-data route and a working scientific execution route exist. Do not work around this gate by generating synthetic biological results, inventing benchmarks, or silently dropping specialist methods.

### 2.2 Route A: available authorized tools, with a minimal test

After authorization:

1. Record tool capabilities, Python/OS/architecture, available disk/RAM, process limits and installed distributions. Preserve command outputs. Do not make network calls through a tool whose contract explicitly disables them.
2. Test the dedicated download capability or another authorized network route with one small official metadata/source object. Check response bytes, status, format, size and hash. A login/error HTML page is not a valid download.
3. Resolve one actual unnormalized well-level profile object from the official listing and retrieve it. Inspect the full header and a small row sample without running compound analyses.
4. Establish a compatible project environment, including the specialist packages in section 16.2. Install transitive dependencies and any required browser binaries in that same execution environment.
5. Run an import smoke test, a tiny known-answer calculation and a browser startup test. Record commands, versions, elapsed time and peak resources.
6. If access fails, preserve the exact failure and try a bounded set of genuinely distinct authorized routes. Do not repeatedly retry a tool documented as network-disabled or evade network/security restrictions.

If Route A passes, the user need not download files or install anything locally.

### 2.3 Route B: prepared GitHub Actions runner outside the chat sandbox

If Route A cannot supply data or dependencies, the preferred initial fallback is a prepared, user-authorized GitHub Actions workflow. The runner downloads public data and installs dependencies in its own environment; it does not repair networking inside the chat sandbox.

The assistant prepares a small bootstrap package: a workflow with `workflow_dispatch`, an environment specification, a source-inventory script, checksum logic, a smoke test, and compact artifact collection. Build this package only after authorization. If a GitHub connector is available, discover its actual permissions and supported actions before relying on it to create files, start runs, or retrieve artifacts. Repository read access does not imply Actions control.

Minimum user actions, when no suitable write/run connector is available:

1. Put the prepared bootstrap files into a repository they own, with the stated folder structure. The assistant provides all files and instructions.
2. Enable Actions if necessary, then run the named workflow from the Actions tab.
3. Upload the resulting compact ZIP containing inventory, logs, environment details and approved files/results to the chat. A screenshot of a green check alone is insufficient to verify the analysis.

Official instructions for manual runs and artifact downloads are in [S19, S20]. No personal token or password should be pasted into chat. Public source downloads do not require AWS credentials. [S2]

As checked in official documentation for this plan, standard public-repository Linux runners offer 4 CPUs, 16 GB RAM and 14 GB SSD; hosted jobs have a 6-hour limit. Public standard compute is free, but this is not unlimited memory, disk, artifact storage or freedom from rate limits. Private repositories use account allowances and may incur charges. Recheck these facts before selecting a runner. [S17, S18]

Do not assume the prior 20 GB working-storage target fits a 14 GB runner. Inventory first; use bounded downloads, plate-wise processing and small resumable jobs, or request a more suitable runtime. Upload compact scientific outputs and logs, not all raw images. Measure dependency/cache disk overhead. Respect artifact quotas and retention.

For long analyses, the assistant still writes, tests and interprets all code and results. The user is only the account/operator bridge when required. Do not claim a remote run succeeded until its actual outputs have been retrieved and checked.

### 2.4 Route C: exact public-file transfer plus compatible dependency bundle

If an external runner is unavailable or undesirable, prepare one manifest-driven upload request, not a vague instruction to download the dataset.

The request must specify, for each file:

- Exact source URL/object key and upstream revision or version when available.
- Exact local destination/name and whether it is raw, aggregated, normalized, metadata, or an image.
- Published checksum when available; otherwise a clearly labeled calculated SHA-256 and later consistency check.
- Measured byte size and total transfer size, allowed format and why the file is needed.
- Whether it is needed immediately or in a later authorized stage.
- Verification status: raw retrieval tested, listing verified only, or not yet resolved.

Do not present guessed S3 object names as verified direct download links. Do not ask for the entire Gallery or an entire multi-gigabyte source repository. The verified entry points and exact candidate plate IDs are in section 16.1; the final per-object request must be generated from the actual inventory.

An offline dependency bundle must target the assistant runtime's Python ABI, OS and CPU architecture and include transitive dependencies. Mac-installed packages or macOS wheels do not become Linux packages merely by uploading them. Prefer an assistant-prepared Linux runner/container to build the compatible bundle; test it with offline installation/imports before treating the gate as passed. If this is impractical, prefer Route B or a properly provisioned remote runtime rather than transferring the technical burden to the user.

### 2.5 Route D: user-approved persistent compute

If reliable runtime, memory, disk or long-run persistence is the limiting issue, propose a CPU cloud machine or larger runner with specific resource needs, current costs, an explicit spending cap, storage/egress assumptions and automatic shutdown. A GPU is not the default for well-level tabular profiling.

The user has expressed willingness to pay when there is a significant advantage, but has not authorized a purchase or an unlimited budget. Paid infrastructure must address a measured bottleneck, not serve as a substitute for experimental independence or sound statistics.

### 2.6 Stage 0 outputs and acceptance

Produce `docs/environment-and-access.md`, `manifests/access-inventory.tsv`, environment/lock files as appropriate, actual smoke-test logs, `BLOCKERS.md`, and a checkpoint.

Pass only if one real public well-level profile file is verified as bytes in the chosen execution runtime, required imports work, a known-answer test and browser check execute, and an artifact route back to the assistant is demonstrated. The selected source and environment may be remote; raw data need not pass through chat when the assistant can verify executed outputs and provenance.

If blocked, stop and state the precise user action needed. Do not proceed to scientific results or quietly narrow the deliverable. Confirm the final execution route and limits before asking for Stage 1 approval.

## 3. Product definition

Question: Which compound-associated morphological signatures are reproducible under a defined experimental condition, and which results depend on the analysis choices or individual experimental plates?

Each result must identify compound, dose/unit, cell line, exposure and experimental grouping. The application will keep these dimensions separate:

| Dimension | Intended evidence |
|---|---|
| Morphological activity | Difference from negative controls and replicate retrieval against controls |
| Replicate agreement | Cross-plate similarity and query-level retrieval scores |
| Distinctiveness | Same-compound retrieval against other compounds, reported separately |
| Analysis sensitivity | Normalization, omitted-plate and feature-channel comparisons |
| Evaluation strength | Held-out performance and the independence of the experimental units |

There will be no unsupported probability of reliability or claim of therapeutic efficacy. A reproducible control-like profile is different from a reproducible active profile. Channel dependence can reflect a meaningful phenotype, not necessarily a defect. Low cell counts are diagnostics, not a validated assay of viability.

A complete release includes both a usable application and its reproducible scientific pipeline. External generalization is a claim to evaluate, not a success result to assume.

## 4. Stage 1: Acquire and qualify the experimental cohorts

### Assistant actions

Inspect the JUMP pilot and its author-maintained analysis repository first. It provides well-level aggregate features as well as normalized reference profiles and image-location metadata. Start from unnormalized aggregate measurements for alternative normalization analyses. [S1]

Starting candidate: `cpg0000-jump-pilot/source_4`, batch `2020_11_04_CPJUMP1`; parental A549 cells, compound perturbations, 48-hour exposure, baseline density, no antibiotics, first imaging and no listed anomaly. Candidate plate barcodes: `BR00117015`, `BR00117016`, `BR00117017`, `BR00117019`. Recheck each against the downloaded `benchmark/output/experiment-metadata.tsv` and the actual profile files. This is a prespecified starting candidate, not a qualified cohort. All four are reported as one preparation batch: held-out plates from it do not demonstrate independent-batch or interlaboratory generalization. [S1, S9]

Audit a coherent U2OS JUMP-MOA subset from `cpg0001-cellpainting-protocol` as a candidate development panel and `cpg0002-jump-scope` as a candidate transportability panel. Use the optimization repository's experiment master metadata and the imaging-systems paper before assigning roles. These are candidates, not confirmed matching cohorts. The imaging-systems study describes 90 compounds at 3 micromolar and prepared plates shipped for imaging; trace the physical preparations before calling acquisitions independent. A shared compound name, accession or folder is not proof of matching biology or independence. Do not use A549 pilot measurements as matched-condition development data for a U2OS test. [S10, S11, S12]

Create profile, design, feature and image manifests. Record exact source URL/object key, upstream revision when available, byte size, checksum, retrieval date, license, processing stage and local file path. A locally calculated checksum detects later corruption; it is not proof of source authenticity unless compared with a trusted source checksum.

Download complete selected plates with their controls, not only visually appealing compounds. Use a predefined small development subset only for debugging; the final benchmark includes all eligible compound-condition groups in the chosen panel. Keep raw sources untouched outside Git.

Inspect file sizes before downloading. Start with selective CPU-oriented processing and measure resources before expanding. The previous 10 GB download / 20 GB working-storage figures are planning ceilings to reassess against the actual execution environment, not promises about dataset sizes.

### Cohort acceptance

Verify compound IDs, concentration units, biological condition, plate identity, feature-extraction compatibility, control counts, duplicate keys and metadata join cardinality. Missing essential metadata leads to an explicit exclusion or a narrower comparison, not invented values.

Target sufficient independent plates for both development and evaluation. The prior four-development/two-test-plate target is a design target, not a guarantee of statistical power. Do not use a pilot holdout that leaves too few independent positives for the declared endpoint. Identify another documented public cohort where necessary.

If an external cohort only offers repeat acquisitions of the same material, analyze acquisition sensitivity separately. Do not quietly rename that experiment independent biological validation. Investigate a suitable alternative and document any remaining scope limitation.

### Output and gate

Outputs: `manifests/`, `configs/cohorts.yaml`, `docs/data-card.md`, `reports/data-audit.md`.

Gate: every retained well has traceable identity and an explicit replicate group; the proposed evaluation's independence and comparison counts are documented. No outcome-driven selection of cohorts.

## 5. Stage 2: Reproduce and freeze a trustworthy baseline

### Assistant actions

Reproduce one author-provided pilot retrieval calculation on a specified subset. Use upstream processed profiles where needed to isolate metric reproduction from preprocessing reproduction, then compare the corresponding aggregate-to-profile processing separately. The source repository describes its preprocessing and AP benchmark tasks. [S1]

Use Pycytominer and copairs where supported by the execution environment. Pin compatible dependencies and source revisions. Check AP calculations with hand-computed examples, including ties, missing positives and zero vectors. copairs and the associated paper supply a methodological baseline, not automatic proof that our grouping is correct. [S3, S4]

Compare intermediate shapes, feature counts, selected wells, normalized values, pair counts, score definitions and numerical outputs. Keep an upstream-reproduction configuration separate from the stricter held-out-evaluation configuration.

### Output and gate

Outputs: reference configuration, baseline result tables, comparison script and `reports/reference-reproduction.md`.

Gate: reproduced values agree within a declared tolerance, or a substantive discrepancy is resolved and described accurately. A similar-looking chart is insufficient. Unresolved errors in the primary calculation block release.

## 6. Stage 3: Implement the scientific analysis package

### Data quality and preprocessing

Implement schema checks; strict join validation; duplicate detection; controls and missingness reports; documented anomaly flags; available cell-count and image-quality diagnostics; and spatial plate diagnostics. Maintain a QC decision ledger.

Do not discard a replicate because it weakens a result. Keep failed-control or insufficient-data conditions visible as not assessable. Prespecify any low-cell-count exclusions separately from exploratory sensitivity checks.

Implement three normalization configurations:

1. Plate-local DMSO MAD robustization as the primary reference.
2. Plate-local DMSO standardization as an alternative.
3. Whole-plate MAD robustization as an exploratory reference-population sensitivity analysis.

These operations are supported by the Pycytominer normalization interface. Exact formulas, scaling constants, epsilon behavior and degenerate-feature rules will be documented and tested. [S5]

Use an explicit feature list, not every numeric column. Keep identifiers, file indices, coordinates and cell-count diagnostics out of the primary phenotype vector. Proposed development starting points are 5% missingness and 0.90 feature-redundancy correlation; verify the library semantics and sensitivity on development data before freezing them. These values are starting conventions, not proven optimal thresholds. [S13]

Fit feature selection, imputation and optional fitted transforms on development data only, refitting inside each development-validation fold. Keep the feature set fixed for the primary normalization comparison; report any full-pipeline re-selection experiment separately. Split-before-fit prevents common evaluation leakage. [S6]

Under a frozen calibration protocol, an incoming plate's controls may calibrate its scale. Its treatment measurements must not select the method, feature mask or thresholds. Reserve or cross-fit negative controls for control-only null checks.

### Metrics

Implement replicate retrieval against controls using explicitly eligible positive and negative pairs. Positives share compound, dose and condition. Exclude self-matches, same-physical-well reimages and, for the cross-plate endpoint, all candidates on the query's physical plate. Apply symmetric plate restrictions to positive and negative candidates. The retrieval universe for activity is the eligible same-treatment replicate wells plus eligible DMSO wells, not other treatments. A separate distinctiveness task includes other compounds. Save the exact query and candidate IDs so pairing is auditable.

Report per-query AP, compound-level mAP, positive/control counts, effect magnitude, replicate similarity and distinctiveness as separate outputs. The established mAP framework motivates this comparison. [S3, S4]

Specify effect magnitude as RMS of the compound consensus's robust standardized deviations from controls, including consensus aggregation and feature-count handling. Define ties and zero-vector behavior. A missing score is not zero.

Evaluate null calibration with synthetic known-null fixtures and real control-only pseudo-groups, respecting experimental grouping and the exchangeability required by each randomization. Use nonzero Monte Carlo p-values, document numerical resolution, and correct the declared testing family where valid. Never choose the best p-value across analysis variants. If calibration is inadequate, label descriptive results and do not claim controlled discovery rates.

### Output and gate

Outputs: tested `src/` modules, QC ledger, feature dictionary, normalization logs, score tables and methods documentation.

Gate: valid inputs yield finite interpretable outputs or explicit missing-result reasons; toy metric cases and leakage tests pass; exclusions and statistical assumptions are inspectable.

## 7. Stage 4: Execute the robustness experiments

| Experiment | Assistant implementation | Required interpretation |
|---|---|---|
| Normalization sensitivity | Compare the three prespecified variants on the same cohort and fixed features | Quantify score/rank changes; variants are not independent experiments |
| Plate influence | Remove one physical plate and repeat the applicable development pipeline | Show every fold and worst influence; do not label this alone independent validation |
| Feature-channel ablation | Remove dependencies for DNA, ER, RNA, AGP or mitochondria, including cross-channel features | This removes extracted measurements, not physical stains or segmentation effects |
| Feature-count control | Repeat matched-size random feature removals | Separate channel-specific loss from reducing dimension count |
| QC/context sensitivity | Analyze documented anomalies and contextual differences separately | Dose, cell line and exposure changes are not automatically technical failures |

Use seeded runs and recorded configurations. Preserve the all-channel primary result. Channel sensitivity is evidence to interpret, not an automatic reliability penalty.

Output: compound-level robustness tables, rank-movement plots and a generated diagnostic report.

Gate: all variants run on known eligible inputs and record retained features, comparison counts, excluded units and failure reasons.

## 8. Stage 5: Lock and run the evaluation

Freeze cohort eligibility, physical-unit split, feature rules, metrics, candidate ranking, thresholds and endpoints before inspecting test outcomes. Save a dated configuration and checksums. Metadata/schema inspection is allowed for feasibility; test treatment outcomes cannot guide tuning. [S6]

Compare three development-only rankings:

- Effect magnitude alone.
- Ordinary all-channel replicate mAP.
- A transparent exploratory robustness summary, initially the median mAP across the prespecified all-channel normalization variants, with dispersion and plate influence reported separately.

The summary is not a calibrated probability and is not assumed to improve performance. Use the same eligible compounds and shortlist size for each method. The proposed shortlist rule is k = max(1, ceiling(0.20 * N)), where N is the common set of compound-condition groups assessable for all compared rankings and the locked endpoint. Report all exclusions and coverage differences. Break exact ranking ties by stable compound-condition ID, never test outcome; report the number of boundary ties and sensitivity when extensive ties matter. The rule must be frozen before evaluation.

Primary evaluation: same-condition replicate retrieval in independently held-out preparations under the frozen reference pipeline. Report full-population rank association, equal-size shortlist performance, paired differences and appropriate uncertainty. Resample independent experimental units, not correlated cells or profile pairs. If there are too few independent units, display all fold outcomes and limit inference.

External transportability: audit exact overlap and feature semantics before attempting direct cross-dataset profile comparisons. When necessary, compute comparable within-dataset endpoints rather than force incompatible raw measurements together. Distinguish held-out plates, independent preparation batches and repeat microscope acquisitions throughout.

Audit well-position confounding. Consistency across plates does not eliminate a repeated position effect. Show this limitation when the design cannot disentangle compound identity and position.

If a coding bug is discovered after evaluation, document an amended run. Do not silently retune to improve results. A negative result is a legitimate final scientific result.

Outputs: frozen split/configuration, baseline comparisons, uncertainty outputs, `reports/validation.md`, and an explicit evidence-level statement.

Gate: headline conclusions match the experimental independence, sample size and observed results. No superiority claim unless supported.

## 9. Stage 6: Attach real image evidence

Download only selected genuine public microscopy fields, identified by analyzed well, plate, acquisition, site and channel. Use a deterministic image-selection rule and display replicate grids rather than handpicking the strongest-looking field.

Use actual channel metadata, control-derived common display scaling, recorded crop/pseudocolor settings and verified dimensions. Preserve source originals separately from display derivatives. Add scale bars only when physical pixel size is documented. The pilot does not supply segmentation masks/bounding boxes, so do not invent them. [S1]

Make clear when the numerical profile represents the whole well but the screen shows one field. Missing image access must produce a visible unavailable state, not a substitute biological image.

Outputs: image manifest, image-processing code, public display derivatives and provenance links.

Gate: the image-to-measurement join is tested, display transformations are recorded, and no synthetic or AI-generated images appear as experimental evidence.

## 10. Stage 7: Build and test the application

Implement the Python analysis separately from the interface. Use a Streamlit research application with validated precomputed result bundles for fast exploration. Also generate a browser-openable HTML evidence report/demo so inspecting the project does not require the user or recruiter to install Python.

The HTML view is explicitly a viewer for already computed results, not a browser replacement for the scientific pipeline. GitHub Pages can host static HTML/CSS/JavaScript, while a live Streamlit application needs Python-capable hosting. [S7, S8]

Views:

1. Dataset/QC: design, controls, replication, exclusions and data coverage.
2. Compound explorer: searchable compounds and separate evidence dimensions.
3. Robustness: normalization comparisons, plate influence and channel contribution.
4. Images: real treated/control fields linked to the analyzed wells.
5. Validation/methods: baselines, held-out results, formulas, provenance and limitations.

Provide CSV/JSON exports and compound HTML reports generated from the same result artifacts. Show units, denominators, missingness and uncertainty. Avoid misleading green pass/fail badges or unsupported biological explanations.

Test navigation, filters, downloads, graph labels, image mapping, missing-data handling and fresh startup in the available browser/runtime. Capture high-resolution screenshots from the actual working program after the scientific outputs are available.

Outputs: app source, static evidence viewer/report, export functions and screenshots.

Gate: displayed values equal the analysis artifacts, core navigation/export works, and missing results are clearly explained.

## 11. Stage 8: Reproducibility, review and release

Run unit, integration, scientific-invariant and browser tests. Repeat a clean build using the pinned environment where infrastructure permits. Record actual OS/runtime coverage; do not claim Mac or cross-browser testing that was not performed.

Important test groups:

| Group | Required checks |
|---|---|
| Data | Bad joins, duplicates, missing annotations, malformed files, hash failures |
| Preprocessing | Zero MAD/SD, near-zero scale, all-missing features, held-out leakage |
| Pairing | No self-match, wrong dose, condition mixing, reimage leakage |
| Metrics | Hand-calculated AP, ties, null calibration, correct denominators |
| Robustness | Complete channel dependencies, repeatable random masks, fold bookkeeping |
| Results | UI/CSV/JSON/HTML consistency and traceable artifacts |
| Reproduction | Repeat run with fixed seeds and declared numeric tolerance |
| Publication | No private data, secrets, broken paths or missing licenses |

The assistant's own tests and methods review are not independent peer review. External scientist feedback is optional and useful, but it is not a required task for Alyan or something to claim without obtaining it.

Deliver a ready-to-upload repository containing source, configurations, manifests, a compact real-data result bundle, tests, generated reports, screenshots, README, methods, data card, limitations, dependency lock, citations, upstream notices and an appropriate code license. Keep raw large data and caches out of Git; include a verified downloader/reproduction workflow.

Write a case study using findings that actually emerge. Include negative and insufficient-evidence results. Do not claim that every desired example category exists. Include a short technical walkthrough covering what the project does, how it was validated and the limits of the claims. Describe upstream methods and AI-assisted implementation honestly.

Prepare the final folder before publication so the initial GitHub upload need not involve repeated folder repair. Maintain the analysis decision log, actual run logs, source provenance and validation freezes in the release even if the public repository starts from one prepared snapshot. The user prefers one clean initial portfolio upload, not a fabricated research history. Private/public runner use may create genuine development commits; explain this distinction and do not suppress scientific provenance to optimize a commit count. Subsequent useful commits are normal.

Outputs: tested release ZIP, static report/demo, complete source repository, validation evidence, publication guide and technical walkthrough.

Gate: scientific and software completion criteria pass; any remaining external-evaluation or infrastructure limitation is prominent. A running interface alone is not completion.

## 12. Repository layout

```text
cell-painting-hit-reliability/
├── README.md
├── LICENSE
├── THIRD_PARTY_NOTICES.md
├── CITATION.cff
├── pyproject.toml
├── dependency lockfile
├── .gitignore
├── configs/
├── manifests/
├── src/cellpainting_reliability/
├── app/
├── tests/fixtures/
├── results/demo/
├── reports/
├── docs/
│   ├── data-card.md
│   ├── methods.md
│   ├── limitations.md
│   ├── environment-and-access.md
│   ├── publishing.md
│   └── technical-walkthrough.md
└── assets/screenshots/
```

Names may be refined during implementation, but the release will have one consistent documented structure. Include `.github/workflows/` if an external runner is used, `scripts/` for acquisition/reproduction/checkpoint commands, and `docs/execution-plan.md`, `BUILD_STATUS.md`, `NEXT_AGENT.md`, `DECISIONS.md`, `RUN_MANIFEST.json`, `CHECKSUMS.sha256`, and `BLOCKERS.md` for handoff. The public dataset license does not replace the license of reused software. Verify each source and retain its notices. [S1, S2]

## 13. Checkpoint and status protocol

At substantial stopping points, save code, configurations, manifests, compact results, test output and `BUILD_STATUS.md`. The status file records:

- Completed and verified work.
- Work implemented but not yet executed.
- Failed checks and unresolved questions.
- Actual commands and resource use.
- The next execution step and any genuine user dependency.

Provide downloadable checkpoints so work is recoverable if the execution environment resets. A link, file or task will not be described as created or tested until the tools establish it. Long jobs must be resumable; no claim of unattended work after a response.

## 14. What Alyan actually needs to do

**Not required:** collect wet-lab data; choose or clean datasets; complete a programming course; write the analysis; install scientific tools on the Mac to enable initial development; supply clinic data; find an external supervisor; or perform the project testing instead of the assistant.

**Potential infrastructure handoff:** if this session's data/dependency access issue persists, authorize a suitable connected runner or transfer the precisely specified bundle. The assistant prepares all technical instructions and files.

**Publication under personal accounts:** authorize GitHub access or upload the final prepared folder; sign in and approve hosting settings where necessary. Never paste passwords or tokens into chat. Deployment and scientific validation are separate tasks.

**Before claiming the work professionally:** read the supplied walkthrough and review how personal contributions, public data, established methods and AI assistance are described. This is not a prerequisite for construction, but the portfolio should be defensible in an interview.

Optional: try the final interface and give usability feedback. Browser/OS-specific behavior on an untested device may need a screenshot or error log.

## 15. Completion checklist

- Real public data, exact provenance and validated identity joins.
- Appropriate biological grouping and explicit physical replication.
- Reference comparison and tested core metrics.
- Executed normalization, plate-influence and channel-feature analyses.
- Appropriate held-out evaluation, with evidence strength stated accurately.
- Baselines, null checks where justified, uncertainty and negative results.
- Genuine microscopy evidence tied to analyzed wells.
- Working interface, consistent exports and high-resolution screenshots.
- Runnable reproduction instructions, dependency versions and test evidence.
- Correct sources/licenses and a clean publication package.

No overall scientific result, performance gain, journal acceptance or recruiter outcome is guaranteed. The commitment is to execute the build, test the claims, document what the evidence supports, and expose any unfinished gate rather than conceal it.

## 16. Self-contained acquisition and dependency reference

### 16.1 Official data entry points and initial scope

These are planning references, not a request for the user to download them now. They do not constitute a complete, verified per-object transfer manifest.

| Material | Official entry point or path | When needed |
|---|---|---|
| Cell Painting Gallery | https://registry.opendata.aws/cellpainting-gallery/ and https://github.com/broadinstitute/cellpainting-gallery | Stage 0 inventory |
| Public bucket browser | https://cellpainting-gallery.s3.amazonaws.com/index.html | Stage 0 object discovery |
| Pilot source/reproduction workflow | https://github.com/jump-cellpainting/2024_Chandrasekaran_NatureMethods_CPJUMP1 | Stages 0-2 |
| Exact experiment-metadata path | `benchmark/output/experiment-metadata.tsv` within the pilot repository | Stages 0-1 |
| Metadata file browser link | https://github.com/jump-cellpainting/2024_Chandrasekaran_NatureMethods_CPJUMP1/blob/main/benchmark/output/experiment-metadata.tsv | Stages 0-1 |
| Compound layouts and annotations | Pilot `metadata/` plus https://github.com/jump-cellpainting/JUMP-Target | Stage 1 |
| Candidate pilot raw aggregates | Discover actual CSV objects under `s3://cellpainting-gallery/cpg0000-jump-pilot/source_4/workspace/backend/2020_11_04_CPJUMP1/` | One file for Stage 0; accepted complete plates for Stage 1 |
| Pilot normalized reference profiles | Pilot `profiles/`; check any Git LFS pointers and retrieve actual content | Stage 2 |
| Published benchmark workflow | Pilot `benchmark/1.calculate-map-cp.ipynb`, supporting helpers, environment and output files | Stage 2 |
| Image-to-well metadata | Pilot `load_data_csv/` and acquisition metadata | Stage 1 manifest; Stage 6 images |
| Protocol dataset | `cpg0001-cellpainting-protocol`; https://github.com/carpenter-singh-lab/2023_Cimini_NatureProtocols | Stage 1 feasibility before assigning development/test roles |
| Imaging systems | `cpg0002-jump-scope`; https://doi.org/10.1002/cyto.a.24786 | Stage 1 feasibility and declared acquisition/transportability analysis |

Initial pilot plate candidates are `BR00117015`, `BR00117016`, `BR00117017`, `BR00117019`, all in `2020_11_04_CPJUMP1`. Do not infer missing per-file suffixes, profile dimensions, compressed sizes, or checksums from this list. Do not use normalized matrices as raw inputs to an alternative normalization experiment. No single-cell SQLite databases or bulk raw-image downloads are needed for the initial feature-based phase. This is a planned use of published measurements, not a fallback to mock data. [S1]

The final Stage 0/1 acquisition manifest must replace mutable `main` source URLs with pinned source revisions when feasible, record dataset object versions when available, and handle Git LFS objects correctly. A GitHub ZIP may omit submodule contents or contain pointers rather than data; verify actual content rather than trusting an archive name.

### 16.2 Specialist packages and environment ownership

Install into the runtime that will execute the analysis, not arbitrarily on the user's Mac. This table is a dependency plan, not a tested lockfile. The assistant selects a Python version supported by all required packages, resolves dependencies, tests imports and reference behavior, then produces platform-appropriate pinned files. Upstream reproduction may require its own legacy environment.

| Package/tool | Purpose | Official reference |
|---|---|---|
| `pycytominer` | Normalization, aggregation utilities and feature processing | https://github.com/cytomining/pycytominer |
| `copairs` | Metadata-restricted pair construction and AP/mAP | https://github.com/cytomining/copairs |
| `numpy`, `pandas`, `scipy` | Arrays, tables and numerical/statistical calculations | https://numpy.org/ ; https://pandas.pydata.org/ ; https://scipy.org/ |
| `pyarrow` | Columnar feature/result storage | https://arrow.apache.org/docs/python/ |
| `scikit-learn` | Consistent fitted transforms, diagnostic comparisons and grouped evaluation utilities | https://scikit-learn.org/stable/ |
| `tifffile`, `Pillow` | Read genuine microscopy TIFFs and generate documented display images | https://pypi.org/project/tifffile/ ; https://pillow.readthedocs.io/ |
| `streamlit` | Research interface | https://docs.streamlit.io/ |
| `plotly`, `matplotlib` | Interactive and static diagnostic plots | https://plotly.com/python/ ; https://matplotlib.org/ |
| `pytest`, `pytest-cov` | Unit/integration tests and coverage | https://docs.pytest.org/ ; https://pytest-cov.readthedocs.io/ |
| `playwright` plus compatible browser binaries | Actual browser/UI tests and screenshots | https://playwright.dev/python/ |
| `PyYAML`, `jsonschema` | Human-readable configurations and validation | https://pyyaml.org/ ; https://python-jsonschema.readthedocs.io/ |
| `boto3` or AWS CLI v2 | Anonymous selective S3 inventory/downloads, only where needed | https://boto3.amazonaws.com/v1/documentation/api/latest/index.html ; https://docs.aws.amazon.com/cli/ |
| Git and, only for affected assets, Git LFS | Source/version and large-object retrieval | https://git-scm.com/ ; https://git-lfs.com/ |

Official installation commands for the two specialist core packages are `pip install pycytominer` and `pip install copairs`; these are discovery commands, not the final scientifically validated environment. Do not ask the user to run them now. Exact versions, compatible transitive packages and hashes are resolved in Stage 0 and frozen in Stage 2. [S4, S16]

Retain upstream license notices and record whether a dependency is runtime, analysis, development-only or optional. Inspect upstream scripts before executing them. No paid package or AI API is currently selected. If a necessary component cannot be installed, first resolve its environment; do not silently drop its validation or mislabel a reimplementation as the original package.

## 17. Predetermined tests, locked data and statistical decision register

### 17.1 What is predetermined and what is not

Three distinct layers are required:

1. **Known-answer unit fixtures:** tiny synthetic or manually specified inputs with expected numeric answers established before running the implementation. Include perfect retrieval, deliberately interleaved positives, all-tie similarity, zero vectors, degenerate controls, bad joins and prohibited pairings. Example: with two relevant profiles at ranks 1 and 3 and no ties, AP is `(1 + 2/3) / 2 = 5/6`. These fixtures test arithmetic and logic, not biological efficacy.
2. **Published reference reproduction:** exact upstream input artifacts and source revision, the documented task and metric, expected published/upstream-computed outputs where available, and stated tolerances. If exact golden result files do not exist for our subset, run the preserved upstream calculation and record a cross-implementation comparison; do not claim equality to unpublished paper numbers.
3. **Real biological holdout:** an eligible public experimental panel selected using design/identity metadata before examining treatment performance. Its results are unknown outcomes to measure, not preset answers. Report independence level and whether prior public analyses of that panel informed our method. It is a prespecified public-data evaluation, not a prospectively collected or independently blinded clinical trial.

Use full eligible plate/control populations in the final analysis. A smoke-test subset is never evidence that the full robustness grid, null calibration or evaluation ran.

### 17.2 Decisions to record before opening test treatment outcomes

Complete `configs/evaluation.yaml` and `DECISIONS.md` with:

- Primary biological condition and stable grouping key, including concentration units.
- Physical preparation, well, plate, batch, acquisition and reimage identities; separate technical from biological replication.
- Full development/test membership; the independent unit used for each endpoint and confidence statement.
- Deterministic QC exclusions, plate-failure criteria and the minimum usable-control/replicate policy, justified from the design and reference workflow.
- Exact feature mask, training-only imputation method, missingness/redundancy rules and DMSO calibration protocol.
- Normalization formulas, MAD scaling constant, epsilon or exclusion handling, and treatment of zero or near-zero scales.
- Similarity measure and numerical precision. Use the verified upstream measure for reference reproduction. Choose and justify any different primary measure using development data only.
- Positive/negative candidate definitions, well-position restrictions, query weighting and ties. For the project endpoint, use score-threshold/tie-aware AP with a tested definition; a stable sorting artifact must not inflate scores when every similarity is equal. Report upstream differences separately.
- AP definition: for non-tied rankings, average precision at relevant positions; for tied scores, freeze a threshold-grouped or explicitly tie-averaged formulation and check it against known cases. No positives/negatives or undefined similarities produce an explicit missing result, not a numeric success.
- Compound-level weighting, preferably equal physical-plate weighting of query averages when eligible plate replicate counts differ, plus a sensitivity report for the upstream convention.
- Consensus aggregation (mean or median), exact RMS effect formula `sqrt(mean(z_j**2))` on the declared features and controls, and the baseline ranking direction.
- The fixed shortlist rule from Stage 5, missing-result handling, comparison population, and which rank association is primary.
- Number and generation rule of matched-size feature removals; preserve shared mask IDs across compounds and record exact retained features. Start development diagnostics with 100 seeded draws; finalize the number by a prespecified Monte Carlo precision check on development only.
- Null/exchangeability design, resampling unit, Monte Carlo draw count/stopping rule, multiplicity family and adjustment.
- Confidence interval interpretation and what happens when too few independent units exist.
- Resource plan, exact software versions/source hashes and random seeds.

These are necessary design decisions, not unknowns the agent should ask the user to solve. Proposed starting settings can be revised on development data, with reasons recorded. After freeze, changes require an amended analysis clearly separated from the primary evaluation.

### 17.3 Null calibration and uncertainty safeguards

Proposed exploratory starting point: 10,000 null draws, with nonzero Monte Carlo p-values `(1 + exceedances) / (1 + draws)`. Verify whether this resolution supports the final multiplicity family and whether the sampling scheme meets exchangeability under the experimental blocks. Do not independently permute correlated profiles as if they were biological replicates.

Use real control pseudo-groups with calibration controls kept separate or cross-fitted, plus synthetic tests with deliberately imposed signals/artifacts. Match eligible candidate counts and pairing rules; show calibration plots and their denominators. Raw mAP is sensitive to the retrieval universe, so do not interpret different positive/control compositions as directly comparable without a justified common/null-calibrated endpoint.

The proposed primary significance criterion is adjusted q < 0.05 within the frozen primary compound-condition family, only when calibration supports such inference. Document the dependence assumptions for Benjamini-Hochberg and consider the more conservative Benjamini-Yekutieli sensitivity check. Do not choose the smallest p-value across preprocessing variants. [S14]

Resample physical experimental units at the appropriate level, with paired comparisons preserved. Compound-level resampling addresses generalization across compounds, not uncertainty across laboratories. State the estimand and do not use thousands of pairwise correlations as independent samples. With few independent plates/batches, show all folds and limit formal interval claims.

No fixed threshold or number of permutations guarantees validity. If calibration or power is inadequate, diagnose it, obtain additional appropriate public experiments where possible, and seek approval for any narrower descriptive release. A missing evaluation is not a completed negative evaluation.

### 17.4 Broader methodological review

Validate channel dependencies against actual extraction settings, including cross-channel correlations and segmentation-derived effects. Do not claim a physical stain omission. [S15]

Assess positional confounding and batch/biological-condition interactions before attributing score changes to treatment. Advanced batch correction is not a default requirement; add it only when justified by the design and evaluation, checking preservation of biology rather than merely visual mixing. [S21]

Before release, perform a methods review separate from UI/code review. The assistant's review is not independent peer review. A paid or volunteer bioimage-analysis/statistics reviewer is optional, potentially valuable for stronger scientific assurance, and requires explicit consent and an agreed scope. No wet-lab confirmation or external approval may be implied without obtaining it.

## 18. Staged execution, resource capacity and blocker escalation

### 18.1 Suggested turn structure

Use multiple stage-specific prompts, not one giant build request. The intended sequence is Stage 0 access, Stage 1 cohorts, Stage 2 reference, Stage 3 engine, Stage 4 robustness, Stage 5 evaluation, Stage 6 images, Stage 7 app, Stage 8 final reproduction/release.

After each stage, give a short user-facing summary: what actually ran; passed/failed gates; results and limitations; any essential user action; and the next proposed stage. Link the checkpoint and wait. Heavy stages can be divided into resumable substages without changing the scientific plan.

Example start instruction for later use only:

> Execute Stage 0 only using Cell_Painting_Execution_Plan_v3.md. Verify data/dependency access and a usable runtime. Do not begin biological analysis. If blocked, prepare the smallest exact handoff or cloud-runner package and stop. Provide the checkpoint and gate evidence.

Example continuation instruction:

> Read the attached version 3 plan and latest checkpoint. Verify its manifest and BUILD_STATUS. Execute only the next authorized stage named in NEXT_AGENT. Preserve evaluation freezes and stop at the gate.

### 18.2 Capacity is measured, not assumed

The assistant can develop the specified code and orchestrate computational tests using available tools, but chat context, process duration, RAM, disk, network and external permissions are finite. No unlimited bandwidth, permanent filesystem, overnight unattended run or all-platform testing is promised.

At Stage 0, measure practical limits. At Stage 1, estimate matrix, similarity and image sizes. At Stage 3, measure representative performance before the full grid. Use chunking/streaming, cached immutable inputs and deterministic per-plate/per-variant runs. Avoid quadratic all-by-all matrices across the whole Gallery when only eligible candidate pairs are needed.

Do not silently lower permutation precision, remove unfavorable compounds, omit difficult folds or shrink independent evaluation to meet a runtime limit. Either preserve the analysis through batching/checkpoints or request an appropriate runtime/cost decision.

| Possible blocker | First action by assistant | User action only when necessary |
|---|---|---|
| Raw download fails | Verify allowed routes; prepare exact inventory and runner fallback | Run prepared workflow or upload exact public files |
| Missing/incompatible packages | Resolve/pin environment or separate reference environment | Authorize runtime or upload prepared platform-matched bundle |
| Chat process timeout/reset | Checkpoint, split work and rehydrate from hashes | Return latest checkpoint or approve external job |
| RAM/disk/time too small | Measure and batch; compare suitable runtime | Approve capped paid compute if needed |
| Inadequate independent replicates/metadata | Audit another legitimate public cohort | Approve a materially narrower scientific claim only if no suitable alternative is found |
| Reference mismatch | Isolate preprocessing, grouping and metric differences | No technical work required; unresolved scientific error blocks release |
| Missing source images or mapping | Resolve actual acquisition metadata and bounded source assets | Transfer exact files if access is the only barrier |
| Unverified scientific interpretation | Restrict conclusions to measurements; seek appropriate review | Optional independent-review decision |
| Account publication restrictions | Inspect supported connector actions; prepare complete upload/runner files | Sign in, grant permission or click the specified account action |

### 18.3 Every checkpoint must be self-contained

Checkpoint contents:

- This plan as `docs/execution-plan.md`.
- `BUILD_STATUS.md`: stage status using NOT_STARTED / RUNNING / BLOCKED / PASSED / FAILED / IMPLEMENTED_NOT_RUN, with paths to evidence.
- `NEXT_AGENT.md`: current stage, exact next action, commands, runtime route, expected outputs, evaluation lock status and essential user dependency.
- `BLOCKERS.md`: errors, attempted routes, consequences and chosen/proposed resolution.
- `DECISIONS.md`: scientific and engineering choices, reasons, version/date, and whether each predates holdout exposure.
- `RUN_MANIFEST.json`: run IDs, source/configuration/code hashes, dependencies, source locations, actual commands, resource use and artifact outputs.
- `CHECKSUMS.sha256`: integrity inventory of included artifacts.
- All code/configurations/tests written so far; actual logs, compact results, current source/object manifest, and exact instructions to reacquire excluded large public files.

Use relative paths in the project, environment parameters for external storage, and actual verified paths in handoffs. Never use an invented sandbox download link. Do not call plans, placeholders, generated fixture data or screenshots a successful analysis.

### 18.4 Budget policy

Current spending authorization: **zero until a specific expense is approved**. The user is willing to consider paid tools when the benefit is substantial.

Compare free and paid options when there is a meaningful bottleneck. Recommend paid resources for materially better memory, runtime, persistence, hosting reliability or independent review, not because paid software is inherently more rigorous. Provide the provider/product, verified current price/currency, expected duration, estimated compute/storage/transfer cost, maximum approved spend, expiry/shutdown and free alternative. Recheck prices and quotas at purchase time.

No premium coding editor, proprietary assay package or paid AI model subscription is currently required by this design. A larger runtime cannot fix confounded or missing biological experiments.

## 19. Current status and unresolved decisions

At issuance of version 3:

- Planning revision and public documentation review only are complete.
- The user has NOT authorized project execution or a new environment preflight.
- The earlier network/dependency failure is unresolved and has not been retested in this revision.
- The final raw-data transfer list, object sizes/hashes, lockfile, runtime route and cloud account access are NOT yet verified.
- Pilot plate IDs are prespecified candidates; full cohort qualification and external overlap/independence are pending Stage 1.
- Exact upstream golden outputs, endpoint parameters and statistical precision are to be established and frozen at the stated gates.
- No biological result, benchmark superiority, full-test pass, external-review outcome or deployable app is claimed.

A new agent should begin by awaiting or confirming permission for Stage 0, not by treating this document as evidence that Stage 0 already passed.

## Source references and provenance

The scientific stage structure is carried forward from the user-uploaded `Cell_Painting_Execution_Plan_v2(1).md`. Version 3 embeds the necessary candidate-cohort details and adds the operational controls above. Package versions, object lists and live account limits must be verified at execution. Literature supports methods and datasets; proposed thresholds, budget controls, checkpoint formats and work division are project design decisions, not literature findings.

[S1] CPJUMP1 author-maintained repository; data levels, metadata, workflow, benchmark and licenses: https://github.com/jump-cellpainting/2024_Chandrasekaran_NatureMethods_CPJUMP1

[S2] Cell Painting Gallery AWS registry; anonymous public access, bucket and data licensing: https://registry.opendata.aws/cellpainting-gallery/

[S3] Kalinin et al. (2025), A versatile information retrieval framework for evaluating profile strength and similarity: https://www.nature.com/articles/s41467-025-60306-2

[S4] copairs reference implementation and tests: https://github.com/cytomining/copairs

[S5] Pycytominer normalization documentation: https://pycytominer.readthedocs.io/en/stable/pycytominer.normalize.html

[S6] scikit-learn, Common pitfalls and recommended practices: https://scikit-learn.org/stable/common_pitfalls.html

[S7] GitHub Pages hosting model: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages

[S8] Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

[S9] Pilot experiment metadata: https://github.com/jump-cellpainting/2024_Chandrasekaran_NatureMethods_CPJUMP1/blob/main/benchmark/output/experiment-metadata.tsv

[S10] Cell Painting protocol optimization author repository: https://github.com/carpenter-singh-lab/2023_Cimini_NatureProtocols

[S11] Cell Painting Gallery catalogue: https://github.com/broadinstitute/cellpainting-gallery

[S12] Tromans-Coia et al. (2023), Assessing the performance of the Cell Painting assay across different imaging systems: https://doi.org/10.1002/cyto.a.24786

[S13] Pycytominer feature selection: https://pycytominer.readthedocs.io/en/stable/pycytominer.feature_select.html

[S14] SciPy false discovery control: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html

[S15] Cimini et al. (2023), Optimizing the Cell Painting assay for image-based profiling: https://www.nature.com/articles/s41596-023-00840-9

[S16] Pycytominer installation and source: https://github.com/cytomining/pycytominer

[S17] GitHub-hosted runners, resources and repository-dependent charging: https://docs.github.com/en/actions/reference/runners/github-hosted-runners

[S18] GitHub Actions job, artifact, concurrency and rate limits: https://docs.github.com/en/actions/reference/limits

[S19] GitHub Actions manual workflow launch: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow

[S20] GitHub Actions artifact retrieval: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts

[S21] Arevalo et al. (2024), Evaluating batch correction methods for image-based cell profiling: https://www.nature.com/articles/s41467-024-50613-5

[S22] scikit-learn, grouped cross-validation: https://scikit-learn.org/stable/modules/cross_validation.html
