import * as cdk from 'aws-cdk-lib';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class InfraStack extends cdk.Stack {
  public readonly repository: ecr.Repository;
  public readonly sourceBucket: s3.Bucket;
  public readonly buildProject: codebuild.Project;
  public readonly runtimeRole: iam.Role;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ECR Repository for agent container
    this.repository = new ecr.Repository(this, 'AgentRepository', {
      repositoryName: 'strands-agent-repository',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      emptyOnDelete: true,
      lifecycleRules: [{
        maxImageCount: 5,
        description: 'Keep last 5 images',
      }],
    });

    // S3 bucket for agent source code
    this.sourceBucket = new s3.Bucket(this, 'SourceBucket', {
      bucketName: `agentcore-source-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    });

    // IAM Role for AgentCore Runtime
    this.runtimeRole = new iam.Role(this, 'RuntimeRole', {
      roleName: 'AgentCoreRuntimeRole',
      // Bedrock AgentCore control plane assumes this role
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com'),
      description: 'Execution role for AgentCore Runtime',
    });

    // Grant permissions to invoke Bedrock models
    this.runtimeRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: [
        'arn:aws:bedrock:::foundation-model/*',
        `arn:aws:bedrock:${this.region}::foundation-model/*`,
        `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/*`,
      ],
    }));

    // Grant CloudWatch Logs permissions
    this.runtimeRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents',
      ],
      resources: [`arn:aws:logs:${this.region}:${this.account}:log-group:/aws/bedrock/agentcore/*`],
    }));

    // Grant ECR pull permissions
    this.repository.grantPull(this.runtimeRole);

    // CodeBuild project for building container
    this.buildProject = new codebuild.Project(this, 'BuildProject', {
      projectName: 'agentcore-container-build',
      source: codebuild.Source.s3({
        bucket: this.sourceBucket,
        path: 'agent-source.zip',
      }),
      environment: {
        buildImage: codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,
        privileged: true,
        computeType: codebuild.ComputeType.SMALL,
        environmentVariables: {
          AWS_ACCOUNT_ID: { value: this.account },
          AWS_REGION: { value: this.region },
          ECR_REPOSITORY_URI: { value: this.repository.repositoryUri },
          IMAGE_TAG: { value: 'latest' },
        },
      },
      buildSpec: codebuild.BuildSpec.fromObject({
        version: '0.2',
        phases: {
          pre_build: {
            commands: [
              'echo Logging in to Amazon ECR...',
              'aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI',
            ],
          },
          build: {
            commands: [
              'echo Building Docker image...',
              'cd agent',
              'docker build --platform linux/arm64 -t $ECR_REPOSITORY_URI:$IMAGE_TAG .',
            ],
          },
          post_build: {
            commands: [
              'echo Pushing Docker image...',
              'docker push $ECR_REPOSITORY_URI:$IMAGE_TAG',
              'echo Build completed successfully',
            ],
          },
        },
      }),
    });

    // Grant CodeBuild permissions
    this.repository.grantPullPush(this.buildProject);
    this.sourceBucket.grantRead(this.buildProject);

    // Outputs
    new cdk.CfnOutput(this, 'RepositoryUri', {
      value: this.repository.repositoryUri,
      exportName: 'AgentCoreRepositoryUri',
    });

    new cdk.CfnOutput(this, 'RepositoryArn', {
      value: this.repository.repositoryArn,
      exportName: 'AgentCoreRepositoryArn',
    });

    new cdk.CfnOutput(this, 'SourceBucketName', {
      value: this.sourceBucket.bucketName,
      exportName: 'AgentCoreSourceBucketName',
    });

    new cdk.CfnOutput(this, 'BuildProjectName', {
      value: this.buildProject.projectName,
      exportName: 'AgentCoreBuildProjectName',
    });

    new cdk.CfnOutput(this, 'RuntimeRoleArn', {
      value: this.runtimeRole.roleArn,
      exportName: 'AgentCoreRuntimeRoleArn',
    });
  }
}
