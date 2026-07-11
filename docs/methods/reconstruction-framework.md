# Reconstruction framework

The published framework estimates a target hemisphere from its contralateral counterpart. Instead of treating lateralization only as a direct left–right subtraction, the model learns a nonlinear cross-hemispheric mapping and quantifies what the reconstruction does not explain.

## Published conceptual sequence

1. Convert T1-weighted MRI into MNI152 1.5 mm `*_GM_masked.nii.gz` gray-matter maps; see [Input and preprocessing](../input-preprocessing.md).
2. Split/crop the maps into left and right hemisphere inputs.
3. Train direction-specific context-encoder-style DGN models:
   - left-to-right reconstruction;
   - right-to-left reconstruction.
4. Apply the trained model to held-out participants.
5. Compare each reconstructed target hemisphere with the actual target hemisphere.
6. Compute ANS and RNS from the actual–reconstructed difference.

This framework originates from Wang et al. (2024); see [Citation](../citation.md).

## HemiSpec runtime sequence

HemiSpec distributes trained generator checkpoints and runs both reconstruction directions. For each preprocessed whole-brain GM input, the software crops the configured source hemisphere, predicts the target hemisphere, pastes the prediction into the whole-volume grid, and computes directional ANS/RNS maps. It then merges the target-side outputs into bilateral left/right maps.

## Method boundary

- **Published contribution:** cross-hemispheric DGN formulation and ANS/RNS framework.
- **HemiSpec contribution:** operational preprocessing documentation, model discovery/download, reusable inference code, bilateral export, ROI summaries, optional validation, and user interfaces.
- **Study-specific responsibility:** acquisition harmonization, preprocessing quality control, exclusion criteria, confound handling, statistical analysis, and external validation.
