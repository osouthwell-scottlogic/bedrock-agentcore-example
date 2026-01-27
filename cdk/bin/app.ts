#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { FrontendStack } from '../lib/frontend-stack';
import { AuthStack } from '../lib/auth-stack';
import { McpStack } from '../lib/mcp-stack';
import { InfraStack } from '../lib/infra-stack';
import { RuntimeStack } from '../lib/runtime-stack';
import { ApiGatewayStack } from '../lib/api-gateway-stack';

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

// Auth stack (Cognito User Pool)
const authStack = new AuthStack(app, 'AgentCoreAuth', {
  env,
  description: 'AgentCore Authentication: Cognito User Pool for API access',
});

// MCP stack (Lambda functions and S3 bucket for client details)
const mcpStack = new McpStack(app, 'AgentCoreMcp', {
  env,
  description: 'MCP Tools: Lambda functions for file operations and S3 storage',
});

// Infrastructure stack (ECR, CodeBuild, IAM)
const infraStack = new InfraStack(app, 'AgentCoreInfra', {
  env,
  description: 'AgentCore Infrastructure: ECR repository and build project',
});

// Runtime stack (AgentCore Runtime with containerized agents)
const runtimeStack = new RuntimeStack(app, 'AgentCoreRuntime', {
  env,
  userPool: authStack.userPool,
  userPoolClient: authStack.userPoolClient,
  sourceBucket: infraStack.sourceBucket,
  buildProject: infraStack.buildProject,
  repository: infraStack.repository,
  runtimeRole: infraStack.runtimeRole,
  listFilesArn: mcpStack.listFilesFunction.functionArn,
  readFileArn: mcpStack.readFileFunction.functionArn,
  listBondsArn: mcpStack.listBondsFunction.functionArn,
  listCustomersArn: mcpStack.listCustomersFunction.functionArn,
  getCustomerArn: mcpStack.getCustomerFunction.functionArn,
  getProductArn: mcpStack.getProductFunction.functionArn,
  searchMarketArn: mcpStack.searchMarketFunction.functionArn,
  sendEmailArn: mcpStack.sendEmailFunction.functionArn,
  getRecentEmailsArn: mcpStack.getRecentEmailsFunction.functionArn,
  description: 'AgentCore Runtime: Containerized multi-agent system',
});
runtimeStack.addDependency(infraStack);
runtimeStack.addDependency(mcpStack);
runtimeStack.addDependency(authStack);

// API Gateway stack (proxy to AgentCore Runtime with CORS)
const apiGatewayStack = new ApiGatewayStack(app, 'AgentCoreApiGateway', {
  env,
  userPool: authStack.userPool,
  userPoolClient: authStack.userPoolClient,
  agentRuntimeArn: runtimeStack.agentRuntimeArn,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  description: 'AgentCore API Gateway: CORS-enabled proxy for browser access',
});
apiGatewayStack.addDependency(runtimeStack);
apiGatewayStack.addDependency(authStack);

// Frontend stack (depends on auth stack and API Gateway)
const frontendStack = new FrontendStack(app, 'AgentCoreFrontendV2', {
  env,
  userPoolId: authStack.userPool.userPoolId,
  userPoolClientId: authStack.userPoolClient.userPoolClientId,
  agentRuntimeArn: runtimeStack.agentRuntimeArn,
  apiGatewayUrl: apiGatewayStack.apiUrl,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  description: 'AgentCore Frontend: CloudFront-hosted React interface',
});
frontendStack.addDependency(apiGatewayStack);

app.synth();