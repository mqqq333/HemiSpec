# Methods overview

HemiSpec documentation separates the published method from the software implementation and downstream extensions.

## Published framework

Wang et al. (2024) introduced a cross-hemispheric deep generation network that predicts one hemisphere from the contralateral hemisphere and derives voxel-wise measures from the actual–reconstructed difference.

HemiSpec uses the metric names consistently as:

- **ANS — absolute neuroanatomical specificity:** the absolute amount of reconstruction-derived hemisphere-specific signal.
- **RNS — relative neuroanatomical specificity:** the reconstruction-derived difference expressed relative to local actual/reconstructed magnitude.

See [Citation](../citation.md) for the complete reference.

## HemiSpec implementation layer

HemiSpec provides:

- a documented T1-to-GM FSL preprocessing path;
- reusable released DGN inference bundles;
- bilateral reconstruction and ANS/RNS export;
- optional ROI aggregation;
- optional hemisphere-classifier and TRT validation;
- CLI, GUI, Python API, tests, documentation, and release tooling.

These software components should not be described as the origin of the DGN or ANS/RNS method.

## Downstream analyses

ANS/RNS maps and ROI features can support demographic analyses, hemisphere-identity classification, behavioral-phenotype associations, and disease–control comparisons. Each downstream analysis requires its own design, confound control, validation, and citation; the existence of a HemiSpec command does not by itself establish scientific validity for a new cohort.
