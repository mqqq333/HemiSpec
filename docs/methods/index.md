# Methods overview

HemiSpec documentation separates method origin from project-specific extensions.

## Original framework

Wang et al. 2024 introduced a cross-hemispheric deep generation network framework for estimating one hemisphere from its contralateral counterpart and deriving neuroanatomical specificity maps from actual-reconstructed residuals.

## HemiSpec extension

The current HemiSpec handedness manuscript applies this reconstruction-derived framework to a behavioral lateralization question. It evaluates whether ANS/RNS features capture subtle structural information related to handedness beyond conventional GMV asymmetry indices.

## Metrics

- **ANS**: absolute neuroanatomical specificity, the absolute residual between actual and reconstructed gray-matter maps.
- **RNS**: relative neuroanatomical specificity, the residual normalized by local gray-matter magnitude.

ANS and RNS are metrics. HemiSpec is the software and documentation project that packages workflows around them.