# Architecture Notes

HemiSpec Toolkit follows a layered architecture so that CLI, GUI, and future notebooks call the same tested core logic.

```text
User input / files
      |
      v
CLI (`hemispec`) or GUI (`hemispec-gui`)
      |
      v
Public API and workflow orchestration (`api.py`, `workflow.py`)
      |
      +--> DGN inference (`dgn_inference.py`, `dgn_model.py`)
      +--> ANS/RNS computation (`compute.py`, `similarity.py`)
      +--> ROI summarization (`roi.py`)
      +--> validation/reporting (`hemisphere_classifier.py`, `reports.py`, `plots.py`)
      |
      v
Outputs: maps, ROI tables, summaries, and figures
```

## Design principles

- **One implementation path:** CLI, GUI, and Python users should share the same core functions.
- **Explicit assets:** local atlases and models are discovered through `paths.py`, environment variables, or user-provided paths.
- **Small public package:** the wheel should not bundle private data, heavy weights, or generated outputs.
- **Stable names:** public code uses `hemispec`; ANS/RNS are metric names, not package names.
- **Reproducible examples:** public examples are synthetic unless an input is explicitly approved for redistribution.

## Current refactor boundaries

The current codebase is in a public-release migration stage. The largest interface modules (`cli.py` and `gui.py`) are kept stable for now to avoid changing runtime behavior during packaging. Future refactors should split them behind the same public entry points, with tests added before moving behavior.
