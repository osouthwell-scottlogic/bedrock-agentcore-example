# Deploy AgentCore Demo - Complete Deployment Script

Write-Host "=== AgentCore Demo Deployment ===" -ForegroundColor Cyan

# Step 1: Verify AWS credentials
Write-Host "`n[1/10] Verifying AWS credentials..." -ForegroundColor Yellow
Write-Host "      (Checking AWS CLI configuration and validating access)" -ForegroundColor Gray

# Check if AWS credentials are configured
$callerIdentity = aws sts get-caller-identity 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "AWS credentials are not configured or have expired" -ForegroundColor Red
    Write-Host "`nPlease configure AWS credentials using one of these methods:" -ForegroundColor Yellow
    Write-Host "  1. Run: aws configure" -ForegroundColor Cyan
    Write-Host "  2. Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY" -ForegroundColor Cyan
    Write-Host "  3. Use AWS SSO: aws sso login --profile <profile-name>" -ForegroundColor Cyan
    Write-Host "`nFor more info: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html" -ForegroundColor Gray
    exit 1
}

# Display current AWS identity
$accountId = ($callerIdentity | ConvertFrom-Json).Account
$arn = ($callerIdentity | ConvertFrom-Json).Arn
Write-Host "      Authenticated as: $arn" -ForegroundColor Green
Write-Host "      AWS Account: $accountId" -ForegroundColor Green

# Default region to use if not provided
$defaultRegion = "us-east-1"

# Step 2: Check AWS CLI version
Write-Host "`n[2/10] Checking AWS CLI version..." -ForegroundColor Yellow
$awsVersion = aws --version 2>&1
$versionMatch = $awsVersion -match 'aws-cli/(\d+)\.(\d+)\.(\d+)'
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3]
    Write-Host "      Current version: aws-cli/$major.$minor.$patch" -ForegroundColor Gray
    
    # Check if version is >= 2.31.13
    $isVersionValid = ($major -gt 2) -or 
                      ($major -eq 2 -and $minor -gt 31) -or 
                      ($major -eq 2 -and $minor -eq 31 -and $patch -ge 13)
    
    if (-not $isVersionValid) {
        Write-Host "      [ERROR] AWS CLI version 2.31.13 or later is required" -ForegroundColor Red
        Write-Host ""
        Write-Host "      AgentCore support was added in AWS CLI v2.31.13 (January 2025)" -ForegroundColor Yellow
        Write-Host "      Your current version: aws-cli/$major.$minor.$patch" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "      Please upgrade your AWS CLI:" -ForegroundColor Yellow
        Write-Host "        https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html" -ForegroundColor Cyan
        exit 1
    }
    Write-Host "      [OK] AWS CLI version is compatible" -ForegroundColor Green
} else {
    Write-Host "      [WARNING] Could not parse AWS CLI version, continuing anyway..." -ForegroundColor Yellow
}

# Step 3: Check AgentCore availability in current region
Write-Host "`n[3/10] Checking AgentCore availability in current region..." -ForegroundColor Yellow

# Ensure region env vars are populated early so the rest of the script can rely on them
if (-not $env:AWS_DEFAULT_REGION -or [string]::IsNullOrEmpty($env:AWS_DEFAULT_REGION)) {
    $env:AWS_DEFAULT_REGION = $defaultRegion
}
if (-not $env:AWS_REGION -or [string]::IsNullOrEmpty($env:AWS_REGION)) {
    $env:AWS_REGION = $env:AWS_DEFAULT_REGION
}

# Check if region is explicitly set via environment variable
if ($env:AWS_DEFAULT_REGION) {
    $currentRegion = $env:AWS_DEFAULT_REGION
    Write-Host "      Using region from AWS_DEFAULT_REGION: $currentRegion" -ForegroundColor Cyan
} elseif ($env:AWS_REGION) {
    $currentRegion = $env:AWS_REGION
    Write-Host "      Using region from AWS_REGION: $currentRegion" -ForegroundColor Cyan
} else {
    # Detect current region from AWS CLI configuration
    $currentRegion = aws configure get region
    if ([string]::IsNullOrEmpty($currentRegion)) {
        Write-Host "      [WARNING] No AWS region configured, trying us-east-1" -ForegroundColor Yellow
        $currentRegion = "us-east-1"
        $env:AWS_DEFAULT_REGION = $currentRegion
    }
}

Write-Host "      Target region: $currentRegion" -ForegroundColor Gray

# List of known AgentCore-supported regions to try
$supportedRegions = @("us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1")

# Try to list AgentCore runtimes to verify service availability
$agentCoreCheck = aws bedrock-agentcore-control list-agent-runtimes --region $currentRegion --max-results 1 2>&1
if ($LASTEXITCODE -ne 0) {
    $errorMessage = $agentCoreCheck | Out-String
    Write-Host "      [ERROR] AgentCore is not available in region: $currentRegion" -ForegroundColor Red
    Write-Host ""
    Write-Host "      Trying alternative regions..." -ForegroundColor Yellow
    
    $foundRegion = $false
    foreach ($testRegion in $supportedRegions) {
        if ($testRegion -eq $currentRegion) { continue }
        
        Write-Host "      Testing $testRegion..." -ForegroundColor Gray
        $testCheck = aws bedrock-agentcore-control list-agent-runtimes --region $testRegion --max-results 1 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      [OK] AgentCore is available in $testRegion" -ForegroundColor Green
            $currentRegion = $testRegion
            $env:AWS_DEFAULT_REGION = $testRegion
            $env:AWS_REGION = $testRegion
            $foundRegion = $true
            break
        }
    }
    
    if (-not $foundRegion) {
        Write-Host ""
        Write-Host "      Could not find an available region for AgentCore" -ForegroundColor Red
        Write-Host "      For supported regions, see:" -ForegroundColor Gray
        Write-Host "      https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-regions.html" -ForegroundColor Gray
        exit 1
    }
} else {
    Write-Host "      [OK] AgentCore is available in $currentRegion" -ForegroundColor Green
}

# Ensure region environment variables are set for all subsequent commands
$env:AWS_DEFAULT_REGION = $currentRegion
$env:AWS_REGION = $currentRegion

# Step 4: Install CDK dependencies
Write-Host "`n[4/10] Installing CDK dependencies..." -ForegroundColor Yellow
Write-Host "      (Installing AWS CDK libraries and TypeScript packages for infrastructure code)" -ForegroundColor Gray
if (-not (Test-Path "cdk/node_modules")) {
    Push-Location cdk
    npm install
    Pop-Location
} else {
    Write-Host "      CDK dependencies already installed, skipping..." -ForegroundColor Gray
}

# Step 5: Install frontend dependencies
Write-Host "`n[5/10] Installing frontend dependencies..." -ForegroundColor Yellow
Write-Host "      (Installing React, Vite, Cognito SDK, and UI component libraries)" -ForegroundColor Gray
Push-Location frontend
# Commented out to save time during development - uncomment for clean builds
# if (Test-Path "node_modules") {
#     Write-Host "Removing existing node_modules..." -ForegroundColor Gray
#     Remove-Item -Recurse -Force "node_modules"
# }
npm install
Pop-Location

# Step 6: Create placeholder dist BEFORE any CDK commands
# (CDK synthesizes all stacks even when deploying one, so frontend/dist must exist)
Write-Host "`n[6/10] Creating placeholder frontend build..." -ForegroundColor Yellow
Write-Host "      (Generating temporary HTML file - required for CDK synthesis)" -ForegroundColor Gray
if (-not (Test-Path "frontend/dist")) {
    New-Item -ItemType Directory -Path "frontend/dist" -Force | Out-Null
    echo "<!DOCTYPE html><html><body><h1>Building...</h1></body></html>" > frontend/dist/index.html
} else {
    Write-Host "      Placeholder already exists, skipping..." -ForegroundColor Gray
}

# Step 7: Bootstrap CDK (if needed)
Write-Host "`n[7/10] Bootstrapping CDK environment..." -ForegroundColor Yellow
Write-Host "      (Setting up CDK deployment resources in your AWS account/region)" -ForegroundColor Gray

# First, clean up any failed change sets
Write-Host "      Cleaning up any failed change sets..." -ForegroundColor Gray
aws cloudformation delete-change-set --stack-name CDKToolkit --change-set-name cdk-deploy-change-set 2>&1 | Out-Null

# Check current stack status and clean up any stuck states
$stackStatus = aws cloudformation describe-stacks --stack-name CDKToolkit --query 'Stacks[0].StackStatus' --output text 2>&1

