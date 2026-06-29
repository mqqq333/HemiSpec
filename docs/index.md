# HemiSpec

**HemiSpec: Reconstruction-derived Hemispheric Specificity** is a software and workflow project for studying hemisphere-specific structure from cross-hemispheric reconstruction residuals.

HemiSpec is not intended to rename the ANS/RNS metrics. Instead, it provides a clearer public home for the software, documentation, tutorials, and reproducible workflows built around those metrics.

## What is HemiSpec?

HemiSpec takes preprocessed gray-matter maps, compares each actual hemisphere with its contralaterally reconstructed counterpart, and produces reconstruction-derived ANS/RNS specificity maps plus optional ROI, classifier, and TRT validation outputs.

HemiSpec v0.1.0 is a first public beta for research use. The source repository includes reusable DGN checkpoints and hemisphere-classifier bundles through Git LFS. Wheel/PyPI and lightweight desktop installs keep the Python package small, but model-enabled CLI/GUI/API runs can auto-download the released weights into a user cache. Real neuroimaging data and generated outputs are not distributed.

<p markdown="span">
  [Download release](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0){ .md-button .md-button--primary }
  [Quick start](quickstart.md){ .md-button }
  [Assets and models](data-and-models.md){ .md-button }
</p>

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

This site is the unified public home for HemiSpec. The public command and import path are `hemispec`. HemiSpec v0.1.0 is published as a GitHub prerelease at [https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0](https://github.com/mqqq333/HemiSpec/releases/tag/v0.1.0).

## Where to start

- Read [Installation](installation.md) for the documentation and toolkit environment.
- Read [Quick start](quickstart.md) for the source-checkout GUI and CLI workflow.
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


