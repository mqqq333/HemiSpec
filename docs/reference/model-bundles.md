# Model bundles

A HemiSpec model bundle should package the files needed to run DGN inference reproducibly.

## Suggested bundle layout

```text
model-bundle/
  manifest.yml
  weights/
    left_to_right.pth
    right_to_left.pth
  preprocessing.md
  metrics.csv
  checksums.txt
```

## Manifest fields

- Model direction or bilateral model set.
- Architecture identifier.
- Training data summary.
- Expected input shape, affine, orientation, and voxel size.
- Preprocessing assumptions.
- Weight filenames and checksums.
- License and citation notes.

Large model weights should not be committed directly to the repository unless there is an explicit release decision.