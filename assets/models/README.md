# Model bundles

Do not commit trained model weights to the source tree.

Expected local layout for development:

```text
assets/models/dgn/<bundle-name>/
assets/models/hemisphere_classifier/<bundle-name>/
```

Public releases should provide model bundles through an external artifact channel
with checksums and a manifest.
