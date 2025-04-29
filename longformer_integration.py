"""
Longformer Integration for MOE Framework
----------------------------------------
This module implements the integration of Longformer model for sparse attention
to handle long sequences within the Mixture of Experts (MOE) framework.
"""

import torch
import torch.nn.functional as F
from transformers import LongformerModel, LongformerTokenizer
from typing import Dict, List, Tuple, Union, Optional


class LongformerExpert:
    """
    Longformer expert for handling long sequences in the MOE framework.
    """
    def __init__(self, model_name: str = "allenai/longformer-base-4096", 
                 device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        Initialize the Longformer expert.
        
        Args:
            model_name: Name of the Longformer model to use
            device: Device to run the model on
        """
        self.model_name = model_name
        self.device = device
        
        # Load model and tokenizer
        print(f"Loading Longformer model: {model_name}")
        self.model = LongformerModel.from_pretrained(model_name)
        self.tokenizer = LongformerTokenizer.from_pretrained(model_name)
        
        # Move model to device
        self.model.to(device)
        
        # Set model to evaluation mode
        self.model.eval()
        
        # Maximum sequence length
        self.max_length = self.model.config.max_position_embeddings
    
    def process_long_text(self, text: str) -> torch.Tensor:
        """
        Process long text using Longformer's sparse attention.
        
        Args:
            text: Long text to process
            
        Returns:
            Processed embeddings
        """
        # Tokenize input
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding="max_length", 
            truncation=True,
            max_length=self.max_length
        )
        
        # Move inputs to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Set global attention on the first token
        global_attention_mask = torch.zeros_like(inputs["attention_mask"])
        global_attention_mask[:, 0] = 1
        inputs["global_attention_mask"] = global_attention_mask
        
        # Process with Longformer
        with torch.no_grad():
            # Use gradient checkpointing for memory efficiency
            self.model.config.use_cache = False
            
            # Get outputs
            outputs = self.model(**inputs)
            
            # Use the last hidden state as embeddings
            embeddings = outputs.last_hidden_state
        
        return embeddings
    
    def get_document_embedding(self, text: str) -> torch.Tensor:
        """
        Get document-level embedding for long text.
        
        Args:
            text: Long text to get embedding for
            
        Returns:
            Document embedding tensor
        """
        # Get token-level embeddings
        token_embeddings = self.process_long_text(text)
        
        # Use CLS token (first token) as document embedding
        document_embedding = token_embeddings[:, 0, :]
        
        return document_embedding
    
    def process_with_checkpointing(self, text: str) -> torch.Tensor:
        """
        Process long text using Longformer with gradient checkpointing for memory efficiency.
        
        Args:
            text: Long text to process
            
        Returns:
            Processed embeddings
        """
        # Tokenize input
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding="max_length", 
            truncation=True,
            max_length=self.max_length
        )
        
        # Move inputs to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Set global attention on the first token
        global_attention_mask = torch.zeros_like(inputs["attention_mask"])
        global_attention_mask[:, 0] = 1
        inputs["global_attention_mask"] = global_attention_mask
        
        # Enable gradient checkpointing
        self.model.gradient_checkpointing_enable()
        
        # Process with Longformer
        with torch.no_grad():
            # Use gradient checkpointing for memory efficiency
            self.model.config.use_cache = False
            
            # Get outputs
            outputs = self.model(**inputs)
            
            # Use the last hidden state as embeddings
            embeddings = outputs.last_hidden_state
        
        # Disable gradient checkpointing
        self.model.gradient_checkpointing_disable()
        
        return embeddings
    
    def chunk_and_process(self, text: str, chunk_size: int = 4000, overlap: int = 100) -> List[torch.Tensor]:
        """
        Process very long text by chunking it into overlapping segments.
        
        Args:
            text: Very long text to process
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of embeddings for each chunk
        """
        # Split text into chunks
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Keep some overlap for context
                overlap_words = current_chunk[-overlap:]
                current_chunk = overlap_words
                current_length = sum(len(word) + 1 for word in current_chunk)
            
            current_chunk.append(word)
            current_length += len(word) + 1
        
        # Add the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        # Process each chunk
        chunk_embeddings = []
        for chunk in chunks:
            embedding = self.get_document_embedding(chunk)
            chunk_embeddings.append(embedding)
        
        return chunk_embeddings
    
    def summarize_chunks(self, chunk_embeddings: List[torch.Tensor]) -> torch.Tensor:
        """
        Summarize chunk embeddings into a single document embedding.
        
        Args:
            chunk_embeddings: List of embeddings for each chunk
            
        Returns:
            Summarized document embedding
        """
        # Stack chunk embeddings
        stacked_embeddings = torch.cat(chunk_embeddings, dim=0)
        
        # Average pooling
        document_embedding = torch.mean(stacked_embeddings, dim=0, keepdim=True)
        
        return document_embedding


# Example usage
def test_longformer_expert():
    """
    Test the Longformer expert.
    """
    # Initialize Longformer expert
    longformer_expert = LongformerExpert()
    
    # Test with short text
    short_text = "This is a test of the Longformer expert for processing short text."
    short_embeddings = longformer_expert.process_long_text(short_text)
    print(f"Short text embeddings shape: {short_embeddings.shape}")
    
    # Test with long text
    long_text = "This is a test of the Longformer expert for processing long text. " * 100
    long_embeddings = longformer_expert.process_long_text(long_text)
    print(f"Long text embeddings shape: {long_embeddings.shape}")
    
    # Test document embedding
    document_embedding = longformer_expert.get_document_embedding(long_text)
    print(f"Document embedding shape: {document_embedding.shape}")
    
    # Test with gradient checkpointing
    checkpointed_embeddings = longformer_expert.process_with_checkpointing(long_text)
    print(f"Checkpointed embeddings shape: {checkpointed_embeddings.shape}")
    
    # Test chunking for very long text
    very_long_text = "This is a test of the Longformer expert for processing very long text. " * 1000
    chunk_embeddings = longformer_expert.chunk_and_process(very_long_text)
    print(f"Number of chunks: {len(chunk_embeddings)}")
    print(f"Chunk embedding shape: {chunk_embeddings[0].shape}")
    
    # Test summarizing chunks
    summarized_embedding = longformer_expert.summarize_chunks(chunk_embeddings)
    print(f"Summarized embedding shape: {summarized_embedding.shape}")


if __name__ == "__main__":
    # Test Longformer expert
    test_longformer_expert()
