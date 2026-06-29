# CLI reference

The preferred public command is:

```text
hemispec
```

The subcommands below were checked against the current toolkit interface on 2026-06-29. Re-check them before public release if the toolkit source or package name changes.

## Current subcommands

```text
hemispec models          list or pre-download released trained DGN model bundles
hemispec infer           run trained DGN inference on preprocessed GM maps
hemispec compute         compute ANS/RNS maps from actual and reconstructed GM maps
hemispec run             run DGN inference followed by ANS/RNS computation
hemispec workflow        run bilateral DGN and generate ANS/RNS outputs
hemispec trt             test-retest reliability validation
hemispec specificity     structural specificity validation
hemispec hemi-classify   ROI-level hemisphere-classifier validation
```

## Command naming

Use `hemispec` for the command-line interface and `hemispec-gui` for the graphical interface.

## Model asset prefetch

Wheel/PyPI installs can pre-download the released DGN checkpoints and classifier bundle:

```bash
hemispec models --install --with-classifier
```

If this is skipped, `workflow`, `infer`, `run`, and the GUI download the released DGN checkpoints automatically on first model use.

## ROI outputs

ROI export is currently exposed through options on `compute`, `run`, and `workflow`. For `workflow`, ROI export is optional and can be skipped with `--no-roi-table`; classifier validation is opt-in with `--run-classifier` and requires ROI features.

```text
--roi-atlas
--roi-out-csv
--roi-label-table
--roi-stat
--no-roi-table
--run-classifier
```

There is not yet a standalone `roi` subcommand.

## Reporting

There is not yet a standalone `report` subcommand. Reporting should be treated as a planned feature until implemented.
