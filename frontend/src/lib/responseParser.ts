/**
 * Utilities for parsing and processing agent responses
 */

/**
 * Clean and normalize agent response text
 * Removes surrounding quotes and unescapes special characters
 */
export const parseAgentResponse = (response: string): string => {
  let cleaned = response.trim();
  
  // Remove surrounding quotes if present
  if (
    (cleaned.startsWith('"') && cleaned.endsWith('"')) ||
    (cleaned.startsWith("'") && cleaned.endsWith("'"))
  ) {
    cleaned = cleaned.slice(1, -1);
  }
  
  // Unescape special characters
  cleaned = cleaned.replace(/\\n/g, '\n');
  cleaned = cleaned.replace(/\\t/g, '\t');
  
  return cleaned;
};

/**
 * Extract and parse JSON array from response text
 * Searches for JSON array pattern in the response
 */
export const extractJsonArray = <T>(response: string): T[] | null => {
  try {
    const jsonMatch = response.match(/\[[\s\S]*\]/);
    if (!jsonMatch) {
      return null;
    }
    const parsed = JSON.parse(jsonMatch[0]);
    return Array.isArray(parsed) ? parsed : null;
  } catch (error) {
    console.error('Failed to parse JSON array:', error);
    return null;
  }
};

/**
 * Extract and parse JSON object from response text
 */
export const extractJsonObject = <T>(response: string): T | null => {
  try {
    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return null;
    }
    return JSON.parse(jsonMatch[0]) as T;
  } catch (error) {
    console.error('Failed to parse JSON object:', error);
    return null;
  }
};

/**
 * Extract "Next Steps" section from agent response
 * Returns array of next step suggestions or null if not found
 */
export const extractNextSteps = (response: string): string[] | null => {
  try {
    // Match "**Next Steps:**" section with bullet points
    const nextStepsMatch = response.match(/\*\*Next Steps:\*\*\s*([\s\S]*?)(?:\n\n|$)/);
    
    if (!nextStepsMatch) {
      return null;
    }
    
    const nextStepsText = nextStepsMatch[1];
    
    // Extract bullet points (lines starting with -, *, or •)
    const bulletPoints = nextStepsText
      .split('\n')
      .map(line => line.trim())
      .filter(line => /^[-*•]\s+/.test(line))
      .map(line => line.replace(/^[-*•]\s+/, '').trim())
      .filter(line => line.length > 0);
    
    return bulletPoints.length > 0 ? bulletPoints : null;
  } catch (error) {
    console.error('Failed to extract next steps:', error);
    return null;
  }
};