if ($stackStatus -match "REVIEW_IN_PROGRESS") {
    Write-Host "      CDKToolkit stack is stuck in REVIEW_IN_PROGRESS state, deleting..." -ForegroundColor Yellow
    
    # Delete all change sets first
    $changeSets = aws cloudformation list-change-sets --stack-name CDKToolkit --query 'Summaries[*].ChangeSetName' --output text 2>&1
    if ($changeSets -and $changeSets -notmatch "does not exist") {
        foreach ($cs in $changeSets -split '\s+') {
            if ($cs) {
                Write-Host "      Deleting change set: $cs" -ForegroundColor Gray
                aws cloudformation delete-change-set --stack-name CDKToolkit --change-set-name $cs 2>&1 | Out-Null
            }
        }
    }
    
    # Now delete the stack
    aws cloudformation delete-stack --stack-name CDKToolkit 2>&1 | Out-Null
    Write-Host "      Waiting for deletion..." -ForegroundColor Gray
    
    $maxWait = 60
    $waited = 0
    while ($waited -lt $maxWait) {
        $checkStatus = aws cloudformation describe-stacks --stack-name CDKToolkit 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "      Stack deleted successfully" -ForegroundColor Green
            break
        }
        Start-Sleep -Seconds 5
        $waited += 5
    }
    $stackStatus = "DELETED"
}

if ($stackStatus -match "ROLLBACK_COMPLETE") {
    Write-Host "      CDKToolkit stack is in ROLLBACK_COMPLETE state, deleting..." -ForegroundColor Yellow
    aws cloudformation delete-stack --stack-name CDKToolkit 2>&1 | Out-Null
    Write-Host "      Waiting for deletion..." -ForegroundColor Gray
    aws cloudformation wait stack-delete-complete --stack-name CDKToolkit 2>&1 | Out-Null
    Write-Host "      Stack deleted" -ForegroundColor Green
    $stackStatus = "DELETED"
}

if ($stackStatus -match "CREATE_COMPLETE|UPDATE_COMPLETE") {
    Write-Host "      CDK already bootstrapped" -ForegroundColor Green
} else {
    # Try bootstrap
    Push-Location cdk
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    Write-Host "      Running bootstrap..." -ForegroundColor Gray
    npx cdk bootstrap --output "cdk.out.$timestamp" --no-cli-pager --no-color 2>&1 | Tee-Object -Variable bootstrapOutput
    $bootstrapExitCode = $LASTEXITCODE
    Pop-Location

    if ($bootstrapExitCode -ne 0) {
        # Check for the specific Early Validation error
        if ($bootstrapOutput -match "EarlyValidation|ResourceExistenceCheck") {
            Write-Host "" -ForegroundColor Yellow
            Write-Host "      [WARNING] AWS Early Validation failure - known CloudFormation bug" -ForegroundColor Yellow
            Write-Host "      Skipping CDK bootstrap and proceeding with direct deployments..." -ForegroundColor Cyan
            aws cloudformation delete-stack --stack-name CDKToolkit 2>&1 | Out-Null
        } else {
            Write-Host "      CDK bootstrap failed" -ForegroundColor Red
            exit 1
        }
    }
}

# Verify CDK execution role exists and has necessary permissions
Write-Host "      Verifying CDK execution role..." -ForegroundColor Gray
$cdkExecRoleName = "cdk-hnb659fds-cfn-exec-role-$accountId-$currentRegion"
$roleCheck = aws iam get-role --role-name $cdkExecRoleName 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "      [WARNING] CDK execution role not found, creating it..." -ForegroundColor Yellow
    
    # Create trust policy for CloudFormation
    $trustPolicy = @'
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect":"Allow",
      "Principal":{"Service":"cloudformation.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }
  ]
}
'@
    
    $trustPolicy | Set-Content -Path "$env:TEMP\cdk-exec-role-trust.json"
    aws iam create-role --role-name $cdkExecRoleName --assume-role-policy-document "file://$env:TEMP/cdk-exec-role-trust.json" --description "CDK CloudFormation execution role" --no-cli-pager | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      CDK execution role created" -ForegroundColor Green
        
        # Attach necessary policies
        aws iam attach-role-policy --role-name $cdkExecRoleName --policy-arn arn:aws:iam::aws:policy/AdministratorAccess | Out-Null
        Write-Host "      Attached AdministratorAccess policy" -ForegroundColor Green
        
        # Wait for role to propagate
        Write-Host "      Waiting for role to propagate..." -ForegroundColor Gray
        Start-Sleep -Seconds 10
    } else {
        Write-Host "      [ERROR] Failed to create CDK execution role" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "      [OK] CDK execution role exists" -ForegroundColor Green
}

# Step 8: Deploy infrastructure stack
Write-Host "`n[8/10] Deploying infrastructure stack..." -ForegroundColor Yellow
Write-Host "      (Creating ECR repository, CodeBuild project, S3 bucket, and IAM roles)" -ForegroundColor Gray

