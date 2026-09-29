# Stage 1B test scope

The executed offline suite has 67 tests. It covers strict encodings and BOMs, explicit legacy metadata decoding, delimiter/row validation, safe paths/checksums, exact metadata joins, explicit control identification, anonymous labels, condition/plate/position restrictions, profile structure, no treatment-value evaluation on external data, bounded gzip expansion, complete/failing HTTP fixtures, transient retries, source ETags, Git blob and LFS hashes, optional/required source failures, metadata conflicts and final artifact recovery.

It also checks the 32-target/15-profile manifest against the actual archived S3 listing and Git tree entries, all four 384-well MOA templates, 82 known and eight undisclosed identities, and the known listed transfer sizes. Synthetic fixtures use intentionally non-biological values to demonstrate that external profile inspection does not compute treatment performance. A fixture with nonnumeric feature strings can pass schema-only inspection by design; this is not a promise that it would pass later scientific numeric QC.

Actual original inputs were checked separately: 693 file-manifest entries, 588 source receipts, 16 prior-review entries and all four pilot matrices. The new suite is distinct from the previous 54 Stage1A tests. Do not add their counts together and claim a single end-to-end biological test run.

The target acquisition workflow has not been run remotely in this checkpoint. Test logs from the next GitHub run are required. Python compilation, shell syntax, packaged file hashes and a Git core.autocrlf=true checkout roundtrip are checked before shipment. The latter simulates line-ending behavior on Linux, not a complete Windows execution test.

No Stage 2 reference reproduction, normalization comparison, reliability scoring, null-calibration experiment, cross-batch performance evaluation or user-interface test is included in these results.
