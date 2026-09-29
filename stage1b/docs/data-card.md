# Data card: Stage 1B qualification checkpoint

**Purpose:** determine whether public experimental cohorts support the proposed Cell Painting reliability project. This is not a completed scientific analysis or a clinical application.

## Available measurements

Four real unnormalized A549 pilot well-aggregate matrices are present in the verified parent archive, 1,536 wells in total. Per plate there are 260 ordinary treatment wells, 60 positive-control compound wells and 64 explicitly annotated DMSO negative controls. The frozen annotation has 306 non-negative-control sample IDs; display-name counts must not substitute for sample identity.

Cell context is parental A549, 48-hour exposure, baseline 1,000 seeded cells per well, 5 micromolar compound dose, first acquisition, and one experiment/batch. Dose and seeding evidence are from published methods. Negative controls are not assigned a compound dose.

## Unit of observation and intended grouping

An aggregate row is a well, not an independently observed single cell. Physical plates and preparation groups are explicit. Repeated acquisition of the same physical well stays in the same group. Most pilot compounds occupy one repeated coordinate per plate, limiting separation of phenotype from recurring position effects.

## Feature scope

There are 5,792 compartment-prefixed measurement columns. This includes five fluorescence channels, three brightfield image types and technical/spatial families. The schema dictionary is preliminary; no fitted feature selection, imputation or normalization was performed. A source prefix alone is not a scientific inclusion rule.

## Missingness and images

All four pilot matrices were structurally complete with finite numeric measurements in the audited prefixed columns. This is not a viability or image-quality certification. There are 122,870 deduplicated original fluorescence image references covering 24,574 fields. Two nominal field-site references are absent, while all wells retain aggregates. No actual image pixels were examined. Old directory strings are not verified current download locations.

## External candidate status

Stain5 Thermo (4 plates), Reagent1 Thermo (4 plates), Stain4 Standard (3 plates), and scope PE confocal/BIN1/1Plane (4 acquisition labels) are selected from design metadata. Their full profile bytes are pending targeted acquisition. Protocol applied compound doses, scope exposure and material aliases, and Reagent1 preprocessing provenance remain open.

Each MOA layout describes 90 labels with four wells each and 24 controls. Only 82 have publicly matched BRD/chemical keys; Compound1-8 remain undisclosed identities. No cross-study chemical identity is inferred from their generic labels. Protocol and scope panels cannot be pooled across differing seeding or other conditions as matched replicates.

## Intended and prohibited use

Suitable now: planning and bounded reference preparation on the existing pilot, design audits and transparent provenance. Not suitable now: independent-batch generalization claims, predicted drug efficacy, fitted reliability models, formal discovery-rate claims or statements that the planned evaluation has passed.

## Files and preservation

Keep `stage1-acquisition.zip` and the Stage 1B checkpoint together. Raw public measurements are excluded from the small checkpoint and public update package, with exact parent hashes and paths recorded. The new runner selects exact listing/tree entries, preserves bytes and records transfer evidence. Upstream notices accompany packaged source metadata. Final release licensing and attribution remain explicit release tasks.
