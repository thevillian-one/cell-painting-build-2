# Stage 1B: scientific cohort qualification

## Decision and scope

The available-data review has been executed. The four-plate A549 pilot is accepted **only for a bounded reference reproduction and within-experiment analysis**, subject to the explicit position and annotation limits below. **Full Stage 1 has not passed.** External cohorts require the targeted profiles and unresolved experimental metadata before acceptance. Stage 2 has not been started or authorized.

This is experimental-design and identity qualification, not a claim that a compound's phenotype reproduces. No normalization, AP/mAP calculation, effect ranking, robustness experiment, held-out performance analysis, image-pixel interpretation, or application development was performed.

## 1. Input integrity

The supplied `stage1-acquisition.zip` has SHA-256 `e435e4bf38fdb5b7fd8ebf7d46f1d71b16adc8b1c8711686a58f5cbeb050fd24`.

This review independently verified all 693 acquisition manifest entries and all 588 source-file size/hash records. It also verified the 16 entries in the prior review checkpoint. See `evidence/input-verification.json` and `logs/input-verification.log`. Checksums establish consistency with the supplied manifests, not independent proof of biological validity. Source revisions and Git blob records remain in the original archive.

The original source files remain unchanged. The former broad Latin-1 reader happened to preserve this source collection, as documented in the earlier review. New Stage 1B code uses strict UTF-8/BOM handling, with an explicit CP1252 override only for the archived protocol master table. It never replaces undecodable characters silently.

## 2. Pilot: exact well and compound assignments

Source: the pilot author's repository at revision `56845c7d4dc322652952783d91dae0ffef47829f`, its barcode-to-platemap mapping, frozen annotation table, and experimental metadata. The published methods supply the applied 5 micromolar compound concentration and baseline seeding of 1,000 cells per well [P1]. These values are not inferred from the compound-library concentration field.

| Attribute | Verified result |
|---|---|
| Plates | BR00117015, BR00117016, BR00117017, BR00117019 |
| Experimental context | A549 parental cells; 48 hours; baseline density; no antibiotics; first imaging; no listed anomaly |
| Applied compound dose | 5 micromolar, from published experimental methods |
| Physical wells | 384 per plate, 1,536 total |
| Ordinary treatment wells | 260 per plate |
| Source-designated positive-control compound wells | 60 per plate |
| Explicit negative-control wells | 64 per plate, 256 total |
| Frozen non-negative-control sample IDs | 306 |
| Frozen non-negative-control InChIKeys | 306 |
| Unique display names | 302 |
| Preparation grouping | One experiment/batch, not four independent laboratories or preparation campaigns |

The negative controls require the blank-sample annotation explicitly designated `control/negcon`; merely having DMSO as solvent does not make a treated well a negative control. DMSO controls are not assigned a fictitious 5 micromolar compound dose.

Four display names occur under more than one source sample/chemical key: dexamethasone, thiostrepton, BVT-948 and ME-0328. These remain distinct source samples. The count above describes this exact frozen table, not a reconciled pharmacological drug count. The paper describes a different headline compound count, and source revisions/identity conventions must not be silently conflated.

A comparison against the acquired current JUMP-Target annotation found **125 changed InChIKeys for the same sample IDs**. The review does not establish why each changed. Keep the frozen study annotations for reproduction, preserve the discrepancy table, and require explicit reconciliation before using newer chemical structures for a chemical-level claim. See `manifests/annotation-version-conflicts.tsv` and `pilot-name-collisions.tsv`.

## 3. Pilot replication and well-position confounding

The four complete raw matrices have identical 5,794-column headers, 5,792 compartment-prefixed columns, and no duplicate/missing well positions. Full numeric-completeness checks were repeated only for this existing pilot development material. No malformed rows, missing/nonfinite measurement cells, or nonnumeric measurement cells were detected. This is not an image-quality or phenotype-reliability finding.

There are 292 sample IDs at one fixed position per plate, and 14 at two fixed positions per plate. Hence much of the design repeats compound identity at the same well coordinate. A cross-plate match alone cannot separate treatment from a recurring positional effect.

Design-only counts, with symmetric cross-plate restrictions for positive and negative candidates:

| Count | Value |
|---|---:|
| Compound-exposed query wells | 1,280 |
| Directed same-sample cross-plate candidate pairs | 4,176 |
| Directed treatment-to-control candidate pairs | 245,760 |
| Queries retaining a positive at a different well coordinate | 112 |
| Sample IDs assessable under that extra position restriction | 14 |

