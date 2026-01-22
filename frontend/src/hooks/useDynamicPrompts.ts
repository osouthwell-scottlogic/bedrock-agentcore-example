import { useState } from 'react';
import { invokeAgent } from '../agentcore';
import { parseAgentResponse, extractJsonArray, sanitizeIds } from '../lib/responseParser';

export interface Message {
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

export interface PromptSuggestion {
  id: string;
  text: string;
}

export interface UseDynamicPromptsReturn {
  dynamicPrompts: PromptSuggestion[];
  loadingPrompts: boolean;
  generateInitialPrompts: () => Promise<void>;
  generateDynamicPrompts: (conversationHistory: Message[]) => Promise<void>;
  clearDynamicPrompts: () => void;
}

const cleanResponse = (response: string): string => {
  let cleaned = response.trim();
  if ((cleaned.startsWith('"') && cleaned.endsWith('"')) ||
    (cleaned.startsWith("'") && cleaned.endsWith("'"))) {
    cleaned = cleaned.slice(1, -1);
  }
  cleaned = cleaned.replace(/\\n/g, '\n');
  cleaned = cleaned.replace(/\\t/g, '\t');
  return cleaned;
};

export function useDynamicPrompts(isLocalDev: boolean, user: any): UseDynamicPromptsReturn {
  const [dynamicPrompts, setDynamicPrompts] = useState<PromptSuggestion[]>([]);
  const [loadingPrompts, setLoadingPrompts] = useState(false);

  const generateInitialPrompts = async () => {
    setLoadingPrompts(true);
    try {
      const suggestionPrompt = `You are helping a user get started with Bank X Financial Assistant. Suggest 4 brief, actionable prompts they might want to try first.

Available capabilities:
- list_available_bonds: Show all 4 bond products
- get_customer_profile: View customer details  
- get_product_details: Get detailed bond information
- search_market_data: Research market trends
- send_email: Email qualified customers about bonds
- get_recent_emails: View sent email history

IMPORTANT: Do NOT include customer IDs (like CUST-001) or any internal identifiers in suggestions. Use customer names or generic references only.

Respond ONLY with a JSON array of 4 short prompts (each 3-8 words), like:
["Show all available bonds", "View customer portfolios", "Email about Government Bond Y", "Check recent emails"]`;

      let suggestionResponse = '';
      
      await invokeAgent({
        prompt: suggestionPrompt,
        onChunk: (chunk: string) => {
          suggestionResponse += chunk;
        }
      });

      const cleanedResponse = parseAgentResponse(suggestionResponse);
      const suggestions = extractJsonArray<string>(cleanedResponse);
      
      if (suggestions && Array.isArray(suggestions) && suggestions.length > 0) {
        const formattedPrompts = suggestions
          .slice(0, 4)
          .map((text: string, idx: number) => ({
            id: `initial-${idx}`,
            text: sanitizeIds(text)
          }));
        setDynamicPrompts(formattedPrompts);
      }
    } catch (err) {
      console.error('Error generating initial prompts:', err);
    } finally {
      setLoadingPrompts(false);
    }
  };

  const generateDynamicPrompts = async (conversationHistory: Message[]) => {
    if (!isLocalDev && !user) return;
    
    setLoadingPrompts(true);
    
    try {
      const recentMessages = conversationHistory.slice(-6);
      
      // Convert conversation history to the format expected by the agent
      const formattedConversationHistory = recentMessages.map(m => ({
        role: m.type === 'user' ? 'user' as const : 'assistant' as const,
        content: m.content
      }));

      // Get the last assistant message to extract any entities mentioned
      const lastAssistantMessage = recentMessages.slice().reverse().find(m => m.type === 'agent');
      
      const suggestionPrompt = `You are the Bank X Suggestion Agent. Analyze the recent conversation and suggest the most natural and helpful next actions.

AVAILABLE CAPABILITIES:
- list_available_bonds: Show all bond products
- get_customer_profile(customer_id): View detailed customer profile
- get_product_details(product_name): Get bond information
- search_market_data(product_type): Research market trends
- send_email: Email customers about bonds (requires approval)
- get_recent_emails: View sent email history
- get_bond_recommendations(customer_id): Get personalized bond recommendations

INSTRUCTIONS:
1. Consider what the user just learned or accomplished
2. Suggest logical next steps that build on the conversation
3. If customers were mentioned, use their FULL NAMES (e.g., "Get recommendations for Sarah Chen") - NEVER use customer IDs
4. For generic suggestions about customers, use phrases like "Find suitable customers" or "View customer profiles" instead of referencing specific IDs
5. Mix different types of actions (view data, take action, research)
6. Keep suggestions concise (3-10 words each)

CRITICAL: NEVER include customer IDs (CUST-001, CUST-002, etc.), preview IDs, or internal identifiers. Always use customer names when referring to specific people.

Respond ONLY with a JSON array of 3-4 contextual prompts:
["Specific actionable prompt 1", "Related prompt 2", "Next logical step 3"]`;

      let suggestionResponse = '';
      
      await invokeAgent({
        prompt: suggestionPrompt,
        conversationHistory: formattedConversationHistory,
        onChunk: (chunk: string) => {
          suggestionResponse += chunk;
        }
      });

      const cleanedResponse = parseAgentResponse(suggestionResponse);
      const suggestions = extractJsonArray<string>(cleanedResponse);
      
      if (suggestions && Array.isArray(suggestions) && suggestions.length > 0) {
        const formattedPrompts = suggestions
          .slice(0, 4)
          .map((text: string, idx: number) => ({
            id: `dynamic-${idx}-${Date.now()}`,
            text: sanitizeIds(text)
          }));
        setDynamicPrompts(formattedPrompts);
      } else {
        setDynamicPrompts([]);
      }
    } catch (err) {
      console.error('Error generating dynamic prompts:', err);
      setDynamicPrompts([]);
    } finally {
      setLoadingPrompts(false);
    }
  };

  const clearDynamicPrompts = () => {
    setDynamicPrompts([]);
  };

  return {
    dynamicPrompts,
    loadingPrompts,
    generateInitialPrompts,
    generateDynamicPrompts,
    clearDynamicPrompts,
  };
}
