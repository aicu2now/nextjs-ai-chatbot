"""
Complete FastAPI MOE Framework Example
-------------------------------------
This module provides a complete example of a FastAPI application
implementing the Mixture of Experts (MOE) framework with transformer models.
"""

import os
import time
import torch
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Tuple, Union, Optional, Any

# Import MOE components
# Note: In a real deployment, these would be proper imports
# For this example, we'll assume these modules are in the same directory
from moe_gating_mechanism import MOEGatingMechanism, InputAnalyzer
from byt5_integration import ByT5Expert
from longformer_integration import LongformerExpert
from moe_optimizations import MOEOptimizer


class InputData(BaseModel):
    """
    Input data model for the MOE API.
    """
    text: str = Field(..., description="Text to process")
    task: Optional[str] = Field("process", description="Task to perform (process, embed, analyze)")
    options: Optional[Dict[str, Any]] = Field({}, description="Additional options for processing")


class OutputData(BaseModel):
    """
    Output data model for the MOE API.
    """
    result: str = Field(..., description="Processing result")
    expert_used: str = Field(..., description="Expert model used for processing")
    confidence: float = Field(..., description="Confidence score for expert selection")
    processing_time: float = Field(..., description="Processing time in seconds")
    input_features: Optional[Dict[str, float]] = Field(None, description="Input features used for routing")