These are combinatorial counts from the well design. No similarities or AP values were computed. `pilot-pair-counts.tsv` and `pilot-different-position-pair-counts.tsv` record per-query denominators.

**Accepted role:** reference reproduction and explicitly limited within-experiment replicate assessment. **Not accepted role:** independent-batch or interlaboratory generalization. Report the position limitation, use the restricted subset where applicable, and do not manufacture cross-position replication.

## 4. Measurement provenance: five fluorescence channels are not the entire matrix

The retained pilot extraction pipeline names five fluorescence channels plus Brightfield, HighZBF and LowZBF. Of the 5,792 prefixed columns, **2,277 have explicit brightfield-channel dependencies**, including mixed-channel measurements. Other prefixed columns include Location, Parent, Children and Number families. Therefore a compartment prefix is not sufficient to define the final biological feature set.

`manifests/pilot-feature-dictionary.tsv` records schema tags, measurement families and explicit channel tokens. These tags are not fitted feature selection or a final mask. The source pipeline specifies nucleus segmentation from CorrBlue and cell segmentation from RNA; retained measurements can therefore retain segmentation dependencies even when channel-specific features are later removed.

The source file's format version and DateRevision are recorded by the pipeline. Do not treat a filename/revision string as a fully verified CellProfiler environment. Stage 2 must distinguish the upstream reproduction feature set from any later five-fluorescence-channel endpoint and verify extraction semantics. No such preprocessing was executed here.

## 5. Image-to-well references

The acquired Stage 1A image-reference table has 589,776 rows. It combines overlapping source mapping files and illumination-function references. Restricting to original fluorescence fields and deduplicating exact plate/well/site/channel references yields:

- 122,870 original fluorescence image references;
- 24,574 field positions;
- two missing nominal field-site references: BR00117015/A17/site 5 and BR00117017/L06/site 14.

All pilot wells still have aggregate measurement rows. Missing individual image-reference sites do not automatically exclude their whole wells. No conflicting original filename mapping was found for the same field/channel.

The compact reference manifest is `pilot-fluorescence-image-references.tsv.gz`. Illumination functions are excluded from biological image examples. Original directory strings are upstream paths, **not verified current S3 download URLs**. Stage 6 must resolve actual Gallery objects and verify image bytes before displaying them. No image pixels were fetched or interpreted in Stage 1B.

## 6. U2OS JUMP-MOA identity templates

The selected frozen protocol layouts and scope layout each describe 384 wells: 90 source compound labels with four wells per label, plus 24 negative controls. Only **82 source compounds have public BRD identifiers and nonblank matching chemical keys**. Eight labels, Compound1 through Compound8, have undisclosed chemical identity.

Preserve those eight labels for within-source bookkeeping, but do not declare them the same chemical across studies just because the labels match. The conservative cross-study identity overlap is the 82 matching public sample IDs with matching frozen keys. The pilot and these MOA templates have 14 exact sample/key overlaps, but different cell types and applied dose contexts prevent treating that overlap as matched biological replication.

The protocol layout's `mmoles_per_liter=1.5` field is preserved as a source-library concentration. It is **not established as the final in-well assay dose**. No dilution factor has been invented. See `manifests/cross-cohort-identity-overlap.tsv`, `evidence/moa-layout-audit.json`, and the original archived maps.

## 7. Candidate external panels and selection rationale

Selections use experimental metadata and file availability, not treatment performance or qualitative conclusions from the master table. The master table's qualitative-conclusion column is excluded from the saved design audit.

| Candidate | Exact selection | Proposed role | Remaining qualification |
|---|---|---|---|
| Stain5 Thermo Standard | BR00120523-26; 4 plates; U2OS, 1,000 seeded cells, 48 hours, Thermo Fisher reagents, widefield, 1 plane, 2x2 binning | Development panel | Applied compound dose, raw bytes/schema, mapping and extraction provenance |
| Reagent1 Thermo Standard | CPJUMP001-004; 4 plates; U2OS, 1,000 seeded cells, 48 hours, matching nominal stain recipe and imaging settings | Separate-batch/site evaluation candidate | Applied dose, raw/annotated processing stage, exact experimental independence and feature semantics |
| Stain4 Standard | BR00116629-31; 3 plates; U2OS, 2,000 seeded cells, 48 hours | A separate 2,000-cell context; possible match to scope if other conditions agree | Applied dose, raw bytes/schema, matching conditions |
| Scope PE confocal, BIN1, 1Plane | CP_Broad_Phenix_C_BIN1_1Plane_P1-P4 | Acquisition/context transportability candidate | Raw bytes/schema, exposure duration, physical preparation aliases and processing provenance |

