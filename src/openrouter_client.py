"""
OpenRouter API client with retry logic and token tracking.
"""

import json
import time
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI


class OpenRouterClient:
    """Client for communicating with OpenRouter API."""
    
    def __init__(self, api_key: str, site_url: str = None, site_name: str = None):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.site_url = site_url
        self.site_name = site_name
        self.max_retries = 2
        
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for OpenRouter requests."""
        headers = {}
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name
        return headers
    
    def _parse_token_usage(self, response) -> Dict[str, int]:
        """Extract token usage from OpenRouter response."""
        usage = response.usage
        return {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0
        }
    
    def send_message(self, model: str, prompt: str, temperature: float = 0.7, 
                    max_tokens: int = 2000) -> Tuple[Optional[Dict[str, Any]], str, Dict[str, int], float]:
        """
        Send message to OpenRouter API with retry logic.
        
        Returns:
        - response_json: Parsed JSON response from model (None if failed)
        - raw_response: Raw text response from model
        - token_usage: Token usage statistics
        - response_time: Response time in seconds
        """
        headers = self._build_headers()
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    extra_headers=headers,
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=temperature,
                    max_tokens=None
                )
                
                response_time = time.time() - start_time
                raw_response = response.choices[0].message.content
                token_usage = self._parse_token_usage(response)
                
                # Try to parse as JSON
                response_json = None
                try:
                    response_json = json.loads(raw_response)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks or other formats
                    response_json = self._extract_json_from_text(raw_response)
                
                return response_json, raw_response, token_usage, response_time
                
            except Exception as e:
                error_msg = f"API call failed (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}"
                print(f"Error: {error_msg}")
                
                if attempt == self.max_retries:
                    # Final attempt failed - exit with error
                    print(f"API communication failed after {self.max_retries + 1} attempts. Exiting.")
                    raise SystemExit(1)
                
                # Wait before retry
                time.sleep(1)
        
        # Should never reach here
        return None, "", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, 0.0
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Try to extract JSON from text that might contain markdown code blocks
        or other formatting around the actual JSON.
        """
        # Try to find JSON in markdown code blocks
        import re
        
        # Look for ```json ... ``` blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Try to find standalone JSON objects
        json_pattern = r'(\{[^{}]*"path"[^{}]*"analysis"[^{}]*\})'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Look for any JSON-like structure
        try:
            # Find the first { and last }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                potential_json = text[start:end+1]
                return json.loads(potential_json)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def validate_response_format(self, response_json: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that the response has the required format.
        Expected format: {"path": "...", "analysis": "..."}
        """
        if not isinstance(response_json, dict):
            return False, "Response is not a valid JSON object"
        
        if "path" not in response_json:
            return False, "Missing 'path' field in response"
        
        if "analysis" not in response_json:
            return False, "Missing 'analysis' field in response"
        
        if not isinstance(response_json["path"], str):
            return False, "'path' field must be a string"
        
        if not isinstance(response_json["analysis"], str):
            return False, "'analysis' field must be a string"
        
        # Check if path is empty
        if not response_json["path"].strip():
            return False, "'path' field cannot be empty"
        
        return True, "Valid response format"


def create_client(api_key: str, site_url: str = None, site_name: str = None) -> OpenRouterClient:
    """Factory function to create OpenRouter client."""
    return OpenRouterClient(api_key, site_url, site_name)