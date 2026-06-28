param(
    [string]$Python = "python",
    [string]$WorkDir = ""
)

$ErrorActionPreference = "Stop"

if (-not $WorkDir) {
    $WorkDir = Join-Path $PSScriptRoot "workdir"
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )
    Write-Host "[HemiSpec synthetic] $Label"
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Label"
    }
}

Invoke-Step "Generating public-safe toy NIfTI maps..." {
    & $Python (Join-Path $PSScriptRoot "make_synthetic_nifti.py") --out-dir $WorkDir
}

$actualGlob = Join-Path $WorkDir "actual\*.nii.gz"
$predGlob = Join-Path $WorkDir "recon\*_PRED_LR_full.nii.gz"
$outDir = Join-Path $WorkDir "outputs\compute"
$atlas = Join-Path $WorkDir "atlas\toy_atlas.nii.gz"
$labels = Join-Path $WorkDir "atlas\toy_labels.csv"
$roiCsv = Join-Path $outDir "toy_roi_summary.csv"

Invoke-Step "Running hemispec compute on synthetic inputs..." {
    & $Python -m hemispec compute `
        --actual-glob $actualGlob `
        --predicted-glob $predGlob `
        --out-dir $outDir `
        --save-subject-maps `
        --roi-atlas $atlas `
        --roi-label-table $labels `
        --roi-out-csv $roiCsv
}

Write-Host "[HemiSpec synthetic] Done. Key outputs:"
Write-Host "  $outDir"
Write-Host "  $roiCsv"
