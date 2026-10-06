# Build (if needed) and launch Agent Course.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
cargo build --release
if ($LASTEXITCODE -ne 0) { throw "cargo build failed" }
Start-Process -FilePath "$PSScriptRoot\target\release\agent-course.exe" -WorkingDirectory $PSScriptRoot
