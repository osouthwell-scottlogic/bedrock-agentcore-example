# Amazon Bedrock Agents - Bank X Financial Assistant

Full-stack AI financial advisor built with **Amazon Bedrock Agents**. Demonstrates real-world use case: personalized bond marketing with customer profiling, product research, and automated email campaigns.

The system uses **Bedrock Agents** with:
- **Knowledge Base** for semantic search over customer/product/bond data
- **Action Groups** for email operations, market search, and file management
- **Guardrails** for content safety and PII protection
- **Multi-step approval workflow** for email sends

## Architecture

![Architecture](./img/architecture_diagram.svg)

**Flow:**
1. Browser loads React app from CloudFront/S3
2. User authenticates with Cognito, receives JWT token
3. Browser calls AgentCore directly with JWT Bearer token
4. AgentCore validates JWT and processes agent requests
5. AgentCore invokes Lambda functions (MCP tools) for customer/product data
6. Lambda functions read/write data from S3 bucket

**Multi-Agent Architecture:**
```
User Request
     ↓
Agent Router (Coordinator)
     ↓
┌────────────┬────────────┬────────────┐
│  Customer  │  Product   │  Marketing │
│   Agent    │   Agent    │   Agent    │
└────────────┴────────────┴────────────┘
     ↓
MCP Tools (Lambda/Local)
```

| Agent | Responsibility | Key Tools |
|-------|---------------|-----------|
| **Customer Service** | Customer queries, profiles | `list_customers()`, `get_customer_profile()` |
| **Product Research** | Products, market data | `list_bonds()`, `get_product_details()`, `search_market_data()` |
| **Marketing** | Email campaigns | `send_email()`, `get_recent_emails()` |
| **Coordinator** | Route & orchestrate | Calls other agents as needed |

## Quick Start

### Cloud Deployment

