#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { AgentCoreInfraStack } from '../lib/infra-stack';
import { AgentCoreStack } from '../lib/runtime-stack';
import { FrontendStack } from '../lib/frontend-stack';
import { AuthStack } from '../lib/auth-stack';
import { McpStack } from '../lib/mcp-stack';

const app = new cdk.App();

// Infrastructure stack (ECR, IAM, CodeBuild, S3)
const infraStack = new AgentCoreInfraStack(app, 'AgentCoreInfra', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'AgentCore Infrastructure: Container registry, build pipeline, and IAM roles (uksb-q3p3ydk6f3)',
});

// Auth stack (Cognito User Pool)
const authStack = new AuthStack(app, 'AgentCoreAuth', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'AgentCore Authentication: Cognito User Pool for API access',
});

// MCP stack (Lambda functions and S3 bucket for client details)
const mcpStack = new McpStack(app, 'AgentCoreMcp', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  agentRuntimeRoleArn: cdk.Fn.importValue('AgentCoreRuntimeRoleArn'),
  description: 'MCP Tools: Lambda functions for file operations and S3 storage',
});
mcpStack.addDependency(infraStack);

// Runtime stack (depends on infra, auth, and mcp stacks)
const agentStack = new AgentCoreStack(app, 'AgentCoreRuntime', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  userPool: authStack.userPool,
  userPoolClient: authStack.userPoolClient,
  listFilesFunctionArn: mcpStack.listFilesFunction.functionArn,
  readFileFunctionArn: mcpStack.readFileFunction.functionArn,
  listBondsFunctionArn: mcpStack.listBondsFunction.functionArn,
  listCustomersFunctionArn: mcpStack.listCustomersFunction.functionArn,
  getCustomerFunctionArn: mcpStack.getCustomerFunction.functionArn,
  getProductFunctionArn: mcpStack.getProductFunction.functionArn,
  searchMarketFunctionArn: mcpStack.searchMarketFunction.functionArn,
  sendEmailFunctionArn: mcpStack.sendEmailFunction.functionArn,
  getRecentEmailsFunctionArn: mcpStack.getRecentEmailsFunction.functionArn,
  dataBucketName: mcpStack.clientDetailsBucket.bucketName,
  description: 'AgentCore Runtime: Container-based agent with built-in Cognito authentication',
});
agentStack.addDependency(mcpStack);

// Frontend stack (depends on runtime and auth stacks)
new FrontendStack(app, 'AgentCoreFrontend', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  userPoolId: authStack.userPool.userPoolId,
  userPoolClientId: authStack.userPoolClient.userPoolClientId,
  agentRuntimeArn: agentStack.agentRuntimeArn,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  description: 'AgentCore Frontend: CloudFront-hosted React interface with direct AgentCore integration',
});

app.synth();
