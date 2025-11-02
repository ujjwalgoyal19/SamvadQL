# PowerShell script for automated first-time development setup
# Run this script: .\scripts\dev-setup.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 SamvadQL Development Setup" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✓ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker daemon is not running" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose installed: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose is not installed" -ForegroundColor Red
    exit 1
}

# Check WSL2 (Windows-specific)
if ($IsWindows) {
    try {
        wsl --status | Out-Null
        Write-Host "✓ WSL2 is available" -ForegroundColor Green
        Write-Host "  Tip: Enable 'Use WSL2 based engine' in Docker Desktop for 10x faster performance" -ForegroundColor Cyan
    } catch {
        Write-Host "⚠ WSL2 not detected - consider enabling for better performance" -ForegroundColor Yellow
    }
}

# Check disk space
$drive = (Get-Location).Drive.Name
$freeSpace = (Get-PSDrive $drive).Free / 1GB
if ($freeSpace -lt 20) {
    Write-Host "⚠ Warning: Only $([math]::Round($freeSpace, 2)) GB free on drive $drive" -ForegroundColor Yellow
    Write-Host "  Recommended: 20+ GB free for Docker images and volumes" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") { exit 0 }
}

Write-Host "`n✓ All prerequisites met!`n" -ForegroundColor Green

# Enable BuildKit
Write-Host "🔧 Enabling BuildKit for faster builds..." -ForegroundColor Yellow
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

# Persist to PowerShell profile
if (Test-Path $PROFILE) {
    $profileContent = Get-Content $PROFILE -Raw
    if ($profileContent -notmatch "DOCKER_BUILDKIT") {
        Add-Content $PROFILE "`n# Docker BuildKit (added by SamvadQL setup)"
        Add-Content $PROFILE "`$env:DOCKER_BUILDKIT = '1'"
        Add-Content $PROFILE "`$env:COMPOSE_DOCKER_CLI_BUILD = '1'"
        Write-Host "✓ BuildKit enabled and added to PowerShell profile" -ForegroundColor Green
    } else {
        Write-Host "✓ BuildKit already configured in profile" -ForegroundColor Green
    }
} else {
    # Create profile if it doesn't exist
    New-Item -Path $PROFILE -ItemType File -Force | Out-Null
    Add-Content $PROFILE "# Docker BuildKit (added by SamvadQL setup)"
    Add-Content $PROFILE "`$env:DOCKER_BUILDKIT = '1'"
    Add-Content $PROFILE "`$env:COMPOSE_DOCKER_CLI_BUILD = '1'"
    Write-Host "✓ BuildKit enabled and PowerShell profile created" -ForegroundColor Green
}

# Setup environment file
Write-Host "`n📝 Setting up environment configuration..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "⚠ .env file already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "Overwrite? (y/n)"
    if ($overwrite -eq "y") {
        Copy-Item ".env.example" ".env" -Force
        Write-Host "✓ .env file created from template" -ForegroundColor Green
    } else {
        Write-Host "✓ Using existing .env file" -ForegroundColor Green
    }
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created from template" -ForegroundColor Green
}

# Prompt for required API keys
Write-Host "`n🔑 API Keys Configuration" -ForegroundColor Yellow
Write-Host "Please provide your API keys (press Enter to skip):`n"

$openaiKey = Read-Host "OpenAI API Key"
if ($openaiKey) {
    (Get-Content ".env") -replace "your-openai-api-key-here", $openaiKey | Set-Content ".env"
}

$anthropicKey = Read-Host "Anthropic API Key (optional)"
if ($anthropicKey) {
    (Get-Content ".env") -replace "your-anthropic-api-key-here", $anthropicKey | Set-Content ".env"
}

$secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
(Get-Content ".env") -replace "your-secret-key-here-change-in-production", $secretKey | Set-Content ".env"
Write-Host "✓ Generated secure SECRET_KEY" -ForegroundColor Green

Write-Host "`n✓ Environment configuration complete!`n" -ForegroundColor Green

# Build images
Write-Host "🏗️  Building Docker images..." -ForegroundColor Yellow
Write-Host "This will take 10-15 minutes on first run (downloads dependencies)`n" -ForegroundColor Cyan

$buildStart = Get-Date
try {
    docker-compose build
    $buildEnd = Get-Date
    $buildTime = ($buildEnd - $buildStart).TotalMinutes
    Write-Host "`n✓ Images built successfully in $([math]::Round($buildTime, 1)) minutes" -ForegroundColor Green
} catch {
    Write-Host "✗ Build failed: $_" -ForegroundColor Red
    exit 1
}

# Start services
Write-Host "`n🚀 Starting services..." -ForegroundColor Yellow
try {
    docker-compose up -d
    Write-Host "✓ Services started" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to start services: $_" -ForegroundColor Red
    exit 1
}

# Wait for services to be healthy
Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check backend health
$maxRetries = 30
$retryCount = 0
$backendHealthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendHealthy = $true
            break
        }
    } catch {
        # Continue waiting
    }
    Start-Sleep -Seconds 2
    $retryCount++
}

if ($backendHealthy) {
    Write-Host "✓ Backend is healthy at http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "⚠ Backend health check timed out - check logs: docker-compose logs backend" -ForegroundColor Yellow
}

# Check frontend
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✓ Frontend is ready at http://localhost:3000" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Frontend not responding yet - may still be starting" -ForegroundColor Yellow
}

# Display success message
Write-Host "`n" -NoNewline
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "==================`n" -ForegroundColor Green

Write-Host "Access your application:" -ForegroundColor Cyan
Write-Host "  • Frontend:      http://localhost:3000" -ForegroundColor White
Write-Host "  • Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:      http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Documentation: http://localhost:3001`n" -ForegroundColor White

Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  • View logs:     docker-compose logs -f backend" -ForegroundColor White
Write-Host "  • Stop services: docker-compose down" -ForegroundColor White
Write-Host "  • Restart:       docker-compose restart backend`n" -ForegroundColor White

Write-Host "📖 Read docs/DEV_WORKFLOW.md for daily development workflow and troubleshooting.`n" -ForegroundColor Yellow

Write-Host "Press any key to view backend logs (Ctrl+C to exit)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
docker-compose logs -f backend
