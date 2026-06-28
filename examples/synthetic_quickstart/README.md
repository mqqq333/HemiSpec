# Synthetic quickstart

This example is the smallest public-safe HemiSpec compute demo. It generates
synthetic NIfTI maps, a toy atlas, and mock DGN-reconstruction outputs, then runs
`hemispec compute` with subject maps and ROI export.

The generated files are **not anatomical data** and must not be interpreted as
MRI-derived results. They only exercise the public CLI, file naming contract,
ANS/RNS computation, and ROI summary path.

## Run on Windows PowerShell

```powershell
cd <hemispec-toolkit-checkout>
python -m pip install -e .
powershell -ExecutionPolicy Bypass -File examples\synthetic_quickstart\run_synthetic_quickstart.ps1 -Python python
```

## Run on macOS/Linux

```bash
cd <hemispec-toolkit-checkout>
python -m pip install -e .
PYTHON=python bash examples/synthetic_quickstart/run_synthetic_quickstart.sh
```

Set `PYTHON` to the interpreter or environment where `hemispec-toolkit` is
installed. If omitted, the runner uses `python`.

## Generated layout

```text
examples/synthetic_quickstart/workdir/
  actual/                      toy actual GM maps
  recon/                       toy reconstructed maps ending in _PRED_LR_full.nii.gz
  atlas/                       toy atlas and CSV label table
  outputs/compute/             ANS/RNS group maps, subject maps, ROI CSV
```

The runner writes to `examples/synthetic_quickstart/workdir/`, which is ignored
by git. Running `make_synthetic_nifti.py` directly without `--out-dir` uses the
same ignored directory next to the script. Recreate it whenever you need a clean
demo.
