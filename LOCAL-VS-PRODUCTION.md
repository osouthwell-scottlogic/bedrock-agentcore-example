# Local Development vs Production

This project supports two execution modes for the MCP file operations:

## Local Development Mode

**File**: `agent/strands_agent_local.py`

- Uses local file system operations
- Reads/writes to `agent/local_data/` directory
- No AWS Lambda or S3 required
- Perfect for rapid development and testing
- Started by `dev-local.ps1` script

### Local Data Files
- `agent/local_data/eon-report.json`
- `agent/local_data/british-gas-report.json`
- `agent/local_data/yorkshire-water-report.json`

### Running Locally
```powershell
.\dev-local.ps1
```

The script will:
1. Verify AWS credentials (for Bedrock model access)
2. Install dependencies
3. Start backend on http://localhost:8080
4. Start frontend on http://localhost:5173

## Production Mode

**File**: `agent/strands_agent.py`

- Uses AWS Lambda functions for file operations
- Reads from S3 bucket (`mcp-client-details-{account}-{region}`)
- Requires deployed Lambda functions and S3 infrastructure
- Deployed via CDK to AWS AgentCore

### Architecture
```
AgentCore Runtime (Container)
    ↓
strands_agent.py (boto3)
    ↓
Lambda Functions (list_files, read_file)
    ↓
S3 Bucket (client-details/*.json)
```

### Deploying to Production
```powershell
cd cdk
npm install
cdk deploy --all
```

## Key Differences

| Feature | Local Dev | Production |
|---------|-----------|------------|
| **Agent File** | `strands_agent_local.py` | `strands_agent.py` |
| **Storage** | Local filesystem | S3 Bucket |
| **File Operations** | Direct Python I/O | Lambda + boto3 |
| **Dependencies** | Python stdlib | boto3, Lambda |
| **Startup** | `dev-local.ps1` | CDK deploy |
| **Use Case** | Development/Testing | Production deployment |

## Tool Functions

Both modes provide the same tools to the agent:

### `list_files()`
- **Local**: Lists `*.json` files in `agent/local_data/`
- **Production**: Invokes ListFilesFunction Lambda → lists S3 objects

### `read_file(filename)`
- **Local**: Reads file from `agent/local_data/{filename}`
- **Production**: Invokes ReadFileFunction Lambda → reads from S3

## Adding New Files

### Local Development
Simply add JSON files to `agent/local_data/`:
```powershell
cp my-report.json agent/local_data/
```

### Production
Upload to S3 bucket:
```powershell
aws s3 cp my-report.json s3://mcp-client-details-{account}-{region}/client-details/
```

Or update `cdk/assets/` and redeploy.

## Environment Variables

### Local Mode
- No special environment variables needed
- Uses local file paths

### Production Mode
- `LIST_FILES_FUNCTION_ARN` - ARN of ListFilesFunction Lambda
- `READ_FILE_FUNCTION_ARN` - ARN of ReadFileFunction Lambda
- Set automatically by CDK in `runtime-stack.ts`

## Testing

### Local Testing
```powershell
.\dev-local.ps1
# Open http://localhost:5173
# Ask: "What files do I have?"
# Ask: "Read the Eon report"
```

### Production Testing
After deployment, use the CloudFront URL provided in the stack outputs.

## Troubleshooting

### Local Mode Issues
- **"No files found"**: Check `agent/local_data/` exists and contains JSON files
- **Backend won't start**: Verify Python dependencies installed (`pip install -r requirements.txt`)

### Production Mode Issues
- **Lambda invoke errors**: Check IAM permissions in `infra-stack.ts`
- **File not found**: Verify files in S3 bucket at `client-details/` prefix
- **Missing environment variables**: Check `runtime-stack.ts` environment configuration
