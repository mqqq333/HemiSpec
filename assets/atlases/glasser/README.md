# Glasser atlas local bundle

This directory is a local lookup location for optional Glasser atlas assets:

```text
assets/atlases/glasser/
  MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
  Glasser_label_index_mapping.xlsx
```

Only this README and `ASSET_MANIFEST.template.yml` are intended for the public source branch. The atlas NIfTI and label table are local assets and must not be committed until their source, license, checksum, compatibility, and redistribution approval are documented.

HemiSpec can resolve approved local files from this directory or from:

```text
HEMISPEC_GLASSER_ATLAS
HEMISPEC_GLASSER_LABEL_TABLE
```

Complete the manifest before distributing any atlas bundle.
