# MOE API Examples

This document provides example API requests and responses for interacting with the MOE (Mixture of Experts) service. These examples can be used as a reference for developers implementing or extending the MOE integration.

## Table of Contents

- [Health Check Endpoint](#health-check-endpoint)
- [Process Text (Synchronous)](#process-text-synchronous)
- [Specific Expert Selection](#specific-expert-selection)
- [Auto-Routing](#auto-routing)
- [Embedding Generation](#embedding-generation)
- [Error Handling Examples](#error-handling-examples)
- [TypeScript Client Examples](#typescript-client-examples)

## Health Check Endpoint

Used to verify if the MOE service is available and all expert models are loaded.

### Request

```bash
GET http://localhost:8000/health
```

### Response

```json
{
  "status": "healthy",
  "models_loaded": true,
  "cuda_available": true,
  "device": "cuda"
}
```

## Process Text (Synchronous)

Used to process text with the MOE service synchronously.

### Request

```bash
POST http://localhost:8000/process/sync
Content-Type: application/json

{
  "text": "This is a sample text to process with the MOE service.",
  "task": "process",
  "options": {}
}
```

### Response

```json
{
  "result": "Processed result: This is a sample text that has been analyzed by the MOE service.",
  "expert_used": "byt5",
  "confidence": 0.92,
  "processing_time": 0.856,
  "input_features": {
    "length": 52,
    "avg_word_length": 4.3,
    "special_char_ratio": 0.05,
    "uppercase_ratio": 0.02,
    "is_binary": 0.0
  }
}
```

## Specific Expert Selection

Force the use of a specific expert model by providing the `force_expert` option.

### Request

```bash
POST http://localhost:8000/process/sync
Content-Type: application/json

{
  "text": "This is a sample text that should be processed by the Longformer expert.",
  "task": "process",
  "options": {
    "force_expert": "longformer"
  }
}
```

### Response

```json
{
  "result": "Processed by Longformer: This is a sample text that has been analyzed using the Longformer expert model.",
  "expert_used": "longformer",
  "confidence": 1.0,
  "processing_time": 1.245,
  "input_features": {
    "length": 69,
    "avg_word_length": 4.5,
    "special_char_ratio": 0.03,
    "uppercase_ratio": 0.02,
    "is_binary": 0.0
  }
}
```

## Auto-Routing

Let the MOE service automatically route to the most appropriate expert.

### Request - Short Text (likely ByT5)

```bash
POST http://localhost:8000/process/sync
Content-Type: application/json

{
  "text": "Analyze this regex pattern: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
  "task": "process",
  "options": {}
}
```

### Response

```json
{
  "result": "This regex pattern validates email addresses. It checks for:\n1. Username: Letters, numbers, and some special characters before the @ symbol\n2. Domain: Letters, numbers, and hyphens after the @ symbol\n3. TLD: At least two letters after the last dot",
  "expert_used": "byt5",
  "confidence": 0.88,
  "processing_time": 0.923,
  "input_features": {
    "length": 76,
    "avg_word_length": 5.1,
    "special_char_ratio": 0.21,
    "uppercase_ratio": 0.07,
    "is_binary": 0.0
  }
}
```

### Request - Long Text (likely Longformer)

```bash
POST http://localhost:8000/process/sync
Content-Type: application/json

{
  "text": "This is a much longer text that contains multiple paragraphs and should be routed to the Longformer expert. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies aliquam, nunc nisl aliquet nunc, vitae aliquam nisl nunc vitae nisl. Nullam auctor, nisl eget ultricies aliquam, nunc nisl aliquet nunc, vitae aliquam nisl nunc vitae nisl...",
  "task": "process",
  "options": {}
}
```

### Response

```json
{
  "result": "Analysis of the long-form text: The provided content contains multiple paragraphs discussing Lorem ipsum placeholder text. The key themes include...",
  "expert_used": "longformer",
  "confidence": 0.95,
  "processing_time": 2.134,
  "input_features": {
    "length": 523,
    "avg_word_length": 4.7,
    "special_char_ratio": 0.04,
    "uppercase_ratio": 0.03,
    "is_binary": 0.0
  }
}
```

## Embedding Generation

Generate embeddings for input text.

### Request

```bash
POST http://localhost:8000/process/sync
Content-Type: application/json

{
  "text": "Generate embeddings for this text.",
  "task": "embed",
  "options": {}
}
```

### Response

```json
{
  "result": "ByT5 embeddings generated with shape [1, 768]",
  "expert_used": "byt5",
  "confidence": 0.91,
  "processing_time": 0.645,
  "input_features": {
    "length": 35,
    "avg_word_length": 5.0,
    "special_char_ratio": 0.0,
    "uppercase_ratio": 0.03,
    "is_binary": 0.0
  }
}
```

## Error Handling Examples

### Request - Invalid Task

```bash
POST http://localhost:8000/process/sync
Content-Type: application/json

{
  "text": "This is a test.",
  "task": "invalid_task",
  "options": {}
}
```

### Response

```json
{
  "detail": "Unknown task: invalid_task for expert: byt5",
  "type": "ValueError"
}
```

### Request - Service Overloaded

When the service is overloaded, it may return a 503 status code.

### Response

```json
{
  "detail": "Service temporarily unavailable due to high load",
  "type": "ServiceUnavailableError"
}
```

## TypeScript Client Examples

The following examples demonstrate how to use the TypeScript client to interact with the MOE service from the NextJS application.

### Check MOE Availability

```typescript
import { checkMOEAvailability } from '@/lib/ai/providers/moe';

async function isMOEAvailable() {
  try {
    const available = await checkMOEAvailability();
    console.log(`MOE service available: ${available}`);
    return available;
  } catch (error) {
    console.error('Error checking MOE availability:', error);
    return false;
  }
}
```

### Process Text with MOE

```typescript
import { processMOEText } from '@/lib/ai/providers/moe';

async function processWithMOE(text: string) {
  try {
    const result = await processMOEText(text, {
      task: 'process',
      options: {
        // Optional parameters
      }
    });
    
    console.log(`Processed by ${result.expert_used} with confidence ${result.confidence}`);
    console.log(`Result: ${result.result}`);
    return result;
  } catch (error) {
    console.error('Error processing with MOE:', error);
    return null;
  }
}
```

### Using the MOE Provider

```typescript
import { myProvider } from '@/lib/ai/providers';

async function useMOEProvider(messages: any[]) {
  // Get the MOE auto-routing model
  const model = myProvider.languageModel('moe-auto');
  
  // Process messages
  const result = await model.generate({
    messages,
    maxTokens: 1000
  });
  
  return result;
}
```

### Force Specific Expert

```typescript
import { myProvider } from '@/lib/ai/providers';

async function useSpecificExpert(messages: any[], expert: 'byt5' | 'longformer') {
  // Get the specific expert model
  const modelId = expert === 'byt5' ? 'moe-expert-byt5' : 'moe-expert-longformer';
  const model = myProvider.languageModel(modelId);
  
  // Process messages
  const result = await model.generate({
    messages,
    maxTokens: 1000
  });
  
  return result;
}
```

### Handling Errors and Fallbacks

```typescript
import { processMOEText, MOEError } from '@/lib/ai/providers/moe';

async function processSafely(text: string) {
  try {
    // Try processing with MOE
    const result = await processMOEText(text);
    return result;
  } catch (error) {
    if (error instanceof MOEError) {
      console.warn(`MOE error: ${error.message}, status: ${error.status}`);
      
      // Handle specific error cases
      if (error.status === 408) {
        console.warn('Request timed out, consider breaking down into smaller chunks');
      } else if (error.status === 503) {
        console.warn('MOE service unavailable, using fallback');
      }
    } else {
      console.error('Unexpected error:', error);
    }
    
    // Use fallback processing
    return useFallbackProcessing(text);
  }
}

function useFallbackProcessing(text: string) {
  // Implement fallback processing logic
  return {
    result: `Fallback processing result for: ${text.substring(0, 50)}...`,
    expert_used: 'fallback',
    confidence: 0,
    processing_time: 0
  };
}
```

These examples should help developers understand how to interact with the MOE API and handle various scenarios when implementing or extending the MOE integration.