class MOEProcessor:
    """
    Main processor for the MOE framework, integrating all components.
    """
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        Initialize the MOE processor.
        
        Args:
            device: Device to use for processing
        """
        self.device = device
        self.analyzer = InputAnalyzer()
        
        # Initialize experts
        print("Initializing expert models...")
        self.byt5_expert = ByT5Expert(device=device)
        self.longformer_expert = LongformerExpert(device=device)
        
        # Create expert models dictionary
        self.expert_models = {
            "byt5": self.byt5_expert.model,
            "longformer": self.longformer_expert.model
        }
        
        # Initialize MOE gating mechanism
        print("Initializing MOE gating mechanism...")
        self.moe_gating = MOEGatingMechanism(self.expert_models, device=device)
        
        # Initialize MOE optimizer
        print("Initializing MOE optimizer...")
        self.moe_optimizer = MOEOptimizer(device=device)
        
        # Optimize expert models
        print("Optimizing expert models...")
        self.expert_models = self.moe_optimizer.optimize_expert_models(self.expert_models)
        
        print("MOE processor initialized successfully!")
    
    def preprocess_input(self, input_data: InputData) -> Tuple[str, Dict[str, float]]:
        """
        Preprocess input data before routing to experts.
        
        Args:
            input_data: Input data to preprocess
            
        Returns:
            Tuple of (preprocessed_text, features)
        """
        text = input_data.text
        
        # Check if input is binary
        is_binary = False
        try:
            text.encode('utf-8').decode('utf-8')
        except UnicodeDecodeError:
            # Convert binary to hex representation for processing
            text = text.hex()
            is_binary = True
        
        # Extract features for routing
        features = self.analyzer.analyze(text)
        features['is_binary'] = 1.0 if is_binary else 0.0
        
        return text, features
    
    def route_to_expert(self, text: str, features: Dict[str, float]) -> Tuple[str, float]:
        """
        Route input to the appropriate expert.
        
        Args:
            text: Input text to route
            features: Input features for routing
            
        Returns:
            Tuple of (expert_name, confidence)
        """
        # Convert features to tensor
        feature_vector = torch.tensor([
            features['length'] / 1000,  # Normalize length
            features['avg_word_length'] / 10,  # Normalize avg word length
            features['special_char_ratio'],
            features['uppercase_ratio'],
            features['is_binary']
        ], dtype=torch.float32).to(self.device)
        
        # Use MOE gating mechanism to select expert
        with torch.no_grad():
            routing_probs = self.moe_gating.gate(feature_vector.unsqueeze(0)).squeeze(0)
            expert_idx = torch.argmax(routing_probs).item()
            expert_name = self.moe_gating.idx_to_expert[expert_idx]
            confidence = routing_probs[expert_idx].item()
        
        return expert_name, confidence
    
    def process_with_expert(self, text: str, expert_name: str, task: str) -> str:
        """
        Process input with the selected expert.
        
        Args:
            text: Input text to process
            expert_name: Name of the expert to use
            task: Task to perform (process, embed, analyze)
            
        Returns:
            Processed text
        """
        if expert_name == "byt5":
            # Process with ByT5 expert
            if task == "process":
                result = self.byt5_expert.process_with_checkpointing(text)
            elif task == "embed":
                embeddings = self.byt5_expert.get_embeddings(text)
                result = f"ByT5 embeddings generated with shape {embeddings.shape}"
            else:
                result = f"Unknown task: {task} for expert: {expert_name}"
        
        elif expert_name == "longformer":
            # Process with Longformer expert
            if task == "process":
                embeddings = self.longformer_expert.process_with_checkpointing(text)
                result = f"Processed with Longformer, embedding shape: {embeddings.shape}"
            elif task == "embed":
                document_embedding = self.longformer_expert.get_document_embedding(text)
                result = f"Longformer document embedding generated with shape {document_embedding.shape}"
            else:
                result = f"Unknown task: {task} for expert: {expert_name}"
        
        else:
            # Default processing
            result = f"Unknown expert: {expert_name}"
        
        return result
    
    def postprocess_output(self, result: str, options: Dict[str, Any]) -> str:
        """
        Postprocess output after expert processing.
        
        Args:
            result: Result to postprocess
            options: Additional options for postprocessing
            
        Returns:
            Postprocessed result
        """
        # Apply any postprocessing based on options
        if options.get("truncate_length"):
            max_length = options["truncate_length"]
            if len(result) > max_length:
                result = result[:max_length] + "..."
        
        if options.get("to_uppercase", False):
            result = result.upper()
        
        return result
    
    async def process_async(self, input_data: InputData) -> OutputData:
        """
        Process input data asynchronously.
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed output data
        """
        start_time = time.time()
        
        # Preprocess input
        preprocessed_text, features = self.preprocess_input(input_data)
        
        # Route to expert
        expert_name, confidence = self.route_to_expert(preprocessed_text, features)
        
        # Process with expert
        result = self.process_with_expert(preprocessed_text, expert_name, input_data.task)
        
        # Postprocess output
        final_result = self.postprocess_output(result, input_data.options)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create output data
        output_data = OutputData(
            result=final_result,
            expert_used=expert_name,
            confidence=confidence,
            processing_time=processing_time,
            input_features=features
        )
        
        return output_data
    
    def process(self, input_data: InputData) -> OutputData:
        """
        Process input data synchronously.
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed output data
        """
        start_time = time.time()
        
        # Preprocess input
        preprocessed_text, features = self.preprocess_input(input_data)
        
        # Route to expert
        expert_name, confidence = self.route_to_expert(preprocessed_text, features)
        
        # Process with expert
        result = self.process_with_expert(preprocessed_text, expert_name, input_data.task)
        
        # Postprocess output
        final_result = self.postprocess_output(result, input_data.options)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create output data
        output_data = OutputData(
            result=final_result,
            expert_used=expert_name,
            confidence=confidence,
            processing_time=processing_time,
            input_features=features
        )
        
        return output_data


# Create FastAPI application
app = FastAPI(
    title="MOE Transformer API",
    description="API for Mixture of Experts transformer processing",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MOE processor
moe_processor = None

@app.on_event("startup")
async def startup_event():
    """
    Initialize MOE processor on startup.
    """
    global moe_processor
    moe_processor = MOEProcessor()

@app.post("/process", response_model=OutputData)
async def process_data(input_data: InputData, background_tasks: BackgroundTasks):
    """
    Process input data with MOE framework.
    
    Args:
        input_data: Input data to process
        background_tasks: Background tasks for async processing
        
    Returns:
        Processed output data
    """
    if moe_processor is None:
        raise HTTPException(status_code=503, detail="MOE processor not initialized")
    
    # Process input data
    output_data = await moe_processor.process_async(input_data)
    
    return output_data

@app.post("/process/sync", response_model=OutputData)
def process_data_sync(input_data: InputData):
    """
    Process input data synchronously with MOE framework.
    
    Args:
        input_data: Input data to process
        
    Returns:
        Processed output data
    """
    if moe_processor is None:
        raise HTTPException(status_code=503, detail="MOE processor not initialized")
    
    # Process input data
    output_data = moe_processor.process(input_data)
    
    return output_data

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy", 
        "models_loaded": moe_processor is not None,
        "cuda_available": torch.cuda.is_available(),
        "device": moe_processor.device if moe_processor else "not initialized"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    
    Args:
        request: Request that caused the exception
        exc: Exception that was raised
        
    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the FastAPI server.
    
    Args:
        host: Host to run the server on
        port: Port to run the server on
    """
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Run the server
    run_server()
