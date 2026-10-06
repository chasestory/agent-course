# Build a portable copy in .\dist (exe + editable content + README).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
cargo build --release
if ($LASTEXITCODE -ne 0) { throw "cargo build failed" }
New-Item -ItemType Directory -Force -Path dist\content | Out-Null
Copy-Item target\release\agent-course.exe dist\ -Force
Copy-Item content\*.json dist\content\ -Force
Copy-Item README.md dist\ -Force
Write-Host "Built: $PSScriptRoot\dist\agent-course.exe"
