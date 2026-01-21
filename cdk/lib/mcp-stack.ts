#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export interface McpStackProps extends cdk.StackProps {}

export class McpStack extends cdk.Stack {
  public readonly listFilesFunction: lambda.Function;
  public readonly readFileFunction: lambda.Function;
  public readonly listBondsFunction: lambda.Function;
  public readonly listCustomersFunction: lambda.Function;
  public readonly getCustomerFunction: lambda.Function;
  public readonly getProductFunction: lambda.Function;
  public readonly searchMarketFunction: lambda.Function;
  public readonly sendEmailFunction: lambda.Function;
  public readonly getRecentEmailsFunction: lambda.Function;
  public readonly clientDetailsBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: McpStackProps) {
    super(scope, id, props);

    // Create S3 bucket for client details JSON files
    this.clientDetailsBucket = new s3.Bucket(this, 'ClientDetailsBucket', {
      bucketName: `agentcore-data-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [{
        noncurrentVersionExpiration: cdk.Duration.days(30),
        id: 'DeleteOldVersions',
      }],
    });

    // Deploy example JSON files to S3
    new s3deploy.BucketDeployment(this, 'DeployClientDetails', {
      sources: [s3deploy.Source.asset('./assets')],
      destinationBucket: this.clientDetailsBucket,
      destinationKeyPrefix: 'client-details/',
      prune: false,
    });

    // Lambda function to list files
    this.listFilesFunction = new lambda.Function(this, 'ListFilesFunction', {
      runtime: lambda.Runtime.NODEJS_22_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('../lambda/list-files'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'ListFilesLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        BUCKET_NAME: this.clientDetailsBucket.bucketName,
      },
    });

    // Lambda function to read file
    this.readFileFunction = new lambda.Function(this, 'ReadFileFunction', {
      runtime: lambda.Runtime.NODEJS_22_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('../lambda/read-file'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'ReadFileLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        BUCKET_NAME: this.clientDetailsBucket.bucketName,
      },
    });

    // Grant S3 read permissions to Lambda functions (scoped to client-details prefix)
    this.clientDetailsBucket.grantRead(this.listFilesFunction, 'client-details/*');
    this.clientDetailsBucket.grantRead(this.readFileFunction, 'client-details/*');

    // Create Lambda functions for all tools
    // List Bonds
    this.listBondsFunction = new lambda.Function(this, 'ListBondsFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/list-bonds'),
      timeout: cdk.Duration.seconds(15),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'ListBondsLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        S3_DATA_BUCKET: this.clientDetailsBucket.bucketName,
        READ_FILE_FUNCTION_ARN: this.readFileFunction.functionArn,
        LIST_FILES_FUNCTION_ARN: this.listFilesFunction.functionArn,
        LOG_LEVEL: 'INFO',
      },
    });

    // List Customers
    this.listCustomersFunction = new lambda.Function(this, 'ListCustomersFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/list-customers'),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'ListCustomersLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        READ_FILE_FUNCTION_ARN: this.readFileFunction.functionArn,
        LOG_LEVEL: 'INFO',
      },
    });

    // Get Customer Profile
    this.getCustomerFunction = new lambda.Function(this, 'GetCustomerFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/get-customer'),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'GetCustomerLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        READ_FILE_FUNCTION_ARN: this.readFileFunction.functionArn,
        LOG_LEVEL: 'INFO',
      },
    });

    // Get Product Details
    this.getProductFunction = new lambda.Function(this, 'GetProductFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/get-product'),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'GetProductLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        READ_FILE_FUNCTION_ARN: this.readFileFunction.functionArn,
        LOG_LEVEL: 'INFO',
      },
    });

    // Search Market Data
    this.searchMarketFunction = new lambda.Function(this, 'SearchMarketFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/search-market'),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'SearchMarketLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        S3_DATA_BUCKET: this.clientDetailsBucket.bucketName,
        LOG_LEVEL: 'INFO',
      },
    });

    // Send Email
    this.sendEmailFunction = new lambda.Function(this, 'SendEmailFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/send-email'),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'SendEmailLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        S3_DATA_BUCKET: this.clientDetailsBucket.bucketName,
        LOG_LEVEL: 'INFO',
      },
    });

    // Get Recent Emails
    this.getRecentEmailsFunction = new lambda.Function(this, 'GetRecentEmailsFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/get-recent-emails'),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      tracing: lambda.Tracing.ACTIVE,
      logGroup: new logs.LogGroup(this, 'GetRecentEmailsLogGroup', {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }),
      environment: {
        S3_DATA_BUCKET: this.clientDetailsBucket.bucketName,
        LOG_LEVEL: 'INFO',
      },
    });

    // Grant permissions
    this.readFileFunction.grantInvoke(this.listBondsFunction);
    this.readFileFunction.grantInvoke(this.listCustomersFunction);
    this.readFileFunction.grantInvoke(this.getCustomerFunction);
    this.readFileFunction.grantInvoke(this.getProductFunction);
    
    // Grant list-bonds permission to invoke list-files and read-file
    this.listFilesFunction.grantInvoke(this.listBondsFunction);
    this.readFileFunction.grantInvoke(this.listBondsFunction);
    
    this.clientDetailsBucket.grantRead(this.searchMarketFunction, 'client-details/market-data/*');
    this.clientDetailsBucket.grantWrite(this.sendEmailFunction, 'sent-emails/*');
    this.clientDetailsBucket.grantRead(this.getRecentEmailsFunction, 'sent-emails/*');

    // Note: Lambda functions are now invoked by Bedrock Agent action groups
    // Permissions are granted in BedrockAgentStack

    // Outputs
    new cdk.CfnOutput(this, 'ClientDetailsBucketName', {
      value: this.clientDetailsBucket.bucketName,
      exportName: 'McpClientDetailsBucketName',
    });

    new cdk.CfnOutput(this, 'ListFilesFunctionArn', {
      value: this.listFilesFunction.functionArn,
      exportName: 'McpListFilesFunctionArn',
    });

    new cdk.CfnOutput(this, 'ReadFileFunctionArn', {
      value: this.readFileFunction.functionArn,
      exportName: 'McpReadFileFunctionArn',
    });
  }
}
