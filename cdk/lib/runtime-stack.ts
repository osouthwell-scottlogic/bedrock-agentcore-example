import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { Construct } from 'constructs';

export interface RuntimeStackProps extends cdk.StackProps {
  userPool: cognito.UserPool;
  userPoolClient: cognito.UserPoolClient;
  sourceBucket: s3.Bucket;
  buildProject: codebuild.Project;
  repository: ecr.Repository;
  runtimeRole: iam.Role;
  listFilesArn: string;
  readFileArn: string;
  listBondsArn: string;
  listCustomersArn: string;
  getCustomerArn: string;
  getProductArn: string;
  searchMarketArn: string;
  sendEmailArn: string;
  getRecentEmailsArn: string;
}

export class RuntimeStack extends cdk.Stack {
  public readonly agentRuntimeArn: string;

  constructor(scope: Construct, id: string, props: RuntimeStackProps) {
    super(scope, id, props);

    // Upload agent source code to S3
    const sourceUpload = new s3deploy.BucketDeployment(this, 'UploadAgentSource', {
      sources: [s3deploy.Source.asset('../agent', {
        exclude: ['__pycache__', '*.pyc', 'venv', 'local_data', 'test_*.py'],
      })],
      destinationBucket: props.sourceBucket,
      destinationKeyPrefix: 'agent/',
      prune: false,
    });

    // Note: Build trigger removed - container image should be pre-built and pushed to ECR
    // before deployment. Alternatively, implement async build via CodePipeline.

    // Grant runtime role permission to invoke Lambda tools
    const lambdaArns = [
      props.listFilesArn,
      props.readFileArn,
      props.listBondsArn,
      props.listCustomersArn,
      props.getCustomerArn,
      props.getProductArn,
      props.searchMarketArn,
      props.sendEmailArn,
      props.getRecentEmailsArn,
    ];

    props.runtimeRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['lambda:InvokeFunction'],
      resources: lambdaArns,
    }));

    // Create AgentCore Runtime using L1 construct; property names must match the CFN spec
    const agentRuntime = new cdk.CfnResource(this, 'AgentRuntime', {
      type: 'AWS::BedrockAgentCore::Runtime',
      properties: {
        AgentRuntimeName: 'AgentCoreRuntime',
        Description: 'Multi-agent financial assistant runtime',
        AgentRuntimeArtifact: {
          ContainerConfiguration: {
            ContainerUri: `${props.repository.repositoryUri}:latest`,
          },
        },
        NetworkConfiguration: {
          NetworkMode: 'PUBLIC',
        },
        ProtocolConfiguration: 'HTTP',
        RoleArn: props.runtimeRole.roleArn,
        EnvironmentVariables: {
          AWS_REGION: this.region,
          LIST_FILES_FUNCTION_ARN: props.listFilesArn,
          READ_FILE_FUNCTION_ARN: props.readFileArn,
          LIST_BONDS_FUNCTION_ARN: props.listBondsArn,
          LIST_CUSTOMERS_FUNCTION_ARN: props.listCustomersArn,
          GET_CUSTOMER_FUNCTION_ARN: props.getCustomerArn,
          GET_PRODUCT_FUNCTION_ARN: props.getProductArn,
          SEARCH_MARKET_FUNCTION_ARN: props.searchMarketArn,
          SEND_EMAIL_FUNCTION_ARN: props.sendEmailArn,
          GET_RECENT_EMAILS_FUNCTION_ARN: props.getRecentEmailsArn,
          LOG_LEVEL: 'INFO',
        },
      },
    });

    agentRuntime.node.addDependency(sourceUpload);

    // Bedrock AgentCore returns AgentRuntimeArn as the read-only identifier
    this.agentRuntimeArn = agentRuntime.getAtt('AgentRuntimeArn').toString();

    // Outputs
    new cdk.CfnOutput(this, 'AgentRuntimeArn', {
      value: this.agentRuntimeArn,
      description: 'AgentCore Runtime ARN',
      exportName: 'AgentCoreRuntimeArn',
    });

    new cdk.CfnOutput(this, 'Region', {
      value: this.region,
      description: 'Deployment region for AgentCore Runtime',
    });
  }
}
