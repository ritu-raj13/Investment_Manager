"""
Ollama Client Utility for Local LLM Integration
Handles connection, model management, and inference with Ollama
"""

import requests
import json
from typing import Optional, Dict, List, Generator
import os


class OllamaClient:
    """Client for interacting with Ollama local LLM"""
    
    def __init__(self, base_url: Optional[str] = None, default_model: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama API base URL (defaults to config)
            default_model: Default model to use (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
        """
        from config.knowledge_base import config
        
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.default_model = default_model or config.OLLAMA_LLM_MODEL
        self.timeout = timeout or config.OLLAMA_TIMEOUT
        
    def is_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available"""
        models = self.list_models()
        return model_name in models or any(model_name in m for m in models)
    
    def pull_model(self, model_name: str) -> Dict:
        """
        Pull/download a model
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            Dict with status
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=600  # 10 minutes for download
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Model {model_name} pulled successfully"}
            else:
                return {"status": "error", "message": f"Failed to pull model: {response.text}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> Dict:
        """
        Generate text completion
        
        Args:
            prompt: User prompt/question
            model: Model to use (uses default if not specified)
            temperature: Temperature for generation (0.0 - 1.0, lower = more deterministic)
            max_tokens: Maximum tokens to generate
            system_prompt: System prompt for context
            stream: Whether to stream the response
            
        Returns:
            Dict with response text or error
        """
        if not self.is_available():
            return {
                "status": "error",
                "message": "Ollama server is not running. Please start Ollama and ensure the model is available."
            }
        
        model = model or self.default_model
        
        # Check if model is available
        if not self.is_model_available(model):
            return {
                "status": "error",
                "message": f"Model '{model}' is not available. Please pull it first using: ollama pull {model}"
            }
        
        # Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            
            if response.status_code == 200:
                if stream:
                    return {"status": "success", "stream": response.iter_lines()}
                else:
                    result = response.json()
                    return {
                        "status": "success",
                        "response": result.get("response", ""),
                        "model": model
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Generation failed: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timed out. The prompt might be too complex."
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        stream: bool = False
    ) -> Dict:
        """
        Chat completion with conversation history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Temperature for generation
            stream: Whether to stream the response
            
        Returns:
            Dict with response or error
        """
        if not self.is_available():
            return {
                "status": "error",
                "message": "Ollama server is not running."
            }
        
        model = model or self.default_model
        
        if not self.is_model_available(model):
            return {
                "status": "error",
                "message": f"Model '{model}' is not available."
            }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            
            if response.status_code == 200:
                if stream:
                    return {"status": "success", "stream": response.iter_lines()}
                else:
                    result = response.json()
                    return {
                        "status": "success",
                        "response": result.get("message", {}).get("content", ""),
                        "model": model
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Chat failed: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }


# Global instance
ollama_client = OllamaClient()


def get_ollama_client() -> OllamaClient:
    """Get the global Ollama client instance"""
    return ollama_client


