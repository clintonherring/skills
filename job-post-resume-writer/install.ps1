# Thin wrapper for Windows PowerShell: find Python 3 and run install.py with the same arguments.
#   powershell -ExecutionPolicy Bypass -File install.ps1 [--check|--upgrade|--uninstall|--ide cursor ...]
$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$candidates = @(
    @{ exe = "py";      args = @("-3") },
    @{ exe = "python3"; args = @() },
    @{ exe = "python";  args = @() }
)
foreach ($c in $candidates) {
    if (Get-Command $c.exe -ErrorAction SilentlyContinue) {
        & $c.exe @($c.args) -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $c.exe @($c.args) (Join-Path $dir "install.py") @args
            exit $LASTEXITCODE
        }
    }
}
Write-Host "Python 3.8 or newer is required. Install it from https://www.python.org/downloads/windows/"
Write-Host "(tick 'Add python.exe to PATH' in the installer), then run this script again."
exit 1
