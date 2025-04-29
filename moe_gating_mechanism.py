"""
MOE Gating Mechanism for Transformer Models
-------------------------------------------
This module implements a simple Mixture of Experts (MOE) gating mechanism
that routes inputs to the appropriate transformer model based on input characteristics.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel, AutoModelForSeq2SeqLM
from typing import Dict, List, Tuple, Union, Optional


class SimpleGate(nn.Module):
    """
    A simple neural network-based gating mechanism for routing inputs to experts.
    """
    def __init__(self, input_dim: int, num_experts: int):
        super().__init__()
        self.input_dim = input_dim
        self.num_experts = num_experts
        
        # Simple feed-forward network for gating
        self.gate = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, num_experts),
            nn.Softmax(dim=-1)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the gating network.
        
        Args:
            x: Input tensor of shape [batch_size, input_dim]
            
        Returns:
            Tensor of shape [batch_size, num_experts] containing routing probabilities
        """
        return self.gate(x)


class InputAnalyzer:
    """
    Analyzes input characteristics to create features for the gating mechanism.
    """
    def __init__(self):
        pass
    
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze input text and extract features for gating.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary of features
        """
        features = {}
        
        # Length-based features
        features['length'] = len(text)
        features['avg_word_length'] = sum(len(word) for word in text.split()) / max(1, len(text.split()))
        
        # Complexity features
        features['special_char_ratio'] = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(1, len(text))
        features['uppercase_ratio'] = sum(1 for c in text if c.isupper()) / max(1, len(text))
        
        # Binary content detection
        try:
            text.encode('utf-8').decode('utf-8')
            features['is_binary'] = 0.0
        except UnicodeDecodeError:
            features['is_binary'] = 1.0
        
        return features
    
    def featurize(self, text: str) -> torch.Tensor:
        """
        Convert text to feature tensor for gating.
        
        Args:
            text: Input text
            
        Returns:
            Feature tensor
        """
        features = self.analyze(text)
        feature_vector = torch.tensor([
            features['length'] / 1000,  # Normalize length
            features['avg_word_length'] / 10,  # Normalize avg word length
            features['special_char_ratio'],
            features['uppercase_ratio'],
            features['is_binary']
        ], dtype=torch.float32)
        
        return feature_vector


class MOEGatingMechanism:
    """
    Mixture of Experts gating mechanism that routes inputs to appropriate transformer models.
    """
    def __init__(self, expert_models: Dict[str, AutoModel], device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.expert_models = expert_models
        self.device = device
        self.analyzer = InputAnalyzer()
        
        # Initialize gating network
        self.gate = SimpleGate(input_dim=5, num_experts=len(expert_models))
        self.gate.to(device)
        
        # Map expert indices to names
        self.idx_to_expert = {i: name for i, name in enumerate(expert_models.keys())}
    
    def select_expert(self, text: str) -> Tuple[str, float]:
        """
        Select the most appropriate expert for the given input.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (expert_name, confidence)
        """
        # Extract features
        features = self.analyzer.featurize(text).unsqueeze(0).to(self.device)
        
        # Get routing probabilities
        with torch.no_grad():
            routing_probs = self.gate(features).squeeze(0)
        
        # Select expert with highest probability
        expert_idx = torch.argmax(routing_probs).item()
        expert_name = self.idx_to_expert[expert_idx]
        confidence = routing_probs[expert_idx].item()
        
        return expert_name, confidence
    
    def route(self, text: str) -> Tuple[AutoModel, str, float]:
        """
        Route the input to the appropriate expert.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (expert_model, expert_name, confidence)
        """
        expert_name, confidence = self.select_expert(text)
        return self.expert_models[expert_name], expert_name, confidence
    
    def train_gate(self, texts: List[str], labels: List[int], 
                  learning_rate: float = 1e-4, epochs: int = 10):
        """
        Train the gating network with labeled examples.
        
        Args:
            texts: List of input texts
            labels: List of expert indices
            learning_rate: Learning rate for optimization
            epochs: Number of training epochs
        """
        # Prepare optimizer
        optimizer = torch.optim.Adam(self.gate.parameters(), lr=learning_rate)
        
        # Prepare data
        features = torch.stack([self.analyzer.featurize(text) for text in texts]).to(self.device)
        labels = torch.tensor(labels, dtype=torch.long).to(self.device)
        
        # Training loop
        self.gate.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            # Forward pass
            routing_probs = self.gate(features)
            
            # Compute loss
            loss = F.cross_entropy(routing_probs, labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
        
        self.gate.eval()


# Example usage
def create_moe_with_existing_transformers():
    """
    Create a MOE gating mechanism with existing transformer models.
    """
    # Initialize expert models
    expert_models = {
        "byt5": AutoModelForSeq2SeqLM.from_pretrained("google/byt5-small"),
        "longformer": AutoModel.from_pretrained("allenai/longformer-base-4096"),
        "bert": AutoModel.from_pretrained("bert-base-uncased")
    }
    
    # Create MOE gating mechanism
    moe = MOEGatingMechanism(expert_models)
    
    # Example training data (in practice, this would be more extensive)
    texts = [
        "This is a short text for BERT.",
        "This is a very long document with multiple paragraphs and sentences that would be better handled by a model that can process long sequences efficiently. " * 10,
        "Binary data: \x00\x01\x02\x03\x04\x05"
    ]
    
    # Labels: 0 for bert, 1 for longformer, 2 for byt5
    labels = [0, 1, 2]
    
    # Train the gating mechanism
    moe.train_gate(texts, labels, epochs=5)
    
    return moe


if __name__ == "__main__":
    # Example usage
    moe = create_moe_with_existing_transformers()
    
    # Test routing
    test_inputs = [
        "This is a short text.",
        "This is a very long document with multiple paragraphs and sentences. " * 20,
        "Binary data: \x00\x01\x02\x03\x04\x05"
    ]
    
    for text in test_inputs:
        expert, name, confidence = moe.route(text)
        print(f"Input: {text[:50]}...")
        print(f"Selected expert: {name} with confidence: {confidence:.4f}")
        print("-" * 50)
