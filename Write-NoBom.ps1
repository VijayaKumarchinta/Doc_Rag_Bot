param(
  [Parameter(Mandatory)] [string]$Path,
  [Parameter(Mandatory)] [string]$Content
)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$full = Join-Path (Get-Location) $Path
$dir  = Split-Path $full -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
[System.IO.File]::WriteAllText($full, $Content, $utf8NoBom)
Write-Host "Wrote (no BOM): $Path"
