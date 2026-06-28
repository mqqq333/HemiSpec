# Atlas assets

Do not commit large atlas NIfTI files directly to the source tree.

Document atlas source, license, resolution, checksum, and expected local path
before enabling examples that depend on an atlas.


## Local Glasser layout

HemiSpec expects the local Glasser bundle at:

```text
assets/atlases/glasser/MNI_Glasser_HCP_v1.0_1p5mm.nii.gz
assets/atlases/glasser/Glasser_label_index_mapping.xlsx
```

Only `README.md` and `ASSET_MANIFEST.template.yml` are intended for git. The
actual atlas and label table files are local assets and should be distributed
through an explicit release channel after source/license approval.