# Check for problematic states
$infraStackStatus = aws cloudformation describe-stacks --stack-name AgentCoreInfra --query 'Stacks[0].StackStatus' --output text 2>&1
if ($infraStackStatus -match "UPDATE_ROLLBACK_COMPLETE") {
    Write-Host "      [WARNING] Infrastructure stack is in UPDATE_ROLLBACK_COMPLETE state" -ForegroundColor Yellow
    Write-Host "      This means a previous update failed and rolled back" -ForegroundColor Gray
    Write-Host "      Attempting deployment anyway..." -ForegroundColor Gray
}

Push-Location cdk
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
npx cdk deploy AgentCoreInfra --output "cdk.out.$timestamp" --no-cli-pager --require-approval never
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host "Infrastructure deployment failed" -ForegroundColor Red
    exit 1
}

# Step 9: Deploy auth stack
Write-Host "`n[9/10] Deploying authentication stack..." -ForegroundColor Yellow
Write-Host "      (Creating Cognito User Pool with email verification and password policies)" -ForegroundColor Gray
Push-Location cdk
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
npx cdk deploy AgentCoreAuth --output "cdk.out.$timestamp" --no-cli-pager --require-approval never
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host "Auth deployment failed" -ForegroundColor Red
    exit 1
}

# Step 10: Build agent container image and deploy backend stack
Write-Host "`n[10/10] Building agent image and deploying backend stack..." -ForegroundColor Yellow
Write-Host "      (Packages agent code, pushes image via CodeBuild, then deploys AgentCore runtime)" -ForegroundColor Gray

# Resolve infra outputs for bucket and build project
$sourceBucket = aws cloudformation describe-stacks --stack-name AgentCoreInfra --query "Stacks[0].Outputs[?OutputKey=='SourceBucketName'].OutputValue" --output text --no-cli-pager
$buildProjectName = aws cloudformation describe-stacks --stack-name AgentCoreInfra --query "Stacks[0].Outputs[?OutputKey=='BuildProjectName'].OutputValue" --output text --no-cli-pager

if ([string]::IsNullOrEmpty($sourceBucket) -or [string]::IsNullOrEmpty($buildProjectName)) {
    Write-Host "      [ERROR] Missing SourceBucket or BuildProject outputs from AgentCoreInfra" -ForegroundColor Red
    exit 1
}

Write-Host "      Source bucket: $sourceBucket" -ForegroundColor Gray
Write-Host "      Build project: $buildProjectName" -ForegroundColor Gray

# Package agent source
$zipPath = Join-Path $PWD "agent-source.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Write-Host "      Packaging agent source..." -ForegroundColor Gray

$archiveSucceeded = $false
try {
    git -C $PWD archive --prefix=agent/ -o $zipPath HEAD:agent 2>$null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $zipPath)) { $archiveSucceeded = $true }
} catch {}

if (-not $archiveSucceeded) {
    Write-Host "      git archive failed; falling back to Compress-Archive" -ForegroundColor Yellow
    Compress-Archive -Path "agent" -DestinationPath $zipPath -Force
}

if (-not (Test-Path $zipPath)) {
    Write-Host "      [ERROR] Failed to create agent-source.zip" -ForegroundColor Red
    exit 1
}

# Upload to S3
Write-Host "      Uploading agent-source.zip to S3..." -ForegroundColor Gray
aws s3 cp $zipPath "s3://$sourceBucket/agent-source.zip" --region $currentRegion | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "      [ERROR] Failed to upload agent-source.zip" -ForegroundColor Red
    exit 1
}

# Start CodeBuild
Write-Host "      Starting CodeBuild ($buildProjectName)..." -ForegroundColor Gray
$buildId = aws codebuild start-build --project-name $buildProjectName --region $currentRegion --query 'build.id' --output text
if ([string]::IsNullOrEmpty($buildId)) {
    Write-Host "      [ERROR] Failed to start CodeBuild" -ForegroundColor Red
    exit 1
}

Write-Host "      Build ID: $buildId" -ForegroundColor Green
Write-Host "      Waiting for build to finish (this may take ~5-10 minutes)..." -ForegroundColor DarkGray

do {
    Start-Sleep -Seconds 15
    $buildInfo = aws codebuild batch-get-builds --ids $buildId --region $currentRegion --query 'builds[0]' --output json | ConvertFrom-Json
    $status = $buildInfo.buildStatus
    $phase = $buildInfo.currentPhase
    Write-Host "      Status: $status | Phase: $phase" -ForegroundColor Gray
} while ($status -eq 'IN_PROGRESS')

