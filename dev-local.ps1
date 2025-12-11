# Local Development Script - Start frontend and AgentCore backend locally

Write-Host "=== Local Development Mode ===" -ForegroundColor Cyan

# Step 1: Verify AWS credentials
Write-Host "`n[1/7] Verifying AWS credentials..." -ForegroundColor Yellow
Write-Host "      (Required for AWS service access when running agent locally)" -ForegroundColor Gray

# Check if AWS credentials are configured
$callerIdentity = aws sts get-caller-identity 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "      [X] AWS credentials are not configured or have expired" -ForegroundColor Red
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
Write-Host "      [OK] Authenticated as: $arn" -ForegroundColor Green
Write-Host "      AWS Account: $accountId" -ForegroundColor Green

# Step 2: Check AWS CLI version
Write-Host "`n[2/7] Checking AWS CLI version..." -ForegroundColor Yellow
Write-Host "      (Ensuring compatibility with Bedrock service)" -ForegroundColor Gray
$awsVersion = aws --version 2>&1
$versionMatch = $awsVersion -match 'aws-cli/(\d+)\.(\d+)\.(\d+)'
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3]
    Write-Host "      Current version: aws-cli/$major.$minor.$patch" -ForegroundColor Gray
    
    # Check if version is >= 2.31.13 (recommended for Bedrock)
    $isVersionValid = ($major -gt 2) -or ($major -eq 2 -and $minor -gt 31) -or ($major -eq 2 -and $minor -eq 31 -and $patch -ge 13)
    
    if (-not $isVersionValid) {
        Write-Host "      [WARNING] AWS CLI version 2.31.13 or later is recommended for Bedrock" -ForegroundColor Yellow
        Write-Host "      Your current version: aws-cli/$major.$minor.$patch" -ForegroundColor Yellow
        Write-Host "      Consider upgrading: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html" -ForegroundColor Gray
    } else {
        Write-Host "      [OK] AWS CLI version is compatible" -ForegroundColor Green
    }
} else {
    Write-Host "      [WARNING] Could not parse AWS CLI version, continuing anyway..." -ForegroundColor Yellow
}

# Step 3: Check AgentCore availability in current region
Write-Host "`n[3/7] Checking AgentCore availability in current region..." -ForegroundColor Yellow
Write-Host "      (Verifying AgentCore service availability)" -ForegroundColor Gray
# Detect current region from AWS CLI configuration
$currentRegion = aws configure get region
if ([string]::IsNullOrEmpty($currentRegion)) {
    Write-Host "      [X] No AWS region configured" -ForegroundColor Red
    Write-Host ""
    Write-Host "      Please configure your AWS region using:" -ForegroundColor Yellow
    Write-Host "        aws configure set region <your-region>" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "      For supported regions, see:" -ForegroundColor Gray
    Write-Host "      https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-regions.html" -ForegroundColor Gray
    exit 1
}
Write-Host "      Target region: $currentRegion" -ForegroundColor Gray

# Try to list AgentCore runtimes to verify service availability
$agentCoreCheck = aws bedrock-agentcore-control list-agent-runtimes --region $currentRegion --max-results 1 2>&1
if ($LASTEXITCODE -ne 0) {
    $errorMessage = $agentCoreCheck | Out-String
    Write-Host "      [X] AgentCore is not available in region: $currentRegion" -ForegroundColor Red
    Write-Host ""
    Write-Host "      Error details:" -ForegroundColor Gray
    Write-Host "      $errorMessage" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "      For supported regions, see:" -ForegroundColor Gray
    Write-Host "      https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-regions.html" -ForegroundColor Gray
    exit 1
}
Write-Host "      [OK] AgentCore is available in $currentRegion" -ForegroundColor Green

# Step 4: Check Python availability
Write-Host "`n[4/7] Checking Python installation..." -ForegroundColor Yellow
Write-Host "      (Required for running the agent locally)" -ForegroundColor Gray

# Try to get Python version (use 'py' which is the Windows Python Launcher)
$pythonVersion = py --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "      [X] Python 3.8+ is required but not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "      Please install Python 3.8 or later:" -ForegroundColor Yellow
    Write-Host "        https://www.python.org/downloads/" -ForegroundColor Cyan
    exit 1
}

Write-Host "      [OK] $pythonVersion" -ForegroundColor Green

# Step 5: Check Node.js availability
Write-Host "`n[5/7] Checking Node.js installation..." -ForegroundColor Yellow
Write-Host "      (Required for frontend development server)" -ForegroundColor Gray
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "      [X] Node.js 18+ is required but not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "      Please install Node.js 18 or later:" -ForegroundColor Yellow
    Write-Host "        https://nodejs.org/en/download/" -ForegroundColor Cyan
    exit 1
}

$nodeVersion = node --version 2>&1
Write-Host "      [OK] Node.js $nodeVersion" -ForegroundColor Green

# Step 6: Install dependencies
Write-Host "`n[6/7] Installing dependencies..." -ForegroundColor Yellow

