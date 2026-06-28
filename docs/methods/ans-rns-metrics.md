# ANS and RNS metrics

ANS and RNS are reconstruction-derived specificity metrics introduced in Wang et al. 2024. HemiSpec uses these metrics as the core representation for downstream analyses.

## Definitions

For an actual gray-matter map `GM` and its contralaterally reconstructed counterpart `recon`:

```text
ANS = abs(GM - recon)
RNS = abs(GM - recon) / (abs(GM) + abs(recon) + eps)
```

## Interpretation

ANS measures the absolute residual magnitude. RNS measures the relative residual magnitude after accounting for local gray-matter intensity.

Both metrics are usually computed voxelwise within a valid gray-matter mask and can then be summarized within atlas ROIs.

## Citation boundary

When using ANS/RNS as metrics, cite Wang et al. 2024. When using HemiSpec-specific handedness workflows, cite the HemiSpec manuscript or preprint once public.