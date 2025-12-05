# Setup script for Amazon WP Poster
# Run this script to set up the project

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Amazon WP Poster - Setup Script                         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.8 or higher" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green

# Create .env if not exists
Write-Host ""
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created!" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env and add your credentials" -ForegroundColor Yellow
} else {
    Write-Host "ℹ️  .env file already exists" -ForegroundColor Cyan
}

# Check cerebras_api_keys.txt
Write-Host ""
if (-not (Test-Path "cerebras_api_keys.txt")) {
    Write-Host "⚠️  cerebras_api_keys.txt not found or empty" -ForegroundColor Yellow
    Write-Host "   Please add your Cerebras API keys (one per line)" -ForegroundColor Yellow
} else {
    $keyCount = (Get-Content "cerebras_api_keys.txt" | Where-Object { $_ -match "^csk-" }).Count
    if ($keyCount -gt 0) {
        Write-Host "✅ Found $keyCount Cerebras API key(s)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No valid API keys found in cerebras_api_keys.txt" -ForegroundColor Yellow
    }
}

# Check keywords.txt
Write-Host ""
if (-not (Test-Path "keywords.txt")) {
    Write-Host "⚠️  keywords.txt not found" -ForegroundColor Yellow
} else {
    $keywordCount = (Get-Content "keywords.txt" | Where-Object { $_.Trim() -ne "" -and -not $_.StartsWith("#") }).Count
    if ($keywordCount -gt 0) {
        Write-Host "✅ Found $keywordCount keyword(s) to process" -ForegroundColor Green
    } else {
        Write-Host "⚠️  keywords.txt is empty" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ Setup Complete!                                       ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Edit .env and add your WordPress/Amazon/Cerebras credentials"
Write-Host "   2. Add Cerebras API keys to cerebras_api_keys.txt"
Write-Host "   3. Add keywords to keywords.txt (one per line)"
Write-Host "   4. Run: python main.py"
Write-Host ""
