# Glasser atlas local bundle

This directory is the default local lookup location for the HemiSpec Glasser
atlas assets:

```text
assets/atlases/glasser/
  MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
  Glasser_label_index_mapping.xlsx
```

The current local copies have been placed here for development and validation,
but the large/data files remain ignored by git. Do not commit the NIfTI or label
table directly unless the project owner makes an explicit public release
decision and the asset source/license is documented.

HemiSpec resolves these files automatically from the project root. Users can also
override them with:

```text
HEMISPEC_GLASSER_ATLAS
HEMISPEC_GLASSER_LABEL_TABLE
```

Before a public model-enabled release, fill in the companion manifest with
source, license, checksum, and compatibility notes.