#### Prerequisites
- **AWS CLI v2.31.13 or later** ([Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
  - Check your version: `aws --version`
  - AgentCore support was added in AWS CLI v2.31.13 (January 2025)
- **Node.js 22+** installed
- **AWS credentials** configured with permissions for CloudFormation, Lambda, S3, ECR, CodeBuild, API Gateway, Cognito, and IAM
- **No Docker required!** (CodeBuild handles container builds)

#### ⚠️ Region Requirements

**Amazon Bedrock AgentCore is only available in specific AWS regions.** Verify availability in your target region at the [AWS AgentCore Regions Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html).

#### One-Command Deploy

**Windows (PowerShell):**
```powershell
.\deploy-bedrock.ps1
```

**macOS/Linux (Bash):**
```bash
chmod +x deploy-bedrock.sh scripts/*.sh
./deploy-bedrock.sh
```

**Advanced Options:**
```powershell
# Dry run (test without deploying)
.\deploy-bedrock.ps1 --dry-run

# Verbose output (detailed logging)
.\deploy-bedrock.ps1 --verbose

# Combine flags
.\deploy-bedrock.ps1 --dry-run --verbose
```

**What It Does:**
1. ✅ Checks Bedrock model access (Claude 3.5 Haiku/Sonnet, Titan Embed v2)
2. 📦 Installs CDK dependencies and deploys all stacks
3. 🔄 **Automatically syncs Knowledge Base** (5-10 minutes)
4. 🤖 **Automatically prepares Bedrock Agent**
5. 🎉 Displays your CloudFront URL - ready to use!

**Time:** ~20-25 minutes (fully automated, including KB sync and agent prep)

**Done!** Your Bedrock Agents-powered app is live at the CloudFront URL shown in the output.

#### Post-Deployment Notes

The deployment is **fully automated**. If you see warnings during post-deployment automation:

- **Knowledge Base sync timeout:** Check sync status with:
  ```bash
  aws bedrock-agent get-ingestion-job \
    --knowledge-base-id <KB_ID> \
    --data-source-id <DS_ID> \
    --ingestion-job-id <JOB_ID> \
    --region <REGION>
  ```

- **Agent preparation failed:** Prepare manually with:
  ```bash
  aws bedrock-agent prepare-agent \
    --agent-id <AGENT_ID> \
    --region <REGION>
  ```

Or use the AWS Console as shown in the warning messages.

#### Test Your App

1. Open the CloudFront URL from deployment output
2. Click **"Sign In"** in the header
3. Create an account (email verification required)
4. Try these prompts:
   - "List all available bond products"
   - "Show me customers interested in government bonds"
   - "Email customers about Government Bond Y" (demonstrates approval workflow)
   - "What are the recent emails we've sent?"
   - "Research market trends for corporate bonds"

### Local Development Mode

For rapid development without AWS deployment:

#### Prerequisites
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **AWS credentials** with Bedrock model invocation permissions (uses `global.anthropic.claude-haiku-4-5-20251001-v1:0`)

#### Start Local Development

**Windows (PowerShell):**
```powershell
.\dev-local.ps1
```

**macOS/Linux (Bash):**
```bash
chmod +x dev-local.sh
./dev-local.sh
```

This will:
1. Create Python virtual environment and install dependencies
2. Install frontend dependencies
3. Start AgentCore agent on `http://localhost:8080`
4. Start frontend dev server on `http://localhost:5173`
5. Configure frontend to call local agent (no auth required)

#### Local Development Features
- ✅ Frontend hot reload (Vite dev server)
- ✅ Fast agent restart cycle (no deployment)
- ✅ Authentication bypassed
- ✅ MCP tools use local file system (`agent/local_data/`)
- ✅ Same agent framework as production
- ✅ No Docker, Lambda, or S3 needed

#### Development Workflow
- **Frontend changes** (`frontend/`): Hot reload automatically
- **Agent changes** (`agent/`): Ctrl+C, then re-run script
- **Test MCP tools**: Add JSON files to `agent/local_data/`

#### Local vs Production Data Storage
- **Local**: Files in `agent/local_data/`
  - Customer data: `bank-x-customers.json`
  - Product data: `government-bond-y.json`, etc.
  - Emails: `sent_emails/YYYY-MM-DD/`
- **Production**: S3 via Lambda functions

## Project Structure

```
.
├── agent/                          # Bedrock Agent implementation
│   ├── agents/                     # Specialized agents
│   │   ├── customer_agent.py       # Production customer agent
│   │   ├── customer_agent_local.py # Local customer agent
│   │   ├── product_agent.py        # Production product agent
│   │   ├── product_agent_local.py  # Local product agent
│   │   ├── marketing_agent.py      # Production marketing agent
│   │   └── marketing_agent_local.py# Local marketing agent
│   ├── agent_router.py             # Coordinator agent
│   ├── strands_agent.py            # Production entry point
│   ├── strands_agent_local.py      # Local entry point
│   ├── local_data/                 # Local development data
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                  # Container for Lambda
├── cdk/                            # AWS CDK infrastructure
│   ├── lib/
│   │   ├── action-schemas/         # OpenAPI action schemas
│   │   ├── bedrock-kb-stack.ts     # Knowledge Base
│   │   ├── bedrock-agent-stack.ts  # Agent + Guardrails
│   │   └── bedrock-agentcore-stack.ts # AgentCore API
│   └── bin/
│       └── bedrock-agentcore.ts    # CDK app
├── frontend/                       # React + TypeScript UI
│   ├── src/
│   │   ├── components/             # React components
│   │   │   └── chat/               # Chat UI components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── styles/                 # CSS modules & theme
│   │   ├── agentcore.ts            # AgentCore client
│   │   └── App.tsx                 # Main app
│   └── package.json
├── lambda/                         # MCP Tools (Lambda functions)
│   ├── get-customer/
│   ├── get-product/
│   ├── list-bonds/
│   ├── list-customers/
│   ├── send-email/                 # Email with approval gate
│   ├── get-recent-emails/
│   ├── search-market/
│   ├── list-files/
│   └── read-file/
├── scripts/
│   └── build-frontend.sh           # Frontend build script
├── deploy-bedrock.ps1              # Windows deployment
├── deploy-bedrock.sh               # Linux/Mac deployment
├── dev-local.ps1                   # Windows local dev
└── dev-local.sh                    # Linux/Mac local dev
```

## Key Features

### Bedrock Agent Capabilities
- **Semantic Search**: Knowledge Base with OpenSearch Serverless
- **Action Groups**: 9 custom tools for customer/product/email operations
- **Guardrails**: Content filtering and PII protection
- **Multi-Agent System**: Specialized agents coordinated by router
- **Streaming Responses**: Real-time token streaming to frontend

### Frontend Features
- **Vaporwave UI**: Modern pastel gradient design with animations
- **Real-time Streaming**: Token-by-token response display
- **Smart Suggestions**: AI-generated contextual prompts
- **Message Feedback**: Thumbs up/down and copy functionality
- **Authentication**: Cognito integration with JWT
- **Responsive Design**: Scalable component architecture

### Email Approval Workflow
When users request to send emails:
1. Agent calls `send_email` tool
2. Lambda function returns approval request (not sent yet)
3. Frontend shows approval UI with email preview
4. User reviews and approves/rejects
5. If approved, agent calls tool again with `approval_confirmed=true`
6. Email is sent and stored

## Deployment Scripts

### `deploy-bedrock.ps1` / `deploy-bedrock.sh`
- Installs CDK dependencies
- Builds frontend (Vite production build)
- Deploys all CDK stacks:
  - Knowledge Base stack (OpenSearch + S3 data source)
  - Agent stack (Bedrock Agent + Guardrails + Action Groups)
  - AgentCore stack (API Gateway + Lambda)
  - Frontend stack (S3 + CloudFront + Cognito)
- Outputs CloudFront URL

### `dev-local.ps1` / `dev-local.sh`
- Creates Python virtual environment
- Installs agent dependencies
- Installs frontend dependencies
- Starts local agent server (port 8080)
- Starts frontend dev server (port 5173)
- Sets `VITE_LOCAL_DEV=true` environment variable

## Environment Variables

### Production (Frontend)
- Automatically set by CDK during build:
  - `VITE_AGENTCORE_API_URL` - AgentCore API Gateway URL
  - `VITE_USER_POOL_ID` - Cognito User Pool ID
  - `VITE_USER_POOL_CLIENT_ID` - Cognito Client ID
  - `VITE_LOCAL_DEV=false`

### Local Development (Frontend)
- Set by `dev-local.*` scripts:
  - `VITE_LOCAL_DEV=true` - Enables local mode
  - `VITE_AGENTCORE_API_URL=http://localhost:8080` - Local agent URL

## Testing

### Test Multi-Agent Routing
```
"List customers interested in government bonds"
→ Routes to Customer Agent → uses list_customers()

"What are the details of Corporate Bond A?"
→ Routes to Product Agent → uses get_product_details()

"Email customers about Government Bond Y"
→ Routes to Marketing Agent → uses send_email() with approval

"Show me market trends and email qualified customers"
→ Router orchestrates Product + Marketing agents
```

### Test Knowledge Base
```
"What is Bank X's customer profiling strategy?"
→ Searches Knowledge Base documents

"How does the bond selection process work?"
→ Retrieves relevant product documentation
```

### Test Guardrails
```
"My SSN is 123-45-6789"
→ PII detected and blocked

"Inappropriate content..."
→ Content filtered by guardrails
```

## Troubleshooting

### Deployment Issues

**Error: Model access check failed**
- **Cause:** Required Bedrock models not enabled in your AWS account
- **Solution:** 
  1. Open [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
  2. Navigate to **Model access**
  3. Click **Manage model access**
  4. Enable:
     - `anthropic.claude-haiku-4-5-20251001-v1:0` (Claude Haiku 4.5)
     - `anthropic.claude-sonnet-4-5-20250929-v1:0` (Claude Sonnet 4.5)
     - `amazon.titan-embed-text-v2:0` (Amazon Titan Embed v2)
  5. Wait for access to be granted (usually instant)
  6. Re-run deployment script

**Error: AWS CLI version too old**
- **Solution:** Update to AWS CLI v2.31.13+
- **Check:** `aws --version`

**Warning: Knowledge Base sync timeout**
- **Cause:** KB ingestion takes longer than 10 minutes (normal for large datasets)
- **Solution:** The deployment continues successfully. Check sync status:
  ```bash
  aws bedrock-agent get-ingestion-job \
    --knowledge-base-id <KB_ID> \
    --data-source-id <DS_ID> \
    --ingestion-job-id <JOB_ID> \
    --region <REGION>
  ```
  Or use AWS Console: **Bedrock > Knowledge Bases > Select KB > View Sync Status**

**Warning: Agent preparation failed**
- **Solution:** Prepare manually:
  ```bash
  aws bedrock-agent prepare-agent --agent-id <AGENT_ID> --region <REGION>
  ```
  Or use AWS Console: **Bedrock > Agents > Select Agent > Prepare**

**Error: CDK deployment fails**
- **Verify:** AWS credentials have required permissions (CloudFormation, Lambda, S3, Bedrock, etc.)
- **Check:** Stack-specific error in CloudFormation console
- **Tip:** Run with `--verbose` flag for detailed logs

### Local Development Issues

**Error: Python version too old**
- Solution: Install Python 3.8+
- Check: `python --version`

**Error: Node version too old**
- Solution: Install Node.js 18+
- Check: `node --version`

**Error: Port 8080 already in use**
- Solution: Kill process on port 8080
- Windows: `Get-Process -Id (Get-NetTCPConnection -LocalPort 8080).OwningProcess | Stop-Process`
- Linux/Mac: `lsof -ti:8080 | xargs kill`

**Error: AWS credentials not found**
- Solution: Configure AWS CLI
- Run: `aws configure`

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [CONTRIBUTING.md](CONTRIBUTING.md) for security issue reporting.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock Agents Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [React Documentation](https://react.dev/)
