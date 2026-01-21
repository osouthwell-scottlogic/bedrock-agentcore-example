// AgentCore Runtime API client with JWT authentication

export interface AgentCoreStreamResponse {
  fullResponse: string;
  requestId?: string;
}

/**
 * Parse AgentCore event stream (similar to local dev format)
 */
export const parseAgentCoreStream = async (
  response: Response,
  onChunk: (text: string) => void
): Promise<AgentCoreStreamResponse> => {
  if (!response.body) {
    throw new Error('Response body is null');
  }

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
            onChunk(parsed);
          } catch {
            fullResponse += data;
            onChunk(data);
          }
        }
      }
    }

    return { fullResponse };
  } finally {
    reader.releaseLock();
  }
};

/**
 * Invoke AgentCore Runtime via API Gateway proxy
 */
export const invokeAgentCoreRuntime = async (
  apiGatewayUrl: string,
  prompt: string,
  conversationHistory: any[],
  jwtToken: string,
  onChunk?: (text: string) => void
): Promise<{ response: string; requestId?: string }> => {
  
  const url = `${apiGatewayUrl}/invoke`;

  console.log('Invoking AgentCore via API Gateway:', { url });

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${jwtToken}`,
    },
    body: JSON.stringify({
      input: {
        prompt,
        conversationHistory,
      },
    }),
  });

  const requestId = response.headers.get('x-amzn-requestid') || undefined;

  if (!response.ok) {
    const errorText = await response.text();
    console.error('AgentCore API Gateway error:', errorText);
    throw new Error(`AgentCore request failed: ${response.status} ${errorText}`);
  }

  // If onChunk callback provided, use streaming parser
  if (onChunk) {
    const { fullResponse } = await parseAgentCoreStream(response, onChunk);
    return { response: fullResponse, requestId };
  }

  // Otherwise return full response
  const data = await response.json();
  return { response: data.response || '', requestId };
};
