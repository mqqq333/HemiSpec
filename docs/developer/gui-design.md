# GUI design

The HemiSpec GUI is a compact `customtkinter` launcher over the same bilateral workflow exposed by the Python API and `hemispec workflow` CLI command. It is not a separate analysis implementation.

## Design goals

- expose only decisions required for routine ANS/RNS generation;
- keep advanced model, threshold, suffix, and validation parameters in the CLI/API;
- show the equivalent CLI command for reproducibility;
- report runtime/model readiness before a long run;
- keep logs, cancellation, and output-folder access visible.

## User-visible workflow

The current GUI contains six functional cards:

1. **Input GM maps** — a directory or glob resolving to preprocessed `*_GM_masked.nii.gz` files.
2. **Output workspace** — the destination for voxel maps, tables, validation results, and optional intermediates.
3. **Setup status** — shallow checks for PyTorch, both DGN directions, optional atlas files, and the optional classifier bundle.
4. **Optional ROI table** — atlas NIfTI and label-table paths.
5. **Optional validation** — hemisphere classification, TRT reliability, and intermediate-output retention.
6. **Run controls** — equivalent CLI command, run/stop controls, logs, copy command, and open-output actions.

Hemisphere-classifier validation remains opt-in. Enabling it also enables ROI export because the classifier consumes ROI features.

## Encapsulated defaults

The GUI intentionally hides:

- DGN checkpoint paths and direction-specific bundle names;
- device selection;
- GM and inference thresholds;
- reconstruction clipping and suffix rules;
- classifier mode and model path;
- TRT session regexes and mask parameters.

These values are defined in the GUI state-to-config adapter and remain available through the CLI/API for advanced or study-specific use.

## Shared execution path

```text
GUI state
  -> make_workflow_config(...)
  -> BilateralWorkflowConfig
  -> run_bilateral_workflow(...)
  -> voxel_maps/ + tables/ + optional validation/
```

The generated CLI preview is derived from the same workflow configuration. Contract tests under `tests/test_gui_contract.py` protect this alignment.

## Runtime behavior

The GUI performs only shallow setup checks before execution; it does not load large checkpoints during status refresh. A background worker runs the workflow so the interface can stream logs and accept cancellation. Cancellation is cooperative and checked between major workflow stages.

## Maintenance rules

- Keep visible fields synchronized with `WORKFLOW_VISIBLE_FIELDS`.
- Keep hidden defaults synchronized with CLI defaults and contract tests.
- Do not add a GUI-only computation path.
- Treat new advanced parameters as CLI/API options unless routine users must decide them.
- Update the GUI user guide and screenshots whenever visible cards or labels change.

ANS/RNS and the cross-hemispheric DGN framework originate from Wang et al. (2024); see [Citation](../citation.md).
