# Research utilities

This folder contains project-owner/developer utilities used to reproduce or
extend local experiments around HemiSpec. They are intentionally kept out of the
package entry-point surface.

These scripts may assume local data layouts, approved private inputs, or optional
model/classifier dependencies. Keep generated outputs outside git and promote
reusable logic into `src/hemispec/` before exposing it through the public CLI,
Python API, or GUI.

- `train_hemisphere_classifier_modes.py` — trains/evaluates hemisphere
  classifier modes from derived feature tables.
- `recompute_icbmval_gan_roi_and_eval.py` — recomputes local validation ROI
  summaries and evaluation tables from approved GAN outputs.
