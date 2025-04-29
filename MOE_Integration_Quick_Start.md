# MOE Integration Quick Start Guide

This guide provides essential information for developers to quickly get started with the Mixture of Experts (MOE) integration in the NextJS chat application.

## Overview

The MOE integration connects specialized AI expert models (ByT5 and Longformer) to the NextJS application through a Python FastAPI service. It provides intelligent routing of user queries to the most appropriate expert model.

## Prerequisites

- NextJS application running on port 3000
- Python 3.8+ with PyTorch and required dependencies
- MOE Python service running on port 8000

## Quick Setup

### 1. Start the MOE Service

```bash
# Install required packages
pip install -r requirements.txt

# Start the MOE service
python fastapi_moe_example.py
```

Verify the service is running:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "cuda_available": true,
  "device": "cuda"
}
```

### 2. Configure NextJS Application

Ensure the following configuration in your NextJS app:

```typescript
// lib/ai/providers/moe.ts
const MOE_API_BASE_URL = process.env.MOE_API_URL || 'http://localhost:8000';
const MOE_TIMEOUT_MS = 30000; // 30 seconds timeout
```

### 3. Server-Side Integration

For optimal performance and SEO, use server-side data fetching:

```typescript
// In your API route (app/(chat)/api/chat/route.ts)
export async function POST(request: Request) {
  // ...
  
  // Check MOE availability server-side
  const isMOEModel = selectedChatModel.startsWith('moe-');
  let moeAvailable = false;
  
  if (isMOEModel) {
    try {
      moeAvailable = await checkMOEAvailability();
    } catch (error) {
      console.error('Error checking MOE availability:', error);
    }
  }
  
  // Process with MOE or fallback appropriately
  // ...
}
```

## Using MOE Models

### Available Models

- **MOE ByT5 Expert** (`moe-expert-byt5`): For specialized text processing
- **MOE Longformer Expert** (`moe-expert-longformer`): For long document processing
- **MOE Auto-Routing** (`moe-auto`): Automatically selects the best expert

### Best Practices

1. **Proper Error Handling**
   ```typescript
   try {
     const moeResponse = await processMOEText(userText);
     return {
       result: moeResponse.result,
       expertUsed: moeResponse.expert_used,
       // ...
     };
   } catch (error) {
     console.error('MOE processing failed:', error);
     return { usedFallback: true };
   }
   ```

2. **Avoid Hydration Mismatches**
   ```typescript
   // Use useEffect for client-side MOE updates
   useEffect(() => {
     if (moeResponse && !moeResponse.usedFallback) {
       setExpertUsed(moeResponse.expertUsed);
     }
   }, [moeResponse]);
   ```

3. **Prevent Resource Contention**
   ```typescript
   // Use AbortController for timeouts
   const controller = new AbortController();
   const timeoutId = setTimeout(() => controller.abort(), MOE_TIMEOUT_MS);
   
   try {
     const response = await fetch(`${MOE_API_BASE_URL}/process/sync`, {
       // ... request options
       signal: controller.signal,
     });
     
     clearTimeout(timeoutId);
     // ... process response
   } catch (error) {
     // ... handle errors
   }
   ```

4. **Implement Monitoring**
   ```typescript
   // Add performance monitoring
   const startTime = performance.now();
   const result = await processMOERequest(messages);
   const processingTime = performance.now() - startTime;
   
   console.log(`MOE processing completed in ${processingTime}ms using ${result.expertUsed}`);
   ```

5. **Add Security Measures**
   ```typescript
   // Implement rate limiting for MOE endpoints
   import { rateLimit } from 'next-connect';
   
   const limiter = rateLimit({
     windowMs: 15 * 60 * 1000, // 15 minutes
     max: 100 // limit each IP to 100 requests per windowMs
   });
   
   // Apply limiter to your API route
   ```

## Troubleshooting

### MOE Service Unavailable
If the MOE service is unavailable, the system will automatically fall back to the default chat model. Check:

1. Is the MOE service running? `curl http://localhost:8000/health`
2. Is the MOE_API_BASE_URL correctly configured?
3. Check MOE service logs for errors

### Slow Responses
If responses are slow:

1. Check MOE service resource utilization
2. Consider adjusting MOE_TIMEOUT_MS if needed
3. For large inputs, consider chunking or using progressive response generation

## Next Steps

Once you have the basic integration working:

1. Review the comprehensive documentation in `MOE_Integration_Documentation.md`
2. Explore extending the system with your own custom expert models
3. Implement monitoring and logging for production deployments

For detailed information, see the complete MOE Integration Documentation.