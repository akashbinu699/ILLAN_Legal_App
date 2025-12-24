"""LLM service for local and cloud models."""
from typing import Optional, Dict
from backend.config import settings
import os

class LLMService:
    """Service for LLM inference."""
    
    def __init__(self):
        self.local_model = None
        self.use_local = bool(settings.local_llm_path and os.path.exists(settings.local_llm_path))
        
        # TODO: Initialize local LLM (gpt-oss-20b) if available
        # This requires transformers library and model loading
        if self.use_local:
            try:
                # Placeholder for local model initialization
                # from transformers import AutoModelForCausalLM, AutoTokenizer
                # self.tokenizer = AutoTokenizer.from_pretrained(settings.local_llm_path)
                # self.model = AutoModelForCausalLM.from_pretrained(settings.local_llm_path)
                pass
            except Exception as e:
                print(f"Error loading local LLM: {str(e)}")
                self.use_local = False
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate text using LLM."""
        if self.use_local and self.local_model:
            return self._generate_local(prompt, max_tokens, temperature)
        else:
            # Fallback to cloud LLM (OpenAI or other)
            return self._generate_cloud(prompt, max_tokens, temperature)
    
    def _generate_local(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using local LLM."""
        # TODO: Implement local inference
        # This is a placeholder
        raise NotImplementedError("Local LLM not yet implemented. Use cloud fallback.")
    
    def _generate_cloud(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using cloud LLM (Groq preferred, OpenAI as fallback)."""
        # Try Groq first if available
        if settings.groq_api_key:
            try:
                from openai import OpenAI
                # Groq uses OpenAI-compatible API
                client = OpenAI(
                    api_key=settings.groq_api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                
                response = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",  # Fast Groq model
                    messages=[
                        {"role": "system", "content": "You are a legal assistant helping with French administrative law cases."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                return response.choices[0].message.content
            except Exception as e:
                print(f"Error generating with Groq: {str(e)}, falling back to OpenAI")
        
        # Fallback to OpenAI
        if settings.openai_api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                
                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are a legal assistant helping with French administrative law cases."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                return response.choices[0].message.content
            except Exception as e:
                print(f"Error generating with OpenAI: {str(e)}")
                return f"Error: {str(e)}"
        
        return "Error: No LLM API key configured (neither GROQ_API_KEY nor OPENAI_API_KEY)"
    
    def generate_with_citations(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        require_citations: bool = True
    ) -> Dict:
        """Generate response with citations."""
        # Build context from retrieved chunks
        context = "\n\n".join([
            f"[Document {chunk['metadata'].get('document_id', '?')}, "
            f"Page {chunk['metadata'].get('page_number', '?')}]\n"
            f"{chunk['document']}"
            for chunk in retrieved_chunks
        ])
        
        # Build prompt with citation requirements
        citation_instruction = ""
        if require_citations:
            citation_instruction = """
IMPORTANT: You MUST include citations in your response. For each fact or claim you make,
cite the source using this format: [Document ID, Page Number, Section Title (if applicable)].

Example: "According to the notification letter [Doc-123, Page 2, Section: Decision], the client..."
"""
        
        prompt = f"""You are a legal assistant helping with French administrative law cases.

Context from documents:
{context}

Query: {query}

{citation_instruction}

Provide a comprehensive answer based on the context. Include specific citations for all facts and claims."""

        response = self.generate(prompt, max_tokens=2000)
        
        # Extract citations from response (simple regex-based extraction)
        import re
        citations = re.findall(r'\[([^\]]+)\]', response)
        
        return {
            'response': response,
            'citations': citations,
            'chunks_used': [chunk['id'] for chunk in retrieved_chunks]
        }

# Global instance
llm_service = LLMService()

