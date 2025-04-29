/**
 * MOE (Mixture of Experts) Provider Implementation
 * 
 * This module provides a TypeScript client for the Python MOE implementation.
 * It interfaces between the NextJS app and the Python MOE components.
 */

// MOE API Configuration
const MOE_API_BASE_URL = process.env.MOE_API_URL || 'http://localhost:8000';
const MOE_TIMEOUT_MS = parseInt(process.env.MOE_TIMEOUT_MS || '30000', 10); // 30 seconds timeout

interface MOERequestOptions {
  task?: string;
  options?: Record<string, any>;
}

interface MOEResponse {
  result: string;
  expert_used: string;
  confidence: number;
  processing_time: number;
  input_features?: Record<string, number>;
}

/**
 * Error class for MOE API errors
 */
export class MOEError extends Error {
  status?: number;
  
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'MOEError';
    this.status = status;
  }
}

/**
 * Checks if the MOE API is available
 * @returns Promise resolving to true if API is available, false otherwise
 */
export async function checkMOEAvailability(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${MOE_API_BASE_URL}/health`, {
      method: 'GET',
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      return false;
    }
    
    const data = await response.json();
    return data.status === 'healthy' && data.models_loaded;
  } catch (error) {
    console.error('MOE health check failed:', error);
    return false;
  }
}

/**
 * Processes text through the MOE API
 * @param text The text to process
 * @param options Additional options for processing
 * @returns Promise resolving to MOE API response
 */
export async function processMOEText(
  text: string,
  { task = 'process', options = {} }: MOERequestOptions = {}
): Promise<MOEResponse> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), MOE_TIMEOUT_MS);
    
    const response = await fetch(`${MOE_API_BASE_URL}/process/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        task,
        options,
      }),
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new MOEError(
        `MOE API returned ${response.status}: ${response.statusText}`,
        response.status
      );
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof MOEError) {
      throw error;
    }
    
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new MOEError('MOE API request timed out', 408);
    }
    
    throw new MOEError(`MOE API request failed: ${(error as Error).message}`);
  }
}

/**
 * Helper function to extract text from a message
 */
export function extractMessageText(message: any): string {
  if (!message || !message.content) {
    return '';
  }
  
  if (typeof message.content === 'string') {
    return message.content;
  }
  
  // Handle array content (multi-modal messages)
  if (Array.isArray(message.content)) {
    return message.content
      .filter((part: any) => typeof part === 'string')
      .join(' ');
  }
  
  return '';
}

/**
 * Creates a MOE provider for the project
 */
export function createMOEProvider(fallbackProvider: any) {
  return {
    processMOERequest: async (messages: any[], options = {}) => {
      try {
        // Check MOE availability
        const isMOEAvailable = await checkMOEAvailability();
        if (!isMOEAvailable) {
          console.warn('MOE API unavailable, falling back to default provider');
          return { usedFallback: true };
        }
        
        // Extract the last user message
        const lastUserMessage = messages
          .filter(m => m.role === 'user')
          .pop();
        
        if (!lastUserMessage) {
          throw new Error('No user message found');
        }
        
        const userText = extractMessageText(lastUserMessage);
        
        // Process with MOE API
        const moeResponse = await processMOEText(userText);
        
        return {
          result: moeResponse.result,
          expertUsed: moeResponse.expert_used,
          confidence: moeResponse.confidence,
          processingTime: moeResponse.processing_time,
          usedFallback: false
        };
      } catch (error) {
        console.error('MOE processing failed:', error);
        return { usedFallback: true };
      }
    }
  };
}