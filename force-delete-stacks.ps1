# Force delete all AgentCore stacks in correct dependency order
Write-Host "=== Force Delete AgentCore Stacks ===" -ForegroundColor Cyan
Write-Host "This will delete all AgentCore stacks in the correct order" -ForegroundColor Yellow
Write-Host ""

# Verify AWS credentials first
$callerIdentity = aws sts get-caller-identity 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] AWS credentials not configured or expired" -ForegroundColor Red
    Write-Host "Please refresh your AWS credentials and try again" -ForegroundColor Yellow
    exit 1
}

$accountId = ($callerIdentity | ConvertFrom-Json).Account
Write-Host "AWS Account: $accountId" -ForegroundColor Green

# Get current region
$currentRegion = if ($env:AWS_DEFAULT_REGION) { $env:AWS_DEFAULT_REGION } elseif ($env:AWS_REGION) { $env:AWS_REGION } else { aws configure get region }
Write-Host "Region: $currentRegion" -ForegroundColor Green
Write-Host ""

# Ensure CDK execution role exists with proper permissions (needed for stack deletion)
$cdkExecRoleName = "cdk-hnb659fds-cfn-exec-role-$accountId-$currentRegion"
Write-Host "Verifying CDK execution role: $cdkExecRoleName" -ForegroundColor Yellow
$roleCheck = aws iam get-role --role-name $cdkExecRoleName 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  Creating missing CDK execution role..." -ForegroundColor Cyan
    
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
        aws iam attach-role-policy --role-name $cdkExecRoleName --policy-arn arn:aws:iam::aws:policy/AdministratorAccess | Out-Null
        Write-Host "  Role created with AdministratorAccess" -ForegroundColor Green
        Start-Sleep -Seconds 5
    } else {
        Write-Host "  [ERROR] Failed to create execution role" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  Role exists" -ForegroundColor Green
}

Write-Host ""

# Delete stacks in correct dependency order (reverse of deployment)
$stacks = @("AgentCoreFrontend", "AgentCoreRuntime", "AgentCoreAuth", "AgentCoreInfra", "AgentCoreLambdaTools", "AgentCoreEcs", "AgentCoreMcp")

foreach ($stackName in $stacks) {
    Write-Host "Deleting $stackName..." -ForegroundColor Yellow
    
    # Check if stack exists
    $stackStatus = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].StackStatus' --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Stack does not exist, skipping" -ForegroundColor Gray
        continue
    }
    
    Write-Host "  Current status: $stackStatus" -ForegroundColor Gray
    
    # Skip if already being deleted
    if ($stackStatus -match "DELETE_IN_PROGRESS") {
        Write-Host "  Already deleting, waiting..." -ForegroundColor Cyan
    } else {
        # Initiate deletion
        aws cloudformation delete-stack --stack-name $stackName 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [WARNING] Failed to initiate deletion" -ForegroundColor Yellow
            continue
        }
    }
    
    # Wait for deletion with timeout
    Write-Host "  Waiting for deletion..." -ForegroundColor Gray
    $timeout = 600 # 10 minutes
    $elapsed = 0
    $interval = 10
    
    while ($elapsed -lt $timeout) {
        $status = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].StackStatus' --output text 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  $stackName deleted successfully" -ForegroundColor Green
            break
        }
        
        if ($status -match "DELETE_FAILED") {
            Write-Host "  [ERROR] Deletion failed" -ForegroundColor Red
            Write-Host "  Failure reasons:" -ForegroundColor Yellow
            aws cloudformation describe-stack-events --stack-name $stackName --max-items 5 --query "StackEvents[?ResourceStatus=='DELETE_FAILED'].{Resource:LogicalResourceId,Reason:ResourceStatusReason}" --output table --no-cli-pager
            break
        }
        
        if ($status -match "DELETE_COMPLETE") {
            Write-Host "  $stackName deleted" -ForegroundColor Green
            break
        }
        
        Start-Sleep -Seconds $interval
        $elapsed += $interval
        
        if ($elapsed % 30 -eq 0) {
            Write-Host "  Still deleting... ($elapsed seconds)" -ForegroundColor Gray
        }
    }
    
    if ($elapsed -ge $timeout) {
        Write-Host "  [WARNING] Deletion timeout" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

Write-Host "=== Deletion Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Checking for remaining stacks..." -ForegroundColor Yellow
$remainingStacks = aws cloudformation list-stacks --query "StackSummaries[?StackStatus!='DELETE_COMPLETE' && starts_with(StackName, 'AgentCore')].{Name:StackName, Status:StackStatus}" --output table --no-cli-pager

if ($remainingStacks) {
    Write-Host "Remaining stacks:" -ForegroundColor Yellow
    Write-Host $remainingStacks
} else {
    Write-Host "All AgentCore stacks deleted successfully" -ForegroundColor Green
}