The protocol candidates have a matching nominal Thermo Fisher stain recipe in the selected master rows, but raw table compatibility and applied compound dose remain unverified. Stain5 PerkinElmer-reagent plates are not pooled with Thermo Fisher plates. Confocal reimages of the same barcodes and Stain4 HighExp reimages are aliases, not additional physical plates. All relevant aliases are recorded.

Reagent1's four selected profile paths are exact Git LFS entries in the protocol's pinned `pilot-data-public` submodule. Their 132-byte tree entries are pointers, not the full measurements. Those files are candidates for unnormalized annotated aggregates; a non-normalized filename does not establish their complete processing history. The targeted collector verifies the pointer's Git hash, then the LFS object's size and SHA-256. Full scientific acceptance still requires source-method review.

The scope paper specifies U2OS, approximately 2,000 seeded cells, 3 micromolar treatment, and shipment of prepared material for imaging [P2]. I have not established treatment duration or an exact preparation alias table for P1-P4 from the available sources. Within one PE acquisition prefix, 16 un-subsampled acquisition labels are conservatively grouped into four P-number groups. This prevents treating four settings per material label as 16 independent experiments, but is not proof of independently prepared material.

The scope source configuration contains `aggregate.perform: false` with `method: median`, while the paper describes mean aggregation. Because that operation is disabled in the configuration, neither entry alone settles the actual downloaded aggregate provenance. Flag this disagreement for review instead of assigning an aggregation method by assumption.

The Stain5 panel's 1,000-cell condition cannot be presented as matched-condition biological validation against the scope panel's approximately 2,000-cell condition. Instrument, preparation, protocol and acquisition differences may be mixed. The older Reagent1 batch would be a preparation/batch holdout candidate, not a prospective temporal test.

## 8. Targeted acquisition now prepared

The frozen manifest requests **15 profile files**: four Stain5, three Stain4, four scope PE and four Reagent1 LFS profiles. It also requests exact source metadata/pipelines and two optional primary-methods XML documents, 32 targets total.

The 11 S3 profile objects total **284,524,641 listed bytes**. Actual content sizes of the four LFS profiles must be read from their verified pointers. The runner has a 768 MiB total transfer cap, 64 MiB per-profile cap, two transient retries, a 30-minute collector deadline and a 45-minute job limit. It downloads no raw microscopy pixels and installs no scientific packages. These are bounded acquisition choices, not a reduction of the planned scientific benchmark.

All S3 keys were selected from the acquired official listing and all Git objects from pinned trees. Source bytes, ETags, hashes, retries and failures are recorded. New profile inspection exports explicit metadata and checks row identities; it does not summarize numerical treatment effects or fit anything using candidate evaluation wells.

The local download probe still failed name resolution. The targeted GitHub run has **not run yet**. Passing local fixtures is not evidence that all remote objects will be accessible. A green targeted acquisition still does not approve Stage 1 until the returned evidence is reviewed.

## 9. Conditions for full Stage 1 acceptance

Obtain and verify the requested profile bytes and source-method evidence. Reconcile applied protocol doses, scope duration/material aliases and Reagent1 processing history. Check actual cross-cohort header semantics and metadata joins. Retain source IDs and disclosed unknowns. Define valid comparison units and report usable comparison counts. Reject inappropriate roles without concealing limitations. If no eligible independent evaluation panel remains, investigate another public cohort or explicitly request a scope decision; do not silently declare the original goal complete.

**No Stage 2 execution is authorized by this report.**

## Sources and evidence

[P1] Chandrasekaran et al., 2024. DOI 10.1038/s41592-024-02241-6. Primary methods inspected through https://pmc.ncbi.nlm.nih.gov/articles/PMC11166567/ . Only the relevant methods facts were used; full article bytes have not been archived in this runtime.

[P2] Tromans-Coia et al., 2023. DOI 10.1002/cyto.a.24786. Primary methods inspected through https://onlinelibrary.wiley.com/doi/10.1002/cyto.a.24786 . Full article bytes have not been archived in this runtime.

All numerical design and integrity counts above were computed from the supplied archive. Reproduce them using `scripts/qualify_cohorts.py`. `manifests/audit-input-sources.json` records source paths/hashes and decoding. Original source revision IDs are in the parent archive's `manifests/repository-revisions.json`. Exact metadata rows and candidate object evidence are retained, not replaced with general scientific assumptions.
