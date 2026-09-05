# Citation

HemiSpec separates citations for the **original scientific method**, the **preprocessing software**, and the **HemiSpec software/downstream work**.

## Original cross-hemispheric DGN and ANS/RNS framework

Cite this paper whenever you use or describe the cross-hemispheric DGN reconstruction method, ANS, or RNS:

> Wang, G., Jiang, N., Ma, Y., Suo, D., Liu, T., Funahashi, S., & Yan, T. (2024). Using a deep generation network reveals neuroanatomical specificity in hemispheres. *Patterns, 5*(4), 100930. https://doi.org/10.1016/j.patter.2024.100930

HemiSpec uses the following public terminology consistently:

- **ANS:** absolute neuroanatomical specificity.
- **RNS:** relative neuroanatomical specificity.

HemiSpec documentation preserves those names and abbreviations.

## FSL preprocessing

The study `process_single_subject.sh` workflow and the packaged reorientation-enhanced variant use FSL, BET, FAST, and FLIRT. Cite the tools that materially support your preprocessing methods:

> Jenkinson, M., Beckmann, C. F., Behrens, T. E. J., Woolrich, M. W., & Smith, S. M. (2012). FSL. *NeuroImage, 62*(2), 782–790. https://doi.org/10.1016/j.neuroimage.2011.09.015

> Smith, S. M. (2002). Fast robust automated brain extraction. *Human Brain Mapping, 17*(3), 143–155. https://doi.org/10.1002/hbm.10062

> Zhang, Y., Brady, M., & Smith, S. (2001). Segmentation of brain MR images through a hidden Markov random field model and the expectation-maximization algorithm. *IEEE Transactions on Medical Imaging, 20*(1), 45–57. https://doi.org/10.1109/42.906424

> Jenkinson, M., & Smith, S. (2001). A global optimisation method for robust affine registration of brain images. *Medical Image Analysis, 5*(2), 143–156. https://doi.org/10.1016/S1361-8415(01)00036-6

## Glasser cortical parcellation

When using a Glasser/HCP-MMP atlas for ROI export or hemisphere classification, cite the original parcellation:

> Glasser, M. F., Coalson, T. S., Robinson, E. C., et al. (2016). A multi-modal parcellation of human cerebral cortex. *Nature, 536*, 171-178. https://doi.org/10.1038/nature18933

An MNI 1.5 mm NIfTI conversion is a derived atlas asset, not the original parcellation itself. Separately record its distributor/source URL, version or commit, retrieval date, MNI template, voxel size, conversion method, and label mapping. Do not attribute a conversion-specific integer convention, such as `1..180` and `1001..1180`, to the original paper. See [Data and models](data-and-models.md) for the local atlas requirements.

## HemiSpec software citation

For software use, cite the public HemiSpec release/archive record when available and retain the software version in the Methods section. Until an archival DOI is registered, use the repository `CITATION.cff` metadata together with the release tag and access date. For a current `main` source checkout, also report the exact commit from `git rev-parse HEAD`; the package version alone does not distinguish it from the archived `v0.1.0` release.

Do not replace the Wang et al. citation with a software citation: the original scientific method and the software implementation are separate contributions and should be credited separately.

## HemiSpec downstream manuscripts

A manuscript marked “in preparation” is not a stable public citation. Cite a HemiSpec downstream manuscript only after a public preprint, journal article, or archival record exists. Until then, describe the analysis as performed with HemiSpec and report the exact software version/commit.

## Suggested Methods wording

> T1-weighted images were converted to MNI152 1.5 mm gray-matter probability maps using an FSL-based workflow (BET, FAST, and FLIRT), thresholded at a GM probability of 0.15, and supplied to HemiSpec. Cross-hemispheric reconstruction and ANS/RNS computation followed the framework introduced by Wang et al. (2024). Software version, model bundle, thresholds, and optional validation settings were recorded for reproducibility.
