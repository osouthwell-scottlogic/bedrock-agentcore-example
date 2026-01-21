# Check Bedrock Model Access
# Verifies that required Bedrock models are accessible before deployment
# Usage: .\check-bedrock-access.ps1 [-DryRun] [-Verbose]

param(
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Required models
$requiredModels = @{
    "anthropic.claude-haiku-4-5-20251001-v1:0" = "Claude Haiku 4.5"
    "anthropic.claude-sonnet-4-5-20250929-v1:0" = "Claude Sonnet 4.5"
    "amazon.titan-embed-text-v2:0" = "Amazon Titan Embed v2"
}

Write-Host "[CHECK] Checking Bedrock Model Access" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Get current region
$region = aws configure get region
if ([string]::IsNullOrEmpty($region)) {
    $region = $env:AWS_DEFAULT_REGION
    if ([string]::IsNullOrEmpty($region)) {
        $region = "us-east-1"
    }
}
Write-Host "Region: $region" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN MODE]" -ForegroundColor Yellow
    Write-Host "Would check access to the following models:" -ForegroundColor Yellow
    foreach ($modelId in $requiredModels.Keys) {
        Write-Host "  - $($requiredModels[$modelId]) ($modelId)" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "Commands that would be executed:" -ForegroundColor Yellow
    Write-Host "  aws bedrock list-foundation-models --region $region --by-provider anthropic" -ForegroundColor Gray
    Write-Host "  aws bedrock list-foundation-models --region $region --by-provider amazon" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[OK] Dry run complete" -ForegroundColor Green
    exit 0
}

# Check Anthropic models
Write-Host "Checking Anthropic models..." -ForegroundColor Cyan
try {
    $anthropicModelsJson = aws bedrock list-foundation-models --region $region --by-provider anthropic 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to list Anthropic models: $anthropicModelsJson"
    }
    
    if ($Verbose) {
        Write-Host "Anthropic models response:" -ForegroundColor DarkGray
        Write-Host $anthropicModelsJson -ForegroundColor DarkGray
        Write-Host ""
    }
    
    $anthropicModels = $anthropicModelsJson | ConvertFrom-Json
    $anthropicModelIds = @()
    if ($anthropicModels.modelSummaries) {
        $anthropicModelIds = $anthropicModels.modelSummaries | ForEach-Object { $_.modelId }
    }
} catch {
    Write-Host "[ERROR] Failed to check Anthropic models" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please verify:" -ForegroundColor Yellow
    Write-Host "  1. AWS credentials are configured" -ForegroundColor Yellow
    Write-Host "  2. Region $region supports Bedrock" -ForegroundColor Yellow
    Write-Host "  3. You have bedrock:ListFoundationModels permission" -ForegroundColor Yellow
    exit 1
}

# Check Amazon models
Write-Host "Checking Amazon models..." -ForegroundColor Cyan
try {
    $amazonModelsJson = aws bedrock list-foundation-models --region $region --by-provider amazon 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to list Amazon models: $amazonModelsJson"
    }
    
    if ($Verbose) {
        Write-Host "Amazon models response:" -ForegroundColor DarkGray
        Write-Host $amazonModelsJson -ForegroundColor DarkGray
        Write-Host ""
    }
    
    $amazonModels = $amazonModelsJson | ConvertFrom-Json
    $amazonModelIds = @()
    if ($amazonModels.modelSummaries) {
        $amazonModelIds = $amazonModels.modelSummaries | ForEach-Object { $_.modelId }
    }
} catch {
    Write-Host "[ERROR] Failed to check Amazon models" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Combine all available models
$allAvailableModels = $anthropicModelIds + $amazonModelIds

if ($Verbose) {
    Write-Host "All available models:" -ForegroundColor DarkGray
    $allAvailableModels | ForEach-Object { Write-Host "  - $_" -ForegroundColor DarkGray }
    Write-Host ""
}

# Check each required model
$missingModels = @()
foreach ($modelId in $requiredModels.Keys) {
    $modelName = $requiredModels[$modelId]
    
    if ($allAvailableModels -contains $modelId) {
        Write-Host "[OK] $modelName" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $modelName ($modelId)" -ForegroundColor Red
        $missingModels += @{
            id = $modelId
            name = $modelName
        }
    }
}

Write-Host ""

if ($missingModels.Count -gt 0) {
    Write-Host "[WARNING] Missing Model Access" -ForegroundColor Red
    Write-Host "==============================" -ForegroundColor Red
    Write-Host ""
    Write-Host "The following models are not accessible in region $region`:" -ForegroundColor Yellow
    foreach ($model in $missingModels) {
        Write-Host "  - $($model.name) ($($model.id))" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Action Required:" -ForegroundColor Cyan
    Write-Host "  1. Open AWS Console: https://console.aws.amazon.com/bedrock" -ForegroundColor White
    Write-Host "  2. Navigate to: Bedrock > Model access" -ForegroundColor White
    Write-Host "  3. Click 'Manage model access'" -ForegroundColor White
    Write-Host "  4. Enable the missing models" -ForegroundColor White
    Write-Host "  5. Wait for access to be granted (usually instant)" -ForegroundColor White
    Write-Host "  6. Re-run this script to verify" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative regions with Bedrock support:" -ForegroundColor Gray
    Write-Host "  - us-east-1, us-west-2, eu-west-1, ap-southeast-1" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "[SUCCESS] All required models are accessible!" -ForegroundColor Green
Write-Host ""
exit 0