if ($status -ne 'SUCCEEDED') {
    $logLink = $buildInfo.logs.deepLink
    Write-Host "      [ERROR] CodeBuild failed with status: $status" -ForegroundColor Red
    if ($logLink) { Write-Host "      Logs: $logLink" -ForegroundColor Cyan }
    exit 1
}

Write-Host "      CodeBuild succeeded; deploying AgentCoreRuntime..." -ForegroundColor Green

Push-Location cdk
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
npx cdk deploy AgentCoreRuntime --output "cdk.out.$timestamp" --no-cli-pager --require-approval never 2>&1 | Tee-Object -Variable cdkOutput
$deployExitCode = $LASTEXITCODE
Pop-Location

if ($deployExitCode -ne 0) {
    Write-Host "Backend deployment failed" -ForegroundColor Red
    exit 1
}

# Deploy API Gateway stack first
Write-Host "`nDeploying API Gateway stack..." -ForegroundColor Yellow
Write-Host "      (Creating CORS-enabled proxy for browser access to AgentCore)" -ForegroundColor Gray
Push-Location cdk
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
npx cdk deploy AgentCoreApiGateway --output "cdk.out.$timestamp" --no-cli-pager --require-approval never
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host "API Gateway deployment failed" -ForegroundColor Red
    exit 1
}

# Build and deploy frontend (after backend is complete)
Write-Host "`nBuilding and deploying frontend..." -ForegroundColor Yellow
Write-Host "      (Retrieving AgentCore Runtime ID and Cognito config, building React app, deploying to S3 + CloudFront)" -ForegroundColor Gray
$agentRuntimeArn = aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" --output text --no-cli-pager
$region = aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].Outputs[?OutputKey=='Region'].OutputValue" --output text --no-cli-pager
$userPoolId = aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text --no-cli-pager
$userPoolClientId = aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text --no-cli-pager
$apiGatewayUrl = aws cloudformation describe-stacks --stack-name AgentCoreApiGateway --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text --no-cli-pager

if ([string]::IsNullOrEmpty($agentRuntimeArn)) {
    Write-Host "Failed to get Agent Runtime ARN from stack outputs" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($region)) {
    Write-Host "Failed to get Region from stack outputs" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($userPoolId) -or [string]::IsNullOrEmpty($userPoolClientId)) {
    Write-Host "Failed to get Cognito config from stack outputs" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($apiGatewayUrl)) {
    Write-Host "Failed to get API Gateway URL from stack outputs" -ForegroundColor Red
    exit 1
}

Write-Host "Agent Runtime ARN: $agentRuntimeArn" -ForegroundColor Green
Write-Host "Region: $region" -ForegroundColor Green
Write-Host "User Pool ID: $userPoolId" -ForegroundColor Green
Write-Host "User Pool Client ID: $userPoolClientId" -ForegroundColor Green
Write-Host "API Gateway URL: $apiGatewayUrl" -ForegroundColor Green

# Build frontend with AgentCore Runtime ARN and Cognito config
& .\scripts\build-frontend.ps1 -UserPoolId $userPoolId -UserPoolClientId $userPoolClientId -AgentRuntimeArn $agentRuntimeArn -ApiGatewayUrl $apiGatewayUrl -Region $region

if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed" -ForegroundColor Red
    exit 1
}

# Deploy frontend stack
Push-Location cdk
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
npx cdk deploy AgentCoreFrontendV2 --output "cdk.out.$timestamp" --no-cli-pager --require-approval never
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend deployment failed" -ForegroundColor Red
    exit 1
}

# Get CloudFront URL
$websiteUrl = aws cloudformation describe-stacks --stack-name AgentCoreFrontendV2 --query "Stacks[0].Outputs[?OutputKey=='WebsiteUrl'].OutputValue" --output text --no-cli-pager

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Website URL: $websiteUrl" -ForegroundColor Cyan
Write-Host "API Gateway URL: $apiGatewayUrl" -ForegroundColor Cyan
Write-Host "Agent Runtime ARN: $agentRuntimeArn" -ForegroundColor Cyan
Write-Host "Region: $region" -ForegroundColor Cyan
Write-Host "User Pool ID: $userPoolId" -ForegroundColor Cyan
Write-Host "User Pool Client ID: $userPoolClientId" -ForegroundColor Cyan
Write-Host "`nNote: Users must sign up and log in to use the application" -ForegroundColor Yellow
Write-Host "Frontend calls AgentCore via API Gateway proxy with JWT authentication" -ForegroundColor Green

