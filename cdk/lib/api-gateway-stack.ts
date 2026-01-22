import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigatewayv2';
import * as integrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';

export interface ApiGatewayStackProps extends cdk.StackProps {
  userPool: cognito.UserPool;
  userPoolClient: cognito.UserPoolClient;
  agentRuntimeArn: string;
  region: string;
}

export class ApiGatewayStack extends cdk.Stack {
  public readonly apiUrl: string;

  constructor(scope: Construct, id: string, props: ApiGatewayStackProps) {
    super(scope, id, props);

    // Lambda function to proxy requests to AgentCore Runtime
    const proxyFunction = new lambda.Function(this, 'AgentCoreProxyFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json
import os
import boto3
from botocore.exceptions import ClientError

runtime_arn = os.environ['AGENT_RUNTIME_ARN']
region = os.environ['AGENT_RUNTIME_REGION']

# Extract runtime ID for logging only
runtime_id = runtime_arn.split('/')[-1] if '/' in runtime_arn else runtime_arn

# Create client once per container
agentcore_client = boto3.client('bedrock-agentcore', region_name=region)

def handler(event, context):
    print(f"Event: {json.dumps(event)}")
    print(f"Runtime ARN: {runtime_arn}")
    print(f"Runtime ID: {runtime_id}")
    
    # Extract request body
    try:
        body = json.loads(event.get('body', '{}'))
        prompt = body.get('input', {}).get('prompt', '')
        conversation_history = body.get('input', {}).get('conversationHistory', [])
        
        if not prompt:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
                'body': json.dumps({'error': 'prompt is required'})
            }
        
        # Build the payload expected by AgentCore
        payload = {
          'input': {
            'prompt': prompt,
            'conversationHistory': conversation_history
          }
        }

        print(f"Payload: {json.dumps(payload)}")

        try:
          # Invoke AgentCore Runtime using official API
          response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            contentType='application/json',
            accept='application/json',
            payload=json.dumps(payload).encode('utf-8')
          )

          # Response from invoke_agent_runtime
          # The 'response' key contains a StreamingBody object
          stream_data = response.get('response')
          
          full_response = ''
          if stream_data:
            # StreamingBody has a read() method
            if hasattr(stream_data, 'read'):
              content = stream_data.read()
              full_response = content.decode('utf-8') if isinstance(content, bytes) else str(content)
          
          print(f"AgentCore response length: {len(full_response)}")
          print(f"AgentCore response (first 500 chars): {full_response[:500]}")

          # Normalize Bedrock event-stream into plain text
          texts = []
          for line in full_response.splitlines():
            if line.startswith('data: '):
              raw = line[6:]
              try:
                texts.append(json.loads(raw))  # lines may already be JSON strings
              except Exception:
                texts.append(raw)

          plain_text = ''.join(texts)

          # Return as text/event-stream for frontend streaming
          # Split plain text into modest chunks and format as SSE (double-newline between events)
          chunks = [plain_text[i:i+200] for i in range(0, len(plain_text), 200)] or ['']
          events = [f"data: {json.dumps(chunk)}" for chunk in chunks]
          sse_data = "\\n\\n".join(events) + "\\n\\n"
          
          return {
            'statusCode': 200,
            'headers': {
              'Content-Type': 'text/event-stream',
              'Access-Control-Allow-Origin': '*',
              'Access-Control-Allow-Methods': 'POST, OPTIONS',
              'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            },
            'body': sse_data
          }
        except ClientError as e:
          print(f"AgentCore client error: {e}")
          return {
            'statusCode': 500,
            'headers': {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*',
              'Access-Control-Allow-Methods': 'POST, OPTIONS',
              'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            },
            'body': json.dumps({'error': str(e)})
          }
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            },
            'body': json.dumps({'error': str(e)})
        }
`),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        AGENT_RUNTIME_ARN: props.agentRuntimeArn,
        AGENT_RUNTIME_REGION: this.region,
      },
    });

    // Grant permissions to invoke AgentCore Runtime
    proxyFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock-agentcore:InvokeAgentRuntime',
        'bedrock-agentcore:InvokeAgent',
      ],
      resources: [
        props.agentRuntimeArn,
        `${props.agentRuntimeArn}/runtime-endpoint/*`,
      ],
    }));

    // Create HTTP API
    const httpApi = new apigateway.HttpApi(this, 'AgentCoreApi', {
      apiName: 'agentcore-api',
      description: 'API Gateway proxy for AgentCore Runtime',
      corsPreflight: {
        allowOrigins: ['*'],
        allowMethods: [apigateway.CorsHttpMethod.POST, apigateway.CorsHttpMethod.OPTIONS],
        allowHeaders: ['Content-Type', 'Authorization'],
        maxAge: cdk.Duration.days(1),
      },
    });

    // Add Lambda integration
    const lambdaIntegration = new integrations.HttpLambdaIntegration(
      'ProxyIntegration',
      proxyFunction
    );

    httpApi.addRoutes({
      path: '/invoke',
      methods: [apigateway.HttpMethod.POST],
      integration: lambdaIntegration,
    });

    this.apiUrl = httpApi.apiEndpoint!;

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.apiUrl,
      description: 'API Gateway URL for AgentCore invocations',
      exportName: 'AgentCoreApiUrl',
    });
  }
}
