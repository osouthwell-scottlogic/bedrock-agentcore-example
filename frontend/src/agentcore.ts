// AgentCore Runtime API client with JWT bearer token authentication
import { HttpError } from './lib/fetchJson';
import { invokeAgentCoreRuntime } from './lib/agentCoreClient';

const region = (import.meta as any).env.VITE_REGION || 'us-east-1';
const isLocalDev = (import.meta as any).env.VITE_LOCAL_DEV === 'true';
const localAgentUrl = (import.meta as any).env.VITE_AGENT_RUNTIME_URL || '/api';
const apiGatewayUrl = (import.meta as any).env.VITE_API_GATEWAY_URL;

const headerVariants = ['x-amzn-requestid', 'x-request-id', 'x-amzn-request-id'];

const getRequestId = (headers: Headers): string | undefined => {
  for (const key of headerVariants) {
    const value = headers.get(key);
    if (value) return value;
  }
  return undefined;
};

const throwHttpErrorFromResponse = async (response: Response): Promise<never> => {
  const headersObj = Object.fromEntries(response.headers.entries());
  const requestId = getRequestId(response.headers);
  let parsed: any | undefined;
  try {
    parsed = await response.json();
  } catch {
    parsed = undefined;
  }
  const errorCode = parsed?.errorCode || parsed?.code;
  const message = parsed?.message || parsed?.error || response.statusText || 'Request failed';
  const details = parsed?.details || parsed;
  throw new HttpError({
    message,
    status: response.status,
    errorCode,
    requestId,
    details,
    headers: headersObj,
  });
};

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface InvokeAgentRequest {
  prompt: string;
  conversationHistory?: ConversationMessage[];
  onChunk?: (chunk: string) => void;
}

export interface InvokeAgentResponse {
  response: string;
  requestId?: string;
}

export const invokeAgent = async (request: InvokeAgentRequest): Promise<InvokeAgentResponse> => {
  try {
    // Local development mode - call local Python agent
    if (isLocalDev) {
      console.log('Local dev mode - using local agent:', { url: localAgentUrl });
      
      const response = await fetch(`${localAgentUrl}/invocations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: request.prompt,
          conversationHistory: request.conversationHistory || []
        }),
      });

      const requestId = getRequestId(response.headers);
      if (!response.ok) {
        await throwHttpErrorFromResponse(response);
      }

      if (request.onChunk && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';
        let buffer = '';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                try {
                  const parsed = JSON.parse(data);
                  fullResponse += parsed;
                  request.onChunk(parsed);
                } catch {
                  fullResponse += data;
                  request.onChunk(data);
                }
              }
            }
          }
          return { response: fullResponse, requestId };
        } finally {
          reader.releaseLock();
        }
      }

      const text = await response.text();
      return { response: text, requestId };
    }

    // Production mode - call AgentCore via API Gateway
    if (!apiGatewayUrl) {
      throw new Error('API Gateway URL must be configured. Check deployment outputs.');
    }

    const { getAccessToken } = await import('./auth');
    const jwtToken = await getAccessToken();
    if (!jwtToken) {
      throw new Error('Not authenticated - no access token available');
    }

    console.log('Invoking AgentCore via API Gateway:', { apiGatewayUrl });
    
    return await invokeAgentCoreRuntime(
      apiGatewayUrl,
      request.prompt,
      request.conversationHistory || [],
      jwtToken,
      request.onChunk
    );

  } catch (error: any) {
    console.error('Agent invocation error:', error);
    throw error instanceof HttpError ? error : new Error(`Failed to invoke agent: ${error.message}`);
  }
};