# Install agent dependencies if needed
Write-Host "      Installing agent dependencies..." -ForegroundColor Gray
Write-Host "      (bedrock-agentcore for local HTTP server, strands-agents framework, boto3 for AWS)" -ForegroundColor DarkGray
if (-not (Test-Path "agent/venv")) {
    Write-Host "      Creating Python virtual environment..." -ForegroundColor DarkGray
    Push-Location agent
    py -m venv venv
    Pop-Location
}

# Always install/update requirements to ensure all packages are present
Push-Location agent
& "venv/Scripts/Activate.ps1"
Write-Host "      Installing Python packages from requirements.txt..." -ForegroundColor DarkGray
pip install --no-cache-dir -q -r requirements.txt 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "      [OK] Agent dependencies installed" -ForegroundColor Green
} else {
    Write-Host "      [ERROR] Failed to install agent dependencies" -ForegroundColor Red
    Write-Host "      Trying to continue anyway..." -ForegroundColor Yellow
}
Pop-Location

# Install frontend dependencies if needed
Write-Host "      Installing frontend dependencies..." -ForegroundColor Gray
Push-Location frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "      Running npm install..." -ForegroundColor DarkGray
    npm install --silent 2>&1 | Out-Null
} else {
    Write-Host "      Verifying npm dependencies..." -ForegroundColor DarkGray
    npm install --silent 2>&1 | Out-Null
}
if ($LASTEXITCODE -eq 0) {
    Write-Host "      [OK] Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "      [WARNING] npm install reported warnings, but continuing..." -ForegroundColor Yellow
}
Pop-Location

# Create local environment file for frontend
Write-Host "      Setting up local environment configuration..." -ForegroundColor Gray

# Remove any production environment file
if (Test-Path "frontend/.env.production.local") {
    Remove-Item "frontend/.env.production.local"
}

$envContent = @"
VITE_LOCAL_DEV=true
VITE_AGENT_RUNTIME_URL=/api
"@

$envContent | Out-File -FilePath "frontend/.env.local" -Encoding UTF8

Write-Host "      [OK] Created local development environment configuration" -ForegroundColor Green

# Step 7: Start services
Write-Host "`n[7/7] Starting local development services..." -ForegroundColor Yellow

Write-Host ""
Write-Host "Backend will be available at: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Frontend will be available at: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Local Development Mode:" -ForegroundColor Yellow
Write-Host "  • MCP tools use local file system (agent/local_data/)" -ForegroundColor Gray
Write-Host "  • No Lambda or S3 required for local testing" -ForegroundColor Gray
Write-Host "  • Production uses Lambda + S3 (strands_agent.py)" -ForegroundColor Gray
Write-Host ""
Write-Host "Development Workflow:" -ForegroundColor Yellow
Write-Host "  • Changes to frontend\ files -> Immediate hot reload" -ForegroundColor Gray
Write-Host "  • Changes to agent\ files -> Restart this script (Ctrl+C then re-run)" -ForegroundColor Gray
Write-Host "  • Test with files in agent\local_data\" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Start AgentCore backend in background
Write-Host "Starting AgentCore backend..." -ForegroundColor Blue
Write-Host "  -> Backend terminal will open in a new window" -ForegroundColor Gray
Write-Host "  -> Using local file operations (no Lambda/S3)" -ForegroundColor DarkGray
$backendCmd = "cd '$PWD\agent'; & '.\venv\Scripts\Activate.ps1'; `$env:PYTHONIOENCODING='utf-8'; py strands_agent_local.py; Write-Host '`nBackend stopped. Press any key to close...'; `$null = `$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend dev server in background
Write-Host "Starting frontend dev server..." -ForegroundColor Magenta
Write-Host "  -> Frontend terminal will open in a new window" -ForegroundColor Gray
$frontendCmd = "cd '$PWD\frontend'; npm run dev; Write-Host '`nFrontend stopped. Press any key to close...'; `$null = `$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru

Write-Host ""
Write-Host "[OK] Services started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Two terminal windows should now be open:" -ForegroundColor Yellow
Write-Host "  1. Backend (Python agent) on http://localhost:8080" -ForegroundColor Cyan
Write-Host "  2. Frontend (Vite dev server) on http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "  - Press Ctrl+C in this window, OR" -ForegroundColor Gray
Write-Host "  - Close the backend and frontend terminal windows" -ForegroundColor Gray
Write-Host ""

# Function to cleanup
function Cleanup {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Red
    if ($backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] Backend stopped" -ForegroundColor Gray
    }
    if ($frontendProcess -and !$frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] Frontend stopped" -ForegroundColor Gray
    }
    Write-Host "All services stopped." -ForegroundColor Green
}

# Register cleanup on Ctrl+C
try {
    # Wait for user to press Ctrl+C
    while ($true) {
        Start-Sleep -Seconds 2
        # Check if processes are still running
        $backendProcess.Refresh()
        $frontendProcess.Refresh()
        
        if ($backendProcess.HasExited -and $frontendProcess.HasExited) {
            Write-Host ""
            Write-Host "Both services have stopped." -ForegroundColor Yellow
            break
        }
    }
} catch {
    # Handle Ctrl+C
} finally {
    Cleanup
}
