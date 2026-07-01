# Methods overview

HemiSpec documentation separates method origin from project-specific extensions.

## Original framework

Wang et al. 2024 introduced a cross-hemispheric deep generation network framework for estimating one hemisphere from its contralateral counterpart and deriving neuroanatomical specificity maps from actual-reconstructed residuals.

## Downstream task layer

HemiSpec extends the reconstruction-derived framework by treating ANS/RNS maps as reusable voxel-wise and ROI-level representations for downstream task analysis. The method layer is framed broadly so the same outputs can support demographic, hemisphere-identity, behavioral-phenotype, and disease-comparison analyses.

## Metrics

- **ANS**: absolute neuroanatomical specificity — the absolute residual between actual and reconstructed gray-matter maps.
- **RNS**: relative neuroanatomical specificity — the residual normalized by local gray-matter magnitude.

ANS and RNS are metrics. HemiSpec is the software and documentation project that packages workflows around them.

## Downstream analyses

ANS/RNS maps and ROI-level features support a range of downstream analyses:

- **Age and sex effects** — how reconstruction-derived specificity varies across demographic groups.
- **Hemisphere identity classification** — distinguishing left from right hemispheres from ROI-level ANS/RNS features.
- **Behavioral phenotypes** — associating specificity features with behavioral or lateralization phenotypes.
- **Disease vs. control comparisons** — comparing ANS/RNS profiles between patient groups and healthy controls.
