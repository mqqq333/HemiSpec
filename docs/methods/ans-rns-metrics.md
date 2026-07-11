# ANS and RNS metrics

ANS and RNS were introduced by Wang et al. (2024) as reconstruction-derived measures of hemispheric specificity.

## Original definitions

For the actual target-hemisphere GM value `Act_i` and its reconstructed value `Recon_i`, the original paper defines:

```text
ANS_i = abs(Act_i - Recon_i)
RNS_i = abs((Act_i - Recon_i) / (Act_i + Recon_i))
```

- **ANS:** absolute neuroanatomical specificity.
- **RNS:** relative neuroanatomical specificity.

ANS represents the amount of actual–reconstructed difference. RNS represents the proportion of local signal expressed by that difference.

## HemiSpec numerical implementation

HemiSpec computes:

```text
ANS = abs(GM - recon)
RNS = abs(GM - recon) / (abs(GM) + abs(recon) + eps)
```

The implementation also requires finite values and applies a configurable valid-GM threshold (`0.15` by default). The absolute-value denominator and small `eps` stabilize division when reconstructed values are near zero or contain small negative numerical values. For non-negative GM and reconstruction values, the implementation approaches the published expression as `eps` approaches zero.

This implementation detail should be reported when exact numerical reproducibility matters.

## Interpretation limits

ANS/RNS are reconstruction-error-derived quantities. They are not direct measurements of neuronal function, causal lateralization, or tissue pathology. Interpretation depends on preprocessing quality, model domain, reconstruction behavior, masking, site/scanner effects, and downstream validation.

## Citation boundary

Cite Wang et al. (2024) for the metric framework. Cite HemiSpec separately for the software implementation when a public software record is available. See [Citation](../citation.md).
