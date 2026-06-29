# Methods overview

HemiSpec documentation separates method origin from project-specific extensions.

## Original framework

Wang et al. 2024 introduced a cross-hemispheric deep generation network framework for estimating one hemisphere from its contralateral counterpart and deriving neuroanatomical specificity maps from actual-reconstructed residuals.

## HemiSpec extension

The current HemiSpec handedness manuscript (Ma & Ma, in preparation) applies this reconstruction-derived framework to a behavioral lateralization question. It evaluates whether ANS/RNS features capture subtle structural information related to handedness beyond conventional GMV asymmetry indices, using T1-weighted MRI data from seven public datasets.

## Metrics

- **ANS**: absolute neuroanatomical specificity — the absolute residual between actual and reconstructed gray-matter maps.
- **RNS**: relative neuroanatomical specificity — the residual normalized by local gray-matter magnitude.

ANS and RNS are metrics. HemiSpec is the software and documentation project that packages workflows around them.

## Downstream analyses

ANS/RNS maps and ROI-level features support a range of downstream analyses:

- **Age and sex effects** — how reconstruction-derived specificity varies across demographic groups.
- **Hemisphere identity classification** — distinguishing left from right hemispheres from ROI-level ANS/RNS features.
- **Behavioral phenotypes** — associating specificity features with lateralized behaviors such as handedness.
- **Disease vs. control comparisons** — comparing ANS/RNS profiles between patient groups and healthy controls.
