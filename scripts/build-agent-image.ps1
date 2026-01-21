param(
    [string] $Region,
    [string] $BucketName,
    [string] $BuildProjectName
)

# Default region if nothing is provided
if (-not $Region -or [string]::IsNullOrEmpty($Region)) {
    if ($env:AWS_DEFAULT_REGION) {
        $Region = $env:AWS_DEFAULT_REGION
    } elseif ($env:AWS_REGION) {
        $Region = $env:AWS_REGION
    } else {
        $Region = "us-east-1"
    }
}
$env:AWS_DEFAULT_REGION = $Region
$env:AWS_REGION = $Region

Write-Host "Using region: $Region" -ForegroundColor Cyan

# Discover outputs from AgentCoreInfra if not provided
$infraStack = "AgentCoreInfra"
if (-not $BucketName -or [string]::IsNullOrEmpty($BucketName)) {
    $BucketName = aws cloudformation describe-stacks --stack-name $infraStack --query "Stacks[0].Outputs[?OutputKey=='SourceBucketName'].OutputValue" --output text --no-cli-pager 2>$null
}
if (-not $BuildProjectName -or [string]::IsNullOrEmpty($BuildProjectName)) {
    $BuildProjectName = aws cloudformation describe-stacks --stack-name $infraStack --query "Stacks[0].Outputs[?OutputKey=='BuildProjectName'].OutputValue" --output text --no-cli-pager 2>$null
}
$RepoUri = aws cloudformation describe-stacks --stack-name $infraStack --query "Stacks[0].Outputs[?OutputKey=='RepositoryUri'].OutputValue" --output text --no-cli-pager 2>$null

if ([string]::IsNullOrEmpty($BucketName) -or [string]::IsNullOrEmpty($BuildProjectName)) {
    Write-Host "[ERROR] Missing SourceBucketName or BuildProjectName. Pass them as parameters or ensure $infraStack exists." -ForegroundColor Red
    exit 1
}

Write-Host "Source bucket: $BucketName" -ForegroundColor Gray
Write-Host "Build project: $BuildProjectName" -ForegroundColor Gray
if ($RepoUri -and $RepoUri -ne "None") { Write-Host "ECR repo: $RepoUri (tag: latest)" -ForegroundColor Gray }

# Package agent source
$zipPath = Join-Path $PWD "agent-source.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Write-Host "Packaging agent source..." -ForegroundColor Yellow

$archiveSucceeded = $false
try {
    git -C $PWD archive --prefix=agent/ -o $zipPath HEAD:agent 2>$null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $zipPath)) { $archiveSucceeded = $true }
} catch {}

if (-not $archiveSucceeded) {
    Write-Host "git archive failed; using Compress-Archive fallback" -ForegroundColor Yellow
    Compress-Archive -Path "agent" -DestinationPath $zipPath -Force
}

if (-not (Test-Path $zipPath)) {
    Write-Host "[ERROR] Failed to create agent-source.zip" -ForegroundColor Red
    exit 1
}

# Upload to S3
Write-Host "Uploading agent-source.zip to s3://$BucketName/agent-source.zip ..." -ForegroundColor Yellow
aws s3 cp $zipPath "s3://$BucketName/agent-source.zip" --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Upload failed" -ForegroundColor Red
    exit 1
}

# Start CodeBuild
Write-Host "Starting CodeBuild ($BuildProjectName)..." -ForegroundColor Yellow
$buildId = aws codebuild start-build --project-name $BuildProjectName --region $Region --query 'build.id' --output text
if ([string]::IsNullOrEmpty($buildId)) {
    Write-Host "[ERROR] Failed to start CodeBuild" -ForegroundColor Red
    exit 1
}
Write-Host "Build ID: $buildId" -ForegroundColor Green
Write-Host "Waiting for build to finish (this may take ~5-10 minutes)..." -ForegroundColor DarkGray

$logLink = ""
do {
    Start-Sleep -Seconds 15
    $buildInfo = aws codebuild batch-get-builds --ids $buildId --region $Region --query 'builds[0]' --output json | ConvertFrom-Json
    $status = $buildInfo.buildStatus
    $phase = $buildInfo.currentPhase
    $logLink = $buildInfo.logs.deepLink
    Write-Host "Status: $status | Phase: $phase" -ForegroundColor Gray
} while ($status -eq 'IN_PROGRESS')

if ($status -ne 'SUCCEEDED') {
    Write-Host "[ERROR] CodeBuild failed with status: $status" -ForegroundColor Red
    if ($logLink) { Write-Host "Logs: $logLink" -ForegroundColor Cyan }
    exit 1
}

Write-Host "CodeBuild succeeded." -ForegroundColor Green
if ($RepoUri -and $RepoUri -ne "None") { Write-Host "Pushed image: $RepoUri:latest" -ForegroundColor Green }
Write-Host "Done." -ForegroundColor Green
