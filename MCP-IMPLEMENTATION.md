# MCP Server Implementation Summary

## Overview
Successfully implemented an MCP (Model Context Protocol) server integrated with AWS Bedrock AgentCore using Lambda functions and S3 for file storage.

## Architecture

### Components Created

1. **S3 Bucket** (`mcp-client-details-{account}-{region}`)
   - Stores client detail JSON files
   - Versioning enabled for file history
   - S3-managed encryption
   - Located in `cdk/lib/mcp-stack.ts`

2. **Example JSON Files** (Auto-seeded to S3)
   - `eon-report.json` - Eon Energy Solutions client details
   - `british-gas-report.json` - British Gas client details  
   - `yorkshire-water-report.json` - Yorkshire Water client details
   - Located in `cdk/assets/`

3. **Lambda Functions** (Node.js 22.x)
   - **ListFilesFunction** - Lists all JSON files in S3 bucket
   - **ReadFileFunction** - Reads specific file by name from S3
   - Both have S3 read permissions
   - Both can be invoked by AgentCore runtime role

4. **Agent Tools** (Updated in `strands_agent.py`)
   - `list_files()` - Invokes ListFilesFunction via Lambda client
   - `read_file(filename)` - Invokes ReadFileFunction via Lambda client
   - Both use boto3 Lambda client with function ARNs from environment variables

## Files Created/Modified

### New Files
- `cdk/lib/mcp-stack.ts` - MCP infrastructure stack
- `cdk/assets/eon-report.json` - Example client data
- `cdk/assets/british-gas-report.json` - Example client data
- `cdk/assets/yorkshire-water-report.json` - Example client data
- `agent/strands_agent_local.py` - Local development version (filesystem)
- `agent/local_data/*.json` - Local development data files
- `LOCAL-VS-PRODUCTION.md` - Documentation for dual-mode setup

### Modified Files
- `cdk/bin/app.ts` - Added McpStack instantiation and dependency chain
- `cdk/lib/runtime-stack.ts` - Added Lambda function ARNs to environment variables
- `cdk/lib/infra-stack.ts` - Added Lambda invoke permissions to agent role
- `agent/strands_agent.py` - Replaced hardcoded getFiles() with Lambda-backed tools
- `dev-local.ps1` - Updated to use `strands_agent_local.py` for local development
- `README.md` - Added MCP local development documentation

## Integration Pattern

**AgentCore ↔ Lambda Integration (No Action Groups)**

AgentCore doesn't support action groups like Bedrock Agents. Instead, we use:

1. **Environment Variables**: Lambda ARNs passed to AgentCore container
   ```typescript
   environmentVariables: {
     LIST_FILES_FUNCTION_ARN: props.listFilesFunctionArn,
     READ_FILE_FUNCTION_ARN: props.readFileFunctionArn,
   }
   ```

2. **IAM Permissions**: Agent runtime role can invoke Lambda functions
   ```typescript
   agentRole.addToPolicy(new iam.PolicyStatement({
     actions: ['lambda:InvokeFunction'],
     resources: [`arn:aws:lambda:${region}:${account}:function:AgentCoreMcp-*`],
   }));
   ```

3. **Direct Invocation**: Agent code uses boto3 to call Lambda
   ```python
   lambda_client.invoke(
     FunctionName=os.environ.get('LIST_FILES_FUNCTION_ARN'),
     InvocationType='RequestResponse',
     Payload=json.dumps({...})
   )
   ```

## Deployment Order

1. **AgentCoreInfra** - Creates IAM role, ECR, CodeBuild
2. **AgentCoreAuth** - Creates Cognito User Pool  
3. **AgentCoreMcp** - Creates Lambda functions and S3 bucket (depends on InfraStack)
4. **AgentCoreRuntime** - Creates AgentCore runtime (depends on McpStack)
5. **AgentCoreFrontend** - Creates CloudFront distribution

## Benefits

✅ **Reusable Lambda functions** - Can be called by any AWS service  
✅ **Automatic file seeding** - Example JSON files deployed via S3 BucketDeployment  
✅ **Clean integration** - Agent tools transparently call Lambda functions  
✅ **Type-safe parameters** - Lambda functions handle event parsing for multiple formats  
✅ **Error handling** - 404 for missing files, 500 for server errors  
✅ **Future-ready** - Easy to add API Gateway later for external access

## Next Steps

### Local Development
```powershell
.\dev-local.ps1
```
- Uses `strands_agent_local.py` with local filesystem
- Reads from `agent/local_data/` directory
- No Lambda or S3 required
- Fast iteration cycle

### Production Deployment
```powershell
cd cdk
npm install
cdk deploy --all
```
- Uses `strands_agent.py` with Lambda + S3
- Full AWS infrastructure deployment
- Scalable and production-ready

### Test the MCP Tools
- Ask agent: "What files do I have?" → Calls `list_files()`
- Ask agent: "Read the Eon report" → Calls `read_file('eon-report.json')`
- Ask agent: "Show me British Gas details" → Calls `read_file('british-gas-report.json')`

For more details on local vs production modes, see [LOCAL-VS-PRODUCTION.md](./LOCAL-VS-PRODUCTION.md)
