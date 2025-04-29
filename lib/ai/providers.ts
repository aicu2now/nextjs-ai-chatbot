import {
  customProvider,
  extractReasoningMiddleware,
  wrapLanguageModel,
} from 'ai';
import { xai } from '@ai-sdk/xai';
import { isTestEnvironment } from '../constants';
import {
  artifactModel,
  chatModel,
  reasoningModel,
  titleModel,
} from './models.test';
import { createMOEProvider } from './providers/moe';

// Create base providers to use as fallbacks
const baseProviders = isTestEnvironment
  ? {
      'chat-model': chatModel,
      'chat-model-reasoning': reasoningModel,
      'title-model': titleModel,
      'artifact-model': artifactModel,
    }
  : {
      'chat-model': xai('grok-2-vision-1212'),
      'chat-model-reasoning': wrapLanguageModel({
        model: xai('grok-3-mini-beta'),
        middleware: extractReasoningMiddleware({ tagName: 'think' }),
      }),
      'title-model': xai('grok-2-1212'),
      'artifact-model': xai('grok-2-1212'),
    };

// Create the MOE provider with fallback to chat-model
const moeProvider = createMOEProvider(baseProviders['chat-model']);

// Combine all providers
export const myProvider = isTestEnvironment
  ? customProvider({
      languageModels: {
        ...baseProviders,
        // Add MOE models
        'moe-expert-byt5': baseProviders['chat-model'], // Fallback in test environment
        'moe-expert-longformer': baseProviders['chat-model'], // Fallback in test environment
        'moe-auto': baseProviders['chat-model'], // Fallback in test environment
      },
    })
  : customProvider({
      languageModels: {
        ...baseProviders,
        // Add MOE models with custom processing
        'moe-expert-byt5': wrapLanguageModel({
          model: baseProviders['chat-model'],
          middleware: async ({ messages, generate }: { messages: any; generate: () => Promise<any> }) => {
            // Process with MOE if available
            const moeResult = await moeProvider.processMOERequest(messages, {
              expertModel: 'byt5'
            });
            
            if (!moeResult.usedFallback) {
              return { text: moeResult.result };
            }
            
            // Fall back to default model
            return generate();
          }
        }),
        'moe-expert-longformer': wrapLanguageModel({
          model: baseProviders['chat-model'],
          middleware: async ({ messages, generate }: { messages: any; generate: () => Promise<any> }) => {
            // Process with MOE if available
            const moeResult = await moeProvider.processMOERequest(messages, {
              expertModel: 'longformer'
            });
            
            if (!moeResult.usedFallback) {
              return { text: moeResult.result };
            }
            
            // Fall back to default model
            return generate();
          }
        }),
        'moe-auto': wrapLanguageModel({
          model: baseProviders['chat-model'],
          middleware: async ({ messages, generate }: { messages: any; generate: () => Promise<any> }) => {
            // Auto-route to best expert
            const moeResult = await moeProvider.processMOERequest(messages);
            
            if (!moeResult.usedFallback) {
              return { text: moeResult.result };
            }
            
            // Fall back to default model
            return generate();
          }
        }),
      },
      imageModels: {
        'small-model': xai.image('grok-2-image'),
      },
    });
