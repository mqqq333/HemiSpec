# HemiSpec

**HemiSpec: Reconstruction-derived Hemispheric Specificity** is a software and workflow project for studying hemisphere-specific structure from cross-hemispheric reconstruction residuals.

HemiSpec is not intended to rename the ANS/RNS metrics. Instead, it provides a clearer public home for the software, documentation, tutorials, and reproducible workflows built around those metrics.

## Workflow overview

<figure markdown="span">
  ![HemiSpec workflow overview](assets/figures/hemispec-workflow-overview.svg){ width="100%" }
  <figcaption>Public-safe workflow schematic aligned with the manuscript Fig. 1B sequence: Input GM, Reconstruction, Difference analysis, and Hemisphere-specific metrics.</figcaption>
</figure>

## What HemiSpec does

HemiSpec is being organized around a workflow that starts from preprocessed gray-matter maps and produces reconstruction-derived hemispheric specificity outputs:

1. Run or import cross-hemispheric DGN reconstructions.
2. Pair each actual hemisphere with its contralaterally reconstructed counterpart.
3. Compute absolute and relative neuroanatomical specificity maps.
4. Summarize voxelwise maps into ROI-level features.
5. Validate reliability and hemisphere-specific information.
6. Use the features in downstream analyses such as handedness classification.

## Method boundary

The ANS/RNS metrics and the original cross-hemispheric DGN framework come from Wang et al. 2024 in *Patterns*. HemiSpec builds on that foundation.

The current HemiSpec manuscript extends the framework to handedness-related structural variation. It uses handedness as a behavioral lateralization test case and asks whether reconstruction-derived features capture information beyond conventional GMV asymmetry indices.

## Current status

This site is the unified public home for HemiSpec. The public command and import path are `hemispec`.

## Where to start

- Read [Installation](installation.md) for the documentation and toolkit environment.
- Read [Quick start](quickstart.md) for the planned command sequence.
- Read [Software overview](software-overview.md) for the package, CLI, GUI, and compiled-app layers.
- Browse [Manuscript figures](manuscript-figures.md) for approved figure previews.
- Read [Methods](methods/index.md) for the original framework and the handedness extension.
- Read [Release artifacts](release-artifacts.md) for the CLI/PyPI/compiled-app release contract.
- Read [Data and models](data-and-models.md) before trying to publish data, model weights, or manuscript results.

<figure markdown="span">
  ![HemiSpec study design overview](assets/figures/hemispec-study-design.png){ width="100%" }
  <figcaption>HemiSpec organizes cross-hemispheric reconstruction, reconstruction-derived ANS/RNS specificity maps, validation, ROI summaries, and downstream lateralization analyses into one workflow.</figcaption>
</figure>

---

<p class="site-credits">
  Made with <a href="https://squidfunk.github.io/mkdocs-material/" target="_blank" rel="noopener">Material for MkDocs</a>.
</p>


