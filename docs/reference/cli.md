# CLI reference

The preferred public command is:

```text
hemispec
```

The subcommands below were checked against the current toolkit interface on 2026-09-05. Re-check them before public release if the toolkit source or package name changes.

## Current subcommands

```text
hemispec quickstart      run the public-safe synthetic smoke test
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

Current `main` can pre-download the DGN checkpoints tracked by Git LFS:

```bash
hemispec models --install
```

If this is skipped, `workflow`, `infer`, `run`, and the GUI download the DGN checkpoints from the repository's `main` Git LFS media on first model use.

The CLI still supports `--with-classifier`, but it is not a working installation recommendation at present because required `feature_names.csv` media URLs return HTTP 404. Obtain classifier assets from a local Git LFS checkout and use `--classifier-model-dir` or `HEMISPEC_CLASSIFIER_MODEL_DIR`; see the [known limitation](../data-and-models.md#current-cache-download-boundary).

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

The released classifier accepts only features from its compatible Glasser 1.5 mm atlas: homologous labels `1..180` on the left and `1001..1180` on the right. A custom atlas may be used for ROI export, but not with the released classifier.

## Reporting

There is not yet a standalone `report` subcommand. Reporting should be treated as a planned feature until implemented.

ANS/RNS and the cross-hemispheric DGN framework originate from Wang et al. (2024); see [Citation](../citation.md).
