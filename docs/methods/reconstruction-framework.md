# Reconstruction framework

The reconstruction framework estimates each anatomical hemisphere from its contralateral counterpart. Instead of treating lateralization as a direct left-right subtraction, it learns a nonlinear mapping between hemispheres and then studies what remains unexplained by that mapping.

## Conceptual steps

1. Split preprocessed gray-matter maps into left and right hemispheres.
2. Train direction-specific reconstruction models:
   - left-to-right reconstruction
   - right-to-left reconstruction
3. Apply trained models to held-out participants.
4. Pair each actual target hemisphere with its reconstructed counterpart.
5. Compute residual maps and downstream summaries.

## Model family

The HemiSpec manuscript follows the DGN/context-encoder-style reconstruction strategy used in the original Patterns framework. The public documentation should describe the model as a cross-hemispheric DGN unless a specific implementation page is discussing architecture details.

## What HemiSpec adds

HemiSpec packages the reconstruction outputs into reproducible workflows: map computation, ROI summaries, validation, reporting, and downstream phenotype analyses.