param(
    [string]$TargetTriple = "",
    [string]$ExecutableExtension = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$os = [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
$isWindowsHost = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)
$isMacHost = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::OSX)
$isLinuxHost = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Linux)

if ([string]::IsNullOrWhiteSpace($TargetTriple)) {
    if ($isMacHost) {
        if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") {
            $TargetTriple = "aarch64-apple-darwin"
        } else {
            $TargetTriple = "x86_64-apple-darwin"
        }
    } elseif ($isLinuxHost) {
        if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") {
            $TargetTriple = "aarch64-unknown-linux-gnu"
        } else {
            $TargetTriple = "x86_64-unknown-linux-gnu"
        }
    } else {
        $TargetTriple = "x86_64-pc-windows-msvc"
    }
}

if ([string]::IsNullOrWhiteSpace($ExecutableExtension) -and $isWindowsHost) {
    $ExecutableExtension = ".exe"
}

$oneFile = Join-Path $root "dist/civilai-backend$ExecutableExtension"
$oneDir = Join-Path $root "dist/civilai-backend/civilai-backend$ExecutableExtension"
$source = if (Test-Path $oneFile) { $oneFile } else { $oneDir }
$targetDir = Join-Path $root "dist\sidecars"
$target = Join-Path $targetDir "civilai-backend-$TargetTriple$ExecutableExtension"

if (!(Test-Path $source)) {
    throw "Backend executable not found: $source"
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
Copy-Item -LiteralPath $source -Destination $target -Force
Write-Host "Prepared Tauri sidecar: $target"
