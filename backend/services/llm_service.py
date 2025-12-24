"""LLM service for local and cloud models."""
from typing import Optional, Dict, List
import os

# Import settings at module level to ensure it's loaded
from backend.config import settings

# Debug: Log settings on import
def _log_llm_settings():
    """Log LLM settings when module is imported."""
    print(f"[LLM Service Import] GROQ_API_KEY: {'SET' if settings.groq_api_key else 'NOT SET'} (length: {len(settings.groq_api_key)})")
    print(f"[LLM Service Import] OPENAI_API_KEY: {'SET' if settings.openai_api_key else 'NOT SET'} (length: {len(settings.openai_api_key)})")

_log_llm_settings()

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
        import os
        
        # Debug logging
        print(f"\n[LLM Service] Attempting to generate with cloud LLM...")
        print(f"[LLM Service] GROQ_API_KEY from settings: {'SET' if settings.groq_api_key else 'NOT SET'} (length: {len(settings.groq_api_key)})")
        print(f"[LLM Service] OPENAI_API_KEY from settings: {'SET' if settings.openai_api_key else 'NOT SET'} (length: {len(settings.openai_api_key)})")
        
        # Also check environment variables directly
        env_groq = os.getenv('GROQ_API_KEY', '')
        env_openai = os.getenv('OPENAI_API_KEY', '')
        print(f"[LLM Service] GROQ_API_KEY from env: {'SET' if env_groq else 'NOT SET'} (length: {len(env_groq)})")
        print(f"[LLM Service] OPENAI_API_KEY from env: {'SET' if env_openai else 'NOT SET'} (length: {len(env_openai)})")
        
        # Try to use environment variable if settings doesn't have it
        groq_key = settings.groq_api_key or env_groq
        openai_key = settings.openai_api_key or env_openai
        
        # Try Groq first if available
        if groq_key:
            print(f"[LLM Service] Attempting Groq API call...")
            try:
                from openai import OpenAI
                # Groq uses OpenAI-compatible API
                client = OpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                
                print(f"[LLM Service] Groq client created, making API call...")
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Updated Groq model (llama-3.1-70b was decommissioned)
                    messages=[
                        {"role": "system", "content": "You are a legal assistant helping with French administrative law cases."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                print(f"[LLM Service] Groq API call successful!")
                return response.choices[0].message.content
            except Exception as e:
                print(f"[LLM Service] Error generating with Groq: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                print(f"[LLM Service] Falling back to OpenAI...")
        
        # Fallback to OpenAI
        if openai_key:
            print(f"[LLM Service] Attempting OpenAI API call...")
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                
                print(f"[LLM Service] OpenAI client created, making API call...")
                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are a legal assistant helping with French administrative law cases."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                print(f"[LLM Service] OpenAI API call successful!")
                return response.choices[0].message.content
            except Exception as e:
                print(f"[LLM Service] Error generating with OpenAI: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                return f"Error: {str(e)}"
        
        error_msg = "Error: No LLM API key configured (neither GROQ_API_KEY nor OPENAI_API_KEY found in settings or environment)"
        print(f"[LLM Service] {error_msg}")
        return error_msg
    
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

