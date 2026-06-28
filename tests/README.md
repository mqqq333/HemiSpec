# Tests

The test suite focuses on public API, CLI-compatible computation paths, and small synthetic arrays. Tests must not depend on private neuroimaging files, local model weights, or generated output folders.

Run:

```bash
python -m pytest
```

When adding a feature, prefer a synthetic or tiny generated fixture over committing binary data.
