param(
    [string]$Python = "",
    [switch]$SkipExe,
    [switch]$SkipGuiSmoke
)

$ErrorActionPreference = "Stop"

if (-not $Python) {
    if ($env:PYTHON) {
        $Python = $env:PYTHON
    } else {
        $Python = "python"
    }
}

$PythonParts = @($Python -split "\s+" | Where-Object { $_ })
$PythonExe = $PythonParts[0]
$PythonArgs = @()
if ($PythonParts.Count -gt 1) {
    $PythonArgs = $PythonParts[1..($PythonParts.Count - 1)]
}

function Invoke-PythonStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Invoke-NativeStep $Label { & $PythonExe @PythonArgs @Arguments }
}

function Invoke-NativeStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host "[HemiSpec] $Label"
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Label"
    }
}

function Test-GuiStarts {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [int]$Seconds = 8
    )

    if ($SkipGuiSmoke) {
        Write-Host "[HemiSpec] Skipping GUI smoke: $Label"
        return
    }

    Write-Host "[HemiSpec] GUI smoke: $Label"
    $process = Start-Process -FilePath $FilePath -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds $Seconds
    if ($process.HasExited) {
        throw "GUI smoke failed: $Label exited early with code $($process.ExitCode)."
    }
    Stop-Process -Id $process.Id -Force
}

Invoke-PythonStep "Ensuring build backend is available..." @("-m", "pip", "install", "--upgrade", "build")
Invoke-PythonStep "Building lightweight wheel..." @("-m", "build", "--wheel")

$Wheel = Get-ChildItem -Path "dist" -Filter "hemispec_toolkit-*.whl" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Wheel) {
    throw "No hemispec_toolkit wheel found under dist/."
}

Invoke-PythonStep "Installing built wheel for local entry-point check: $($Wheel.Name)" @("-m", "pip", "install", "--force-reinstall", $Wheel.FullName)
Invoke-PythonStep "Checking module CLI..." @("-m", "hemispec", "--help")
Invoke-NativeStep "Checking console CLI..." { & hemispec --help }

Invoke-PythonStep "Installing GUI optional dependency for smoke/build..." @("-m", "pip", "install", "customtkinter>=5.2")
$GuiEntry = (Get-Command hemispec-gui -ErrorAction Stop).Source
Test-GuiStarts "hemispec-gui console entry" $GuiEntry

if (-not $SkipExe) {
    # The editable install is only for PyInstaller's source checkout analysis after
    # the wheel entry points have already been checked above.
    Invoke-PythonStep "Installing PyInstaller/dev tools..." @("-m", "pip", "install", "-e", ".[dev,gui]")
    Invoke-PythonStep "Building CLI executable from hemispec.spec..." @("-m", "PyInstaller", "--clean", "--noconfirm", "hemispec.spec")
    Invoke-NativeStep "Checking compiled CLI executable..." { & ".\dist\hemispec.exe" --help }
    Invoke-PythonStep "Building GUI executable from hemispec_gui.spec..." @("-m", "PyInstaller", "--clean", "--noconfirm", "hemispec_gui.spec")
    Test-GuiStarts "compiled hemispec_gui.exe" ".\dist\hemispec_gui\hemispec_gui.exe"
}

Write-Host "[HemiSpec] Release artifacts are under dist/."
Write-Host "[HemiSpec] Default EXE specs do not bundle local assets/ or torch. Add only approved model/atlas bundles beside the release folder with ASSET_MANIFEST.md."
