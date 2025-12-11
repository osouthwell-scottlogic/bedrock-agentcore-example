# Amazon Bedrock AgentCore - Bank X Financial Assistant

Full-stack AI financial advisor built with [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/resources/). Demonstrates real-world use case: personalized bond marketing with customer profiling, product research, and automated email campaigns.

The agent is built with the [Strands Agents framework](https://github.com/strands-agents/) and integrates MCP (Model Context Protocol) tools for customer management, bond product research, market analysis, and email marketing. Features authentication, multi-step workflows with approval gates, and local development mode.

## Architecture

![Architecture](./img/architecture_diagram.svg)

Flow:
1. Browser loads React app from CloudFront/S3
2. User authenticates with Cognito, receives JWT token
3. Browser calls AgentCore directly with JWT Bearer token
4. AgentCore validates JWT and processes agent requests
5. AgentCore invokes Lambda functions (MCP tools) for customer/product data
6. Lambda functions read/write data from S3 bucket

## Quick Start

### Cloud Deployment

#### Prerequisites
- **AWS CLI v2.31.13 or later** installed and configured ([Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
  - Check your version: `aws --version`
  - AgentCore support was added in AWS CLI v2.31.13 (January 2025)
- **Node.js 22+** installed
- **AWS credentials** configured with permissions for CloudFormation, Lambda, S3, ECR, CodeBuild, API Gateway, Cognito, and IAM via:
  - `aws configure` (access key/secret key)
  - AWS SSO: `aws sso login --profile <profile-name>`
  - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **No Docker required!** (CodeBuild handles container builds)

#### ⚠️ Important: Region Requirements

**Amazon Bedrock AgentCore is only available in specific AWS regions.**

Before deploying, verify AgentCore availability in your target region by checking the [AWS AgentCore Regions Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html).

#### One-Command Deploy

**Windows (PowerShell):**
```powershell
.\deploy-all.ps1
```

**macOS/Linux (Bash):**
```bash
chmod +x deploy-all.sh scripts/build-frontend.sh
./deploy-all.sh
```

> **Platform Notes:**
> - **Windows users**: Use the PowerShell script (`.ps1`)
> - **macOS/Linux users**: Use the bash script (`.sh`)
> - Both scripts perform identical operations and produce the same infrastructure
> - If you prefer PowerShell on macOS: `brew install --cask powershell` then run `pwsh deploy-all.ps1`

**Time:** ~10 minutes (most time is CodeBuild creating the container image)

**Done!** Your app is live at the CloudFront URL shown in the output.

> **Architecture Note**: This demo uses a simple architecture where the React frontend calls AgentCore directly with JWT authentication.

#### Test Your App

1. Open the CloudFront URL from deployment output
2. **Click "Sign In"** in the header
3. **Create an account:**
   - Click "Sign up"
   - Enter your email and password (min 8 chars, needs uppercase, lowercase, digit)
   - Check your email for verification code
   - Enter the code to confirm
4. You'll be automatically signed in
5. Enter a prompt: "What is 42 + 58?"
6. See the response from the agent

Try these prompts:
- "List all available bond products"
- "Show me customers who might be interested in government bonds"
- "Email customers about Government Bond Y" (demonstrates approval workflow)
- "What are the recent emails we've sent?"
- "Research market trends for corporate bonds"

### Local Development Mode

For rapid development without AWS deployment:

**Prerequisites:**
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **AWS credentials** configured with permissions for Bedrock model invocation. The default example invokes Anthropic Claude Haiku 4.5, model id `global.anthropic.claude-haiku-4-5-20251001-v1:0`.

**Start Local Development:**

**macOS/Linux:**
```bash
chmod +x dev-local.sh
./dev-local.sh
```

**Windows (PowerShell):**
```powershell
.\dev-local.ps1
```

This will:
1. Create a Python virtual environment and install agent dependencies
2. Install frontend dependencies
3. Start the AgentCore agent locally on `http://localhost:8080`
4. Start the frontend dev server on `http://localhost:5173`
5. Configure the frontend to call the local agent (no authentication required)

**Local Development Features:**
- ✅ Frontend hot reload (Vite dev server)
- ✅ Fast agent restart cycle (no deployment needed)
- ✅ Authentication with Cognito is bypassed
- ✅ MCP tools use local file system (no Lambda/S3 needed)
- ✅ Same agent framework as production
- ✅ Rapid iteration without AWS deployment

**How Local Development Works:**
- `python strands_agent_local.py` starts your agent as a regular Python process
- `app.run()` creates HTTP server on `localhost:8080` (via `bedrock-agentcore` library)
- Frontend sends POST requests to `/api/invocations`
- Agent executes directly in Python, calls AWS Bedrock APIs
- MCP tools read from `agent/local_data/` directory
- No Docker, Lambda, or S3 needed - just Python + web server

**Development Workflow:**
- **Frontend changes** (`frontend/` files): Hot reload automatically via Vite
- **Agent changes** (`agent/` files): Restart required - Ctrl+C then re-run script
- **Test MCP tools**: Add JSON files to `agent/local_data/`

**MCP Tools in Local vs Production:**
- **Local**: Files stored in `agent/local_data/` (filesystem)
  - Customer data: `bank-x-customers.json`
  - Product data: `government-bond-y.json`, `corporate-bond-a.json`, etc.
  - Email storage: `sent_emails/YYYY-MM-DD/` (plain text files)
- **Production**: Files stored in S3, accessed via Lambda functions
  - Customer data: S3 `mcp-bank-x-data-*/customer-data/`
  - Product data: S3 `mcp-bank-x-data-*/product-data/`
  - Email storage: S3 `mcp-bank-x-data-*/sent-emails/YYYY-MM-DD/`
- See [LOCAL-VS-PRODUCTION.md](./LOCAL-VS-PRODUCTION.md) and [MCP-IMPLEMENTATION.md](./MCP-IMPLEMENTATION.md) for architecture details

**Note:** Agent restart takes ~10 seconds vs ~10 minutes for production deployment.

## Stack Architecture

| Stack Name | Purpose | Key Resources |
|------------|---------|---------------|
| **AgentCoreInfra** | Build infrastructure | ECR Repository, CodeBuild Project, IAM Roles, S3 Bucket |
| **AgentCoreAuth** | Authentication | Cognito User Pool, User Pool Client |
| **AgentCoreMcp** | MCP tools (Bank X data & operations) | Lambda Functions (9), S3 Bucket, Customer/Product Data |
| **AgentCoreRuntime** | Agent runtime with built-in auth | AgentCore Runtime with Cognito JWT Authorizer, Lambda Waiter |
| **AgentCoreFrontend** | Web UI | S3 Bucket, CloudFront Distribution, React App with Auth |

## Project Structure

```
project-root/
├── agent/                     # Agent runtime code
│   ├── strands_agent.py       # Production agent (Lambda + S3)
│   ├── strands_agent_local.py # Local development agent (filesystem)
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # ARM64 container definition
│   ├── .dockerignore          # Docker ignore patterns
│   └── local_data/            # Local development data files
│       ├── bank-x-customers.json
│       ├── government-bond-y.json
│       ├── corporate-bond-a.json
│       ├── green-bond-g.json
│       ├── municipal-bond-m.json
│       └── sent_emails/       # Local email storage
│
├── cdk/                       # Infrastructure as Code
│   ├── bin/
│   │   └── app.ts             # CDK app entry point (5 stacks)
│   ├── lib/
│   │   ├── infra-stack.ts     # Build infrastructure (ECR, IAM, CodeBuild)
│   │   ├── auth-stack.ts      # Cognito authentication
│   │   ├── mcp-stack.ts       # MCP tools (7 Lambda functions + S3)
│   │   ├── runtime-stack.ts   # AgentCore runtime + API
│   │   └── frontend-stack.ts  # CloudFront + S3
│   ├── assets/                # Production data files (deployed to S3)
│   │   ├── bank-x-customers.json
│   │   ├── government-bond-y.json
│   │   ├── corporate-bond-a.json
│   │   ├── green-bond-g.json
│   │   └── municipal-bond-m.json
│   ├── cdk.json               # CDK configuration
│   ├── tsconfig.json          # TypeScript configuration
│   └── package.json           # CDK dependencies
│
├── lambda/                    # MCP Lambda function code
│   ├── list-bonds/            # List available bond products
│   ├── list-customers/        # List Bank X customers
│   ├── get-customer/          # Get customer profile
│   ├── get-product/           # Get product details
│   ├── search-market/         # Market research data
│   ├── send-email/            # Send marketing emails
│   └── get-recent-emails/     # Email history
│
├── frontend/                  # React app (Vite + Cloudscape)
│   ├── src/
│   │   ├── App.tsx            # Main UI component with auth
│   │   ├── AuthModal.tsx      # Login/signup modal
│   │   ├── auth.ts            # Cognito authentication logic
│   │   ├── agentcore.ts       # Direct AgentCore invocation
│   │   └── main.tsx           # React entry point
│   ├── dist/                  # Build output (gitignored)
│   └── package.json           # Frontend dependencies
│
├── scripts/
│   ├── build-frontend.ps1     # Builds React app with AgentCore ARN injection (Windows)
│   └── build-frontend.sh      # Builds React app with AgentCore ARN injection (macOS/Linux)
│
├── deploy-all.ps1             # Main deployment orchestration (Windows)
├── deploy-all.sh              # Main deployment orchestration (macOS/Linux)
├── dev-local.ps1              # Local development mode (Windows)
├── dev-local.sh               # Local development mode (macOS/Linux)
├── MCP-IMPLEMENTATION.md      # MCP architecture documentation
├── LOCAL-VS-PRODUCTION.md     # Dual-mode development guide
└── README.md                  # This file
```

## How It Works

### Deployment Flow

The `deploy-all.ps1` script orchestrates the complete deployment:

1. **Verify AWS credentials** (checks AWS CLI configuration)
2. **Check AWS CLI version** (requires v2.31.13+ for AgentCore support)
3. **Check AgentCore availability** (verifies service is available in your configured region)
4. **Install CDK dependencies** (cdk/node_modules)
5. **Install frontend dependencies** (frontend/node_modules, includes amazon-cognito-identity-js)
6. **Create placeholder frontend build** (for initial deployment)
7. **Bootstrap CDK environment** (sets up CDK deployment resources in your AWS account/region)
8. **Deploy AgentCoreInfra** - Creates build pipeline resources:
   - ECR repository for agent container images
   - IAM role for AgentCore runtime with Lambda invoke permissions
   - S3 bucket for CodeBuild sources
   - CodeBuild project for ARM64 builds
9. **Deploy AgentCoreAuth** - Creates authentication resources:
    - Cognito User Pool (email/password)
    - User Pool Client for frontend
    - Password policy (min 8 chars, uppercase, lowercase, digit)
10. **Deploy AgentCoreMcp** - Creates MCP tools (Bank X business logic):
    - S3 bucket for customer data, products, and sent emails
    - **9 Lambda functions** for MCP tools:
      - **Bank X Business Logic (7 functions used by agent):**
        - ListBondsFunction - Browse bond catalog
        - ListCustomersFunction - Customer directory
        - GetCustomerFunction - Customer profiles
        - GetProductFunction - Product details
        - SearchMarketFunction - Market research
        - SendEmailFunction - Email campaigns
        - GetRecentEmailsFunction - Email history
      - **Legacy Infrastructure (2 functions, not used by agent):**
        - ListFilesFunction - Generic file listing
        - ReadFileFunction - Generic file reading
    - Auto-deploys customer and product data files to S3
11. **Deploy AgentCoreRuntime** - Deploys agent with built-in auth:
    - Uploads agent source code to S3
    - Triggers CodeBuild via Custom Resource
    - **Lambda waiter polls CodeBuild** (5-10 minutes)
    - Creates AgentCore runtime with built-in Cognito JWT authentication
    - Injects Lambda ARNs as environment variables (9 MCP Lambda functions, agent uses 7)
12. **Build frontend with AgentCore ARN and Cognito config, then deploy AgentCoreFrontend**:
    - Retrieves AgentCore Runtime ARN and Cognito config from stack outputs
    - Builds React app with injected configuration
    - S3 bucket for static hosting
    - CloudFront distribution with OAC
    - Deploys React app with authentication UI

### Request Flow

1. User signs in via Cognito (email verification required)
2. Frontend receives JWT access token from Cognito
3. User enters prompt in React UI
4. Frontend sends POST directly to AgentCore `/runtimes/{arn}/invocations` with JWT Bearer token
5. AgentCore validates JWT token with Cognito (built-in authentication)
6. AgentCore executes agent in isolated container (microVM)
7. Agent processes request using Strands framework + Anthropic Claude Haiku 4.5
8. Response returned directly to frontend

## Key Components

### 1. Authentication (`AgentCoreAuth` stack)
- **Cognito User Pool** for user management
- Email-based authentication with verification
- Password policy: min 8 chars, uppercase, lowercase, digit
- **Frontend integration** via amazon-cognito-identity-js
- JWT tokens automatically included in API requests
- Sign in/sign up modal with email confirmation flow
- **JWT Bearer Token Authentication**: Implements AgentCore's built-in JWT authorization (see [JWT Authentication Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-oauth.html#invoke-agent))

### 2. Agent (`agent/strands_agent.py`)
- Built with Strands Agents framework
- Uses Anthropic Claude Haiku 4.5
- **Bank X Financial Marketing Tools:**
  - `list_available_bonds()` - Browse bond product catalog
  - `list_customers()` - View customer directory
  - `get_customer_profile(customer_id)` - Detailed customer profiles with investment preferences
  - `get_product_details(product_name)` - Full bond product specifications
  - `search_market_data(product_type)` - Market research and comparable products
  - `send_email(customer_email, subject, body)` - Send marketing emails (stored in S3)
  - `get_recent_emails(limit)` - View email history
- Multi-step workflow with approval gates for email campaigns
- Wrapped with `@BedrockAgentCoreApp` decorator

### 3. Container Build
- ARM64 architecture (native AgentCore support)
- Python 3.13 slim base image
- Built via CodeBuild (no local Docker required)
- Automatic build on deployment
- Build history and logs in AWS Console

### 4. Lambda Waiter (Critical Component)
- Custom Resource that waits for CodeBuild completion
- Polls every 30 seconds, 15-minute timeout
- Returns minimal response to CloudFormation (<4KB)
- Ensures image exists before AgentCore runtime creation
- **Why needed:** CodeBuild's `batchGetBuilds` response exceeds CloudFormation's 4KB Custom Resource limit

### 5. Direct AgentCore Integration
- Frontend calls AgentCore directly using HTTPS
- JWT Bearer token authentication (Cognito access tokens)
- Built-in Cognito JWT authorizer in AgentCore runtime
- Session ID generation for request tracking

### 6. IAM Permissions
The execution role includes:
- Bedrock model invocation
- ECR image access
- CloudWatch Logs & Metrics
- X-Ray tracing
- AgentCore Identity (workload access tokens)

### 7. MCP Tools (Bank X Business Logic)
The agent uses 7 Lambda-based MCP tools for customer and product operations:

**Customer Management:**
- `list_customers()` - Browse customer directory
- `get_customer_profile(customer_id)` - Full profiles with investment preferences, portfolio value, bond interest

**Product Research:**
- `list_available_bonds()` - Browse bond catalog with yields, maturity, minimum investment
- `get_product_details(product_name)` - Detailed product specifications
- `search_market_data(product_type)` - Market trends and comparable products

**Email Marketing:**
- `send_email(customer_email, subject, body)` - Send personalized emails (stored in S3 `sent-emails/YYYY-MM-DD/`)
- `get_recent_emails(limit)` - View email history with metadata

**Data Storage:**
- **S3 Bucket:** `mcp-bank-x-data-{account}-{region}`
- **Customer Data:** `customer-data/bank-x-customers.json`
- **Product Data:** `product-data/*.json` (government, corporate, green, municipal bonds)
- **Email Archive:** `sent-emails/YYYY-MM-DD/{timestamp}_{email}_{subject}.txt`

**Multi-Step Workflow Example:**
1. User: "Email customers about Government Bond Y"
2. Agent researches product: `get_product_details('government-bond-y')`
3. Agent searches market: `search_market_data('government_bond')`
4. Agent filters customers: `list_customers()` → checks `interestedInBonds` and `portfolioValue`
5. Agent gets profiles: `get_customer_profile()` for each qualified customer
6. Agent generates personalized email drafts
7. **Agent requests approval:** Shows all drafts and waits for "yes" confirmation
8. Agent sends emails: `send_email()` for each approved recipient
9. Agent reports results: Successes/failures with error details

### 8. Built-in Observability
- **CloudWatch Logs:** `/aws/bedrock-agentcore/runtimes/strands_agent-*`
- **Lambda Logs:** `/aws/lambda/AgentCoreMcp-*` (9 MCP functions: 7 active + 2 legacy)
- **X-Ray Tracing:** Distributed tracing enabled
- **CloudWatch Metrics:** Custom metrics in `bedrock-agentcore` namespace
- **CodeBuild Logs:** `/aws/codebuild/bedrock-agentcore-strands-agent-builder`

## Manual Deployment

If you prefer to deploy stacks individually:

### 1. Bootstrap CDK (one-time setup)
```bash
cd cdk
npx cdk bootstrap --no-cli-pager
```

### 2. Deploy Infrastructure
```bash
cd cdk
npx cdk deploy AgentCoreInfra --no-cli-pager
```

### 3. Deploy Authentication
```bash
cd cdk
npx cdk deploy AgentCoreAuth --no-cli-pager
```

### 4. Deploy MCP Tools
```bash
cd cdk
npx cdk deploy AgentCoreMcp --no-cli-pager
```

### 5. Deploy Runtime (triggers build automatically)
```bash
cd cdk
npx cdk deploy AgentCoreRuntime --no-cli-pager
```
*Note: This will pause for 5-10 minutes while CodeBuild runs*

### 6. Deploy Frontend

**Windows (PowerShell):**
```powershell
$agentRuntimeArn = aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" --output text --no-cli-pager
$region = aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].Outputs[?OutputKey=='Region'].OutputValue" --output text --no-cli-pager
$userPoolId = aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text --no-cli-pager
$userPoolClientId = aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text --no-cli-pager
.\scripts\build-frontend.ps1 -UserPoolId $userPoolId -UserPoolClientId $userPoolClientId -AgentRuntimeArn $agentRuntimeArn -Region $region
cd cdk
npx cdk deploy AgentCoreFrontend --no-cli-pager
```

**macOS/Linux (Bash):**
```bash
AGENT_RUNTIME_ARN=$(aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" --output text --no-cli-pager)
REGION=$(aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].Outputs[?OutputKey=='Region'].OutputValue" --output text --no-cli-pager)
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text --no-cli-pager)
USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text --no-cli-pager)
./scripts/build-frontend.sh "$USER_POOL_ID" "$USER_POOL_CLIENT_ID" "$AGENT_RUNTIME_ARN" "$REGION"
cd cdk
npx cdk deploy AgentCoreFrontend --no-cli-pager
```

## Updating the Agent

To modify the agent code:

1. Edit `agent/strands_agent.py` or `agent/requirements.txt`
2. Redeploy runtime stack:
   ```bash
   cd cdk
   npx cdk deploy AgentCoreRuntime --no-cli-pager
   ```

The deployment will:
- Upload new agent code to S3
- Trigger CodeBuild to rebuild container
- Wait for build completion
- Update AgentCore runtime with new image

## Cleanup

```bash
cd cdk
npx cdk destroy AgentCoreFrontend --no-cli-pager
npx cdk destroy AgentCoreRuntime --no-cli-pager
npx cdk destroy AgentCoreMcp --no-cli-pager
npx cdk destroy AgentCoreAuth --no-cli-pager
npx cdk destroy AgentCoreInfra --no-cli-pager
```

**Note:** Deleting AgentCoreMcp will remove the S3 bucket containing customer data, product data, and sent email history. Cognito User Pool will be deleted along with all user accounts.

## Troubleshooting

### ❌ "Template format error: Unrecognized resource types: [AWS::BedrockAgentCore::Runtime]"

**This is the most common deployment error.** It means you're trying to deploy to a region where AgentCore is not available.

**Solution:**

1. **Check current regional availability** - Visit [AWS AgentCore Regions Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html)
2. **Set the region environment variables** to a supported region before deploying:

**Windows (PowerShell):**
```powershell
$env:AWS_DEFAULT_REGION = "your-supported-region"
$env:AWS_REGION = "your-supported-region"
.\deploy-all.ps1
```

**macOS/Linux (Bash):**
```bash
export AWS_DEFAULT_REGION="your-supported-region"
export AWS_REGION="your-supported-region"
./deploy-all.sh
```

### "CDK Bootstrap Required" or "SSM parameter not found"
If you see errors like "Has the environment been bootstrapped? Please run 'cdk bootstrap'":

This means CDK hasn't been set up in your AWS account/region yet. The deployment script now handles this automatically, but if you're doing manual deployment:

```bash
cd cdk
npx cdk bootstrap --no-cli-pager
```

**Region-specific bootstrap**: CDK bootstrap is required once per AWS account/region combination.

### "Access Denied" or "Unauthorized"
If AWS credentials are not configured or have expired:

**Option 1: Configure with access keys**
```bash
aws configure
```

**Option 2: Use AWS SSO**
```bash
aws sso login --profile <profile-name>
export AWS_PROFILE=<profile-name>
```

**Option 3: Set environment variables**
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=your-region
```

**Verify credentials are working:**
```bash
aws sts get-caller-identity
```

If API returns 401 Unauthorized:
- Make sure you're signed in (check header shows your email)
- Try signing out and back in
- Check browser console for JWT token errors

### "Container failed to start"
Check CloudWatch logs:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/strands_agent-* --follow --no-cli-pager
```

### "Image not found in ECR"
Redeploy runtime stack - it will trigger a new build:
```bash
cd cdk
npx cdk deploy AgentCoreRuntime --no-cli-pager
```

### "Build timeout after 15 minutes"
Check CodeBuild console for build status. If build is still running, wait for completion and redeploy runtime stack.

### CodeBuild fails
Check build logs:
```bash
aws logs tail /aws/codebuild/bedrock-agentcore-strands-agent-builder --follow --no-cli-pager
```

### Frontend shows errors
Verify AgentCore Runtime ARN and Cognito config are correct:
```bash
aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" --output text --no-cli-pager
aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].Outputs[?OutputKey=='Region'].OutputValue" --output text --no-cli-pager
aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text --no-cli-pager
aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text --no-cli-pager
```

### Email verification not received
- Check spam/junk folder
- Verify email address is correct
- Wait a few minutes (can take up to 5 minutes)
- Try signing up with a different email

### Verify deployment status
Check all stack statuses:
```bash
aws cloudformation describe-stacks --stack-name AgentCoreInfra --query "Stacks[0].StackStatus" --no-cli-pager
aws cloudformation describe-stacks --stack-name AgentCoreAuth --query "Stacks[0].StackStatus" --no-cli-pager
aws cloudformation describe-stacks --stack-name AgentCoreRuntime --query "Stacks[0].StackStatus" --no-cli-pager
aws cloudformation describe-stacks --stack-name AgentCoreFrontend --query "Stacks[0].StackStatus" --no-cli-pager
```

## Architecture Details

### CDK vs AgentCore CLI

This project uses AWS CDK to replicate the functionality of the AgentCore CLI's `agentcore launch` command. Here's how they compare:

**AgentCore CLI Approach:**
```bash
# Simple CLI commands handle everything
agentcore configure -e agent.py
agentcore launch
```

**Our CDK Approach:**
```bash
# Infrastructure as Code with same end result
./deploy-all.ps1  # or ./deploy-all.sh
```

**Why CDK Instead of CLI?**
- **Full-stack deployment**: Includes authentication, frontend, and infrastructure
- **Reproducible infrastructure**: Version-controlled, declarative infrastructure
- **Team collaboration**: Shared infrastructure definitions
- **Integration flexibility**: Easy to extend with additional AWS services
- **Production readiness**: Proper IAM roles, security groups, and resource tagging

Both approaches create the same AgentCore runtime, but CDK provides more control over the complete application stack.

### Why Lambda Waiter?
The AgentCore CLI's `agentcore launch` command waits for container builds to complete before creating the runtime. Our CDK implementation replicates this synchronous behavior using a Lambda Custom Resource:

- **Replicates CLI synchronization**: Simulates how `agentcore launch` waits for build completion
- **CloudFormation limitation**: Custom Resources have a 4KB response limit, but CodeBuild's `batchGetBuilds` response exceeds this
- **Internal polling**: Lambda waiter polls CodeBuild internally and returns only success/failure to CloudFormation
- **Ensures proper sequencing**: Prevents AgentCore runtime creation before container image exists (same as CLI)

### Why CodeBuild?
AgentCore CLI's `agentcore launch` command automatically handles container building and ECR pushing. Our CDK implementation replicates this functionality using CodeBuild to provide the same automated container build process:

- **Replicates CLI behavior**: Simulates `agentcore launch` container build process
- **Native ARM64 build environment** (no emulation, matches AgentCore CLI)
- **Consistent builds across team members** (no local Docker Desktop required)
- **Build history and logs in AWS Console** (same as CLI provides)
- **Automatic image push to ECR** (matches CLI workflow)
- **Infrastructure as Code**: Declarative alternative to CLI commands

### Why Five Stacks?
- **AgentCoreInfra**: Rarely changes, contains build pipeline (ECR, CodeBuild)
- **AgentCoreAuth**: Authentication resources, rarely changes (Cognito)
- **AgentCoreMcp**: Business logic layer (9 Lambda functions + S3 data), changes when tools/data update
- **AgentCoreRuntime**: Changes when agent code updates, includes built-in Cognito authentication
- **AgentCoreFrontend**: Changes when UI updates (React app, CloudFront)

This separation allows independent updates without rebuilding everything. For example, adding a new bond product only requires updating AgentCoreMcp, not rebuilding the entire agent container.

### Why ARM64?
AgentCore natively supports ARM64 architecture, providing better performance and cost efficiency compared to x86_64.

## Bank X Use Case: Financial Product Marketing

This implementation demonstrates a real-world enterprise use case: **personalized bond marketing with AI-powered customer intelligence**.

### Business Scenario
**Challenge:** Bank X needs to market new bond products to qualified customers without sending generic mass emails.

**Solution:** AI agent that:
1. Researches product specifications and market conditions
2. Analyzes customer profiles (portfolio value, investment preferences, bond interest)
3. Identifies qualified prospects based on minimum investment thresholds
4. Generates personalized emails referencing customer-specific factors
5. Presents drafts for human approval before sending
6. Tracks email history for compliance and follow-up

### Key Features
- **Customer Intelligence**: Agent reads customer profiles with `interestedInBonds` flag and `portfolioValue` to identify qualified leads
- **Product Research**: Agent analyzes bond specifications (yield, maturity, minimum investment) to match with customer needs
- **Market Context**: Agent searches comparable products and market trends to provide informed recommendations
- **Approval Workflow**: Multi-step process with human-in-the-loop approval gate before sending emails
- **Audit Trail**: All sent emails stored with timestamps for compliance and historical analysis
- **Error Resilience**: Individual email failures don't halt the campaign; agent reports successes and failures

### Sample Customer Data
The demo includes realistic customer profiles:
- **CUST-001**: High net worth customer ($2.5M portfolio), interested in bonds
- **CUST-002**: Mid-tier customer ($750K portfolio), interested in bonds
- **CUST-003**: Small investor ($150K portfolio), not interested in bonds
- Each customer has email, portfolio value, risk tolerance, and investment preferences

### Sample Bond Products
- **Government Bond Y**: Low-risk sovereign debt (2.8% yield, 10-year maturity, $1K minimum)
- **Corporate Bond A**: Investment-grade corporate debt (4.2% yield, 5-year maturity, $5K minimum)
- **Green Bond G**: ESG-focused municipal bond (3.5% yield, 7-year maturity, $2.5K minimum)
- **Municipal Bond M**: Tax-advantaged local government bond (2.9% yield, 15-year maturity, $1K minimum)

### Demo Workflow
**User prompt:** "Email customers about Government Bond Y"

**Agent execution:**
1. **Research**: Retrieves product details → "2.8% yield, 10-year maturity, $1,000 minimum investment"
2. **Market analysis**: Searches comparable bonds → "Competitive yield in current 2.5-3.0% market"
3. **Customer filtering**: Lists customers → Filters for `interestedInBonds: true` AND `portfolioValue >= $1,000`
4. **Profile enrichment**: Gets full profiles → Identifies CUST-001 ($2.5M) and CUST-002 ($750K) as qualified
5. **Personalization**: Generates unique emails → References portfolio size, investment goals, market context
6. **Approval gate**: Presents drafts → **Waits indefinitely** for user to type "yes" (no timeout, uses AgentCore memory)
7. **Execution**: Sends emails → Stores to S3 `sent-emails/2025-12-11/{timestamp}_jane@example.com_government-bond-y-offer.txt`
8. **Reporting**: Summarizes results → "Successfully sent 2 emails, 0 failures"

### Security

- **Authentication required** - API protected by Cognito JWT tokens
- **Email verification** - Users must verify email before access
- **Password policy** - Enforced minimum complexity requirements
- Frontend served via HTTPS (CloudFront)
- AWS credentials never exposed to browser
- CORS configured for API Gateway
- Lambda has minimal IAM permissions
- AgentCore Runtime runs in isolated microVMs
- Container images scanned by ECR
- Origin Access Control (OAC) for S3/CloudFront
- JWT tokens stored in browser session (not localStorage)

## Cost Estimate

Approximate monthly costs for US East (N. Virginia) region:

**Authentication & User Management:**
- **Cognito**: Free for first 10,000 MAUs (Monthly Active Users), then $0.015 per MAU. This demo uses email/password authentication (no SAML/OIDC federation)

**Agent Runtime & Compute:**
- **AgentCore Runtime**: Consumption-based pricing - $0.0895 per vCPU-hour + $0.00945 per GB-hour (only charged for active processing time, I/O wait is free)
- **Bedrock Model (Claude Haiku 4.5)**: $0.0008 per 1K input tokens + $0.0016 per 1K output tokens (on-demand pricing)
- **Lambda (7 MCP Functions)**: Free tier covers 1M requests/month + 400,000 GB-seconds/month. After free tier: $0.20 per 1M requests + $0.0000166667 per GB-second
- **Lambda (Waiter Function)**: Free tier covers deployment waiter operations. After free tier: $0.20 per 1M requests + $0.0000166667 per GB-second

**Frontend & Content Delivery:**
- **CloudFront**: Always free tier includes 1 TB data transfer out/month + 10M HTTP/HTTPS requests/month. After free tier: $0.085 per GB (next 9 TB) + $0.01 per 10,000 HTTPS requests
- **S3 (Static Hosting)**: $0.023 per GB-month storage + $0.0004 per 1,000 GET requests (negligible for static sites)

**Container Build & Storage:**
- **ECR**: Free tier: 500 MB/month for 12 months (new customers). After free tier: $0.10 per GB-month for private repository storage
- **CodeBuild (ARM64)**: Free tier: 100 build minutes/month. After free tier: $0.005 per build minute (only charged during deployments, ~5-10 minutes per deployment)

**Monitoring & Logs:**
- **CloudWatch Logs**: $0.50 per GB ingested + $0.03 per GB stored (first 5 GB ingestion free)

**Infrastructure (No Cost):**
- **CloudFormation**: Free for stack operations
- **IAM**: Free

**Typical demo cost**: $3-10/month with light usage (100-500 requests/month)
- AgentCore Runtime: ~$0.50-2/month (assuming 30-60 seconds per request, 1 vCPU, 2 GB memory)
- Bedrock Model: ~$0.50-3/month (depends on prompt/response length)
- Lambda (MCP Functions): Covered by free tier for light usage (~10-50 invocations per agent request)
- CloudFront, S3: Covered by free tiers for light usage
- ECR: ~$0.10/month (container image ~1 GB)
- CloudWatch Logs: ~$0.50-1/month
- Other services: Free or negligible

**Note**: Costs scale with usage. High-volume production workloads will incur higher costs, especially for AgentCore Runtime and Bedrock model invocations.

## Customizing the UI

The frontend is built with [AWS Cloudscape Design System](https://cloudscape.design/), AWS's open-source design system for building intuitive web applications. While AgentCore is the focus of this demo, the UI is designed to be easily customizable.

### Why Cloudscape?

- **AWS Native**: Built by AWS for AWS applications
- **Accessibility**: WCAG 2.1 AA compliant out of the box
- **Responsive**: Works seamlessly across devices
- **Rich Components**: 50+ pre-built components for common patterns
- **GenAI Patterns**: Specialized components for AI chat interfaces

### Quick Customization Examples

**1. Change Support Prompts** (`frontend/src/App.tsx`):
```typescript
// Modify the getSupportPrompts() function
const getSupportPrompts = () => {
  if (messages.length === 0) {
    return [
      { id: 'custom1', text: 'Your custom prompt here' },
      { id: 'custom2', text: 'Another custom prompt' },
      // Add more prompts...
    ];
  }
  // Add contextual prompts based on conversation...
};
```

**2. Change Prompt Alignment** (horizontal/vertical):
```typescript
<SupportPromptGroup
  alignment="horizontal"  // or "vertical"
  items={getSupportPrompts()}
  // ...
/>
```

**3. Customize Markdown Styling** (`frontend/src/markdown.css`):
```css
/* Change code block background */
.markdown-content pre {
  background-color: #f0f0f0;
}

/* Customize table styling */
.markdown-content table th {
  background-color: #e0e0e0;
}
```

**4. Add More Feedback Options**:
```typescript
// In the ButtonGroup items array, add:
{
  type: 'icon-button',
  id: 'share',
  iconName: 'share',
  text: 'Share',
}
```

**5. Change App Theme Colors**:
Cloudscape uses design tokens. Create `frontend/src/theme.css`:
```css
:root {
  --awsui-color-text-heading-default: #your-color;
  --awsui-color-background-container-content: #your-bg;
}
```

### Cloudscape Resources

- [Component Library](https://cloudscape.design/components/)
- [GenAI Chat Patterns](https://cloudscape.design/patterns/genai/generative-AI-chat/)
- [Design Tokens](https://cloudscape.design/foundation/visual-foundation/design-tokens/)
- [GitHub Repository](https://github.com/cloudscape-design/components)

### Key UI Features in This Demo

- **Chat Components**: `ChatBubble`, `Avatar`, `SupportPromptGroup`
- **Markdown Rendering**: Full markdown support with `react-markdown`
- **Feedback Buttons**: Thumbs up/down and copy functionality
- **Authentication UI**: Sign in/sign up modal with Cognito
- **Responsive Layout**: 3-column grid that adapts to screen size
- **Design Tokens**: Consistent styling using Cloudscape tokens

## Next Steps

**Bank X Enhancements:**
- **Add Products**: Create new bond JSON files in `cdk/assets/product-data/` and redeploy
- **Import Customers**: Update `bank-x-customers.json` with real customer data
- **Email Templates**: Add template support to `send_email` tool
- **Customer Segmentation**: Implement advanced filtering logic (risk tolerance, investment horizon)
- **Real Market Data**: Integrate with financial APIs for live market data
- **Email Analytics**: Track open rates, click-through rates
- **CRM Integration**: Connect to Salesforce or HubSpot

**Infrastructure Enhancements:**
- **Change Model**: Edit `model_id` in `agent/strands_agent.py` (try Amazon Nova or Claude Opus)
- **Add Memory**: Integrate AgentCore Memory for persistent customer conversation history
- **Custom Domain**: Add Route53 and ACM certificate to frontend stack
- **Monitoring**: Set up CloudWatch alarms for Lambda errors, AgentCore latency
- **Streaming**: Implement streaming responses for better UX
- **MFA**: Enable multi-factor authentication in Cognito
- **API Gateway**: Add API Gateway for external MCP tool access
- **User Management**: Build admin panel for managing customers and products

## Resources

**AWS Documentation:**
- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-agentcore.html)
- [JWT Bearer Token Authentication Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-oauth.html#invoke-agent) - AgentCore's built-in JWT authentication
- [AgentCore Regions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html) - Regional availability
- [CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/)
- [Bedrock Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)

**Frameworks & Tools:**
- [Strands Agents Documentation](https://github.com/awslabs/strands) - Multi-agent framework used in this demo
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Protocol for tool integration
- [AWS Cloudscape Design System](https://cloudscape.design/) - UI component library

**Project Documentation:**
- [MCP-IMPLEMENTATION.md](./MCP-IMPLEMENTATION.md) - Detailed MCP architecture and Lambda integration
- [LOCAL-VS-PRODUCTION.md](./LOCAL-VS-PRODUCTION.md) - Dual-mode development guide
- [BANK-X-IMPLEMENTATION-PLAN.md](./BANK-X-IMPLEMENTATION-PLAN.md) - Original implementation plan

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review AWS Bedrock documentation
- Open an issue in the repository
## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.