# CLI reference

The preferred public command is:

```text
hemispec
```

The subcommands below were checked against the current migration toolkit interface on 2026-06-28. Re-check them before public release if the toolkit source or package name changes.

## Current subcommands

```text
hemispec models          list discoverable local trained DGN model bundles
hemispec infer           run trained DGN inference on preprocessed GM maps
hemispec compute         compute ANS/RNS maps from actual and reconstructed GM maps
hemispec run             run DGN inference followed by ANS/RNS computation
hemispec workflow        run the bilateral HemiSpec workflow
hemispec trt             test-retest reliability validation
hemispec specificity     structural specificity validation
hemispec hemi-classify   ROI-level hemisphere-classifier validation
```

## Command naming

Use `hemispec` for the command-line interface and `hemispec-gui` for the graphical interface.

## ROI outputs

ROI export is currently exposed through options on `compute`, `run`, and `workflow`:

```text
--roi-atlas
--roi-out-csv
--roi-label-table
--roi-stat
```

There is not yet a standalone `roi` subcommand.

## Reporting

There is not yet a standalone `report` subcommand. Reporting should be treated as a planned feature until implemented.
