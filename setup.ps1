# ============================================================
#  Image Upscaler - Binary Auto Setup
#  Downloads ncnn-Vulkan binaries from official GitHub releases.
# ------------------------------------------------------------
#  Run: .\setup.ps1          (interactive, asks for confirmation)
#       .\setup.ps1 -Yes     (no prompt)
#  Note: Image processing is fully local. This script only
#        communicates with github.com to fetch binaries.
# ============================================================

param(
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

# Force TLS 1.2 (for Windows PowerShell 5.1)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BinDir = Join-Path $ScriptDir 'bin'

if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir | Out-Null
}

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Get-LatestZipUrl {
    param(
        [string]$Repo,
        [string]$Pattern
    )
    # Search across recent releases (some repos keep binaries only on older tags)
    $api = "https://api.github.com/repos/$Repo/releases?per_page=30"
    Write-Host "  -> GitHub API: $api"
    try {
        $releases = Invoke-RestMethod -Uri $api -Headers @{ 'User-Agent' = 'image-upscaler-setup' } -TimeoutSec 30
    } catch {
        throw "GitHub API request failed: $($_.Exception.Message)"
    }
    foreach ($rel in $releases) {
        $asset = $rel.assets | Where-Object { $_.name -like $Pattern } | Select-Object -First 1
        if ($asset) {
            return @{
                Url  = $asset.browser_download_url
                Name = $asset.name
                Size = $asset.size
                Tag  = $rel.tag_name
            }
        }
    }
    throw "No asset matching '$Pattern' found in last 30 releases of $Repo"
}

function Install-Engine {
    param(
        [string]$EngineName,
        [string]$TargetDir,
        [string]$Repo,
        [string]$Pattern,
        [string]$ExeName
    )

    Write-Section "$EngineName setup"

    $exePath = Join-Path $TargetDir $ExeName
    if (Test-Path $exePath) {
        Write-Host "  [OK] Already installed: $exePath" -ForegroundColor Green
        return
    }

    $info = Get-LatestZipUrl -Repo $Repo -Pattern $Pattern
    $sizeMB = [math]::Round($info.Size / 1MB, 1)
    Write-Host "  Latest: $($info.Tag)"
    Write-Host "  File  : $($info.Name) ($sizeMB MB)"
    Write-Host "  From  : $($info.Url)"

    $rand = [guid]::NewGuid().ToString('N').Substring(0, 8)
    $tmpZip = Join-Path $env:TEMP "imgupscaler_${rand}_$($info.Name)"
    $tmpExtract = Join-Path $env:TEMP "imgupscaler_extract_$rand"

    Write-Host "  -> Downloading..."
    try {
        Invoke-WebRequest -Uri $info.Url -OutFile $tmpZip -UseBasicParsing -TimeoutSec 600
    } catch {
        throw "Download failed: $($_.Exception.Message)"
    }

    Write-Host "  -> Extracting..."
    Expand-Archive -Path $tmpZip -DestinationPath $tmpExtract -Force

    $items = Get-ChildItem $tmpExtract
    if ($items.Count -eq 1 -and $items[0].PSIsContainer) {
        $sourceDir = $items[0].FullName
    } else {
        $sourceDir = $tmpExtract
    }

    if (Test-Path $TargetDir) {
        Remove-Item $TargetDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $TargetDir | Out-Null

    Get-ChildItem $sourceDir | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $TargetDir
    }

    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue
    Remove-Item $tmpExtract -Recurse -Force -ErrorAction SilentlyContinue

    if (Test-Path $exePath) {
        Write-Host "  [OK] Installed: $exePath" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] $ExeName not found. ZIP layout differs from expected." -ForegroundColor Yellow
        Write-Host "         Please install manually per README.md." -ForegroundColor Yellow
    }
}

# ---------- Start ----------
Write-Host ""
Write-Host "Image Upscaler - Binary Setup" -ForegroundColor Magenta
Write-Host ""
Write-Host "This script downloads the following from GitHub:"
Write-Host "  1. Real-ESRGAN ncnn-Vulkan  (xinntao/Real-ESRGAN)"
Write-Host "  2. waifu2x ncnn-Vulkan      (nihui/waifu2x-ncnn-vulkan)"
Write-Host ""
Write-Host "Note: Only github.com is contacted. No personal data is sent." -ForegroundColor Green
Write-Host ""

if (-not $Yes) {
    try {
        $ans = Read-Host "Continue? [Y/n]"
    } catch {
        $ans = ''  # non-interactive mode -> treat as Y
    }
    if ($ans -and $ans -notmatch '^[Yy]') {
        Write-Host "Aborted."
        exit 0
    }
}

$errs = @()

try {
    Install-Engine -EngineName 'Real-ESRGAN ncnn-Vulkan' `
        -TargetDir (Join-Path $BinDir 'realesrgan-ncnn-vulkan') `
        -Repo 'xinntao/Real-ESRGAN' `
        -Pattern '*ncnn-vulkan*windows*.zip' `
        -ExeName 'realesrgan-ncnn-vulkan.exe'
} catch {
    $errs += "Real-ESRGAN: $($_.Exception.Message)"
    Write-Host "  [ERR] $($_.Exception.Message)" -ForegroundColor Red
}

try {
    Install-Engine -EngineName 'waifu2x ncnn-Vulkan' `
        -TargetDir (Join-Path $BinDir 'waifu2x-ncnn-vulkan') `
        -Repo 'nihui/waifu2x-ncnn-vulkan' `
        -Pattern '*windows*.zip' `
        -ExeName 'waifu2x-ncnn-vulkan.exe'
} catch {
    $errs += "waifu2x: $($_.Exception.Message)"
    Write-Host "  [ERR] $($_.Exception.Message)" -ForegroundColor Red
}

# ---------- Summary ----------
Write-Section "Setup Result"

$realesrganExe = Join-Path $BinDir 'realesrgan-ncnn-vulkan\realesrgan-ncnn-vulkan.exe'
$waifu2xExe = Join-Path $BinDir 'waifu2x-ncnn-vulkan\waifu2x-ncnn-vulkan.exe'

if (Test-Path $realesrganExe) {
    Write-Host "  [OK]  Real-ESRGAN ncnn-Vulkan" -ForegroundColor Green
} else {
    Write-Host "  [NG]  Real-ESRGAN ncnn-Vulkan (not installed)" -ForegroundColor Red
}

if (Test-Path $waifu2xExe) {
    Write-Host "  [OK]  waifu2x ncnn-Vulkan" -ForegroundColor Green
} else {
    Write-Host "  [NG]  waifu2x ncnn-Vulkan (not installed)" -ForegroundColor Red
}

if ($errs.Count -gt 0) {
    Write-Host ""
    Write-Host "Errors:" -ForegroundColor Yellow
    foreach ($e in $errs) { Write-Host "   - $e" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "If a download failed, follow the manual steps in README.md." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next: .\run.bat   or   py -m streamlit run app.py" -ForegroundColor Cyan
Write-Host ""
