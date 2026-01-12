"""LLM service for local and cloud models."""
from typing import Optional, Dict, List
import os

# Import settings at module level to ensure it's loaded
from backend.config import settings

# Debug: Log settings on import
def _log_llm_settings():
    """Log LLM settings when module is imported."""
    print(f"[LLM Service Import] GEMINI_API_KEY: {'SET' if settings.gemini_api_key else 'NOT SET'} (length: {len(settings.gemini_api_key)})")
    print(f"[LLM Service Import] OPENAI_API_KEY: {'SET' if settings.openai_api_key else 'NOT SET'} (length: {len(settings.openai_api_key)})")
    print(f"[LLM Service Import] GROQ_API_KEY: {'SET' if settings.groq_api_key else 'NOT SET'} (length: {len(settings.groq_api_key)})")

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
    
    async def generate(
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
            # Use asyncio.to_thread because the underlying _generate_cloud is sync (uses requests/genai sync)
            import asyncio
            return await asyncio.to_thread(self._generate_cloud, prompt, max_tokens, temperature)
    
    def _generate_local(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using local LLM."""
        # TODO: Implement local inference
        # This is a placeholder
        raise NotImplementedError("Local LLM not yet implemented. Use cloud fallback.")
    
    def _generate_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using Google Gemini 3 API."""
        try:
            import google.generativeai as genai
            
            # Configure Gemini
            genai.configure(api_key=settings.gemini_api_key)
            
            # Use Gemini 2.0 Flash (or fallback to 1.5 Pro if 2.0 not available)
            model_name = "gemini-2.0-flash-exp"
            try:
                model = genai.GenerativeModel(model_name)
            except Exception:
                # Fallback to 1.5 Pro if 2.0 not available
                model_name = "gemini-1.5-pro"
                model = genai.GenerativeModel(model_name)
            
            print(f"[LLM Service] Using Gemini model: {model_name}")
            
            # Generate content
            # Gemini uses system instruction in generation_config
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            # Combine system and user prompt
            full_prompt = f"""You are a legal assistant helping with French administrative law cases.

{prompt}"""
            
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            print(f"[LLM Service] Gemini API call successful!")
            return response.text
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"[LLM Service] Error generating with Gemini: {error_type}: {error_msg}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to trigger fallback
    
    def _generate_cloud(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using cloud LLM with fallback chain: Gemini 3 → OpenAI → Groq."""
        import os
        
        # Debug logging
        print(f"\n[LLM Service] Attempting to generate with cloud LLM...")
        print(f"[LLM Service] GEMINI_API_KEY from settings: {'SET' if settings.gemini_api_key else 'NOT SET'} (length: {len(settings.gemini_api_key)})")
        print(f"[LLM Service] OPENAI_API_KEY from settings: {'SET' if settings.openai_api_key else 'NOT SET'} (length: {len(settings.openai_api_key)})")
        print(f"[LLM Service] GROQ_API_KEY from settings: {'SET' if settings.groq_api_key else 'NOT SET'} (length: {len(settings.groq_api_key)})")
        
        # Also check environment variables directly
        env_gemini = os.getenv('GEMINI_API_KEY', '')
        env_openai = os.getenv('OPENAI_API_KEY', '')
        env_groq = os.getenv('GROQ_API_KEY', '')
        print(f"[LLM Service] GEMINI_API_KEY from env: {'SET' if env_gemini else 'NOT SET'} (length: {len(env_gemini)})")
        print(f"[LLM Service] OPENAI_API_KEY from env: {'SET' if env_openai else 'NOT SET'} (length: {len(env_openai)})")
        print(f"[LLM Service] GROQ_API_KEY from env: {'SET' if env_groq else 'NOT SET'} (length: {len(env_groq)})")
        
        # Try to use environment variable if settings doesn't have it
        gemini_key = (settings.gemini_api_key or env_gemini).strip()
        openai_key = (settings.openai_api_key or env_openai).strip()
        groq_key = (settings.groq_api_key or env_groq).strip()
        
        # 1. Try Gemini first (primary LLM)
        if gemini_key:
            print(f"[LLM Service] Attempting Gemini API call...")
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                
                # Preferred models in order - explicitly use 'models/' prefix as seen in list_models()
                preferred_models = [
                    "models/gemini-1.5-flash",
                    "models/gemini-flash-latest",
                    "models/gemini-2.0-flash",
                    "models/gemini-1.5-pro",
                    "models/gemini-pro-latest",
                    "models/gemini-2.0-flash-exp"
                ]
                
                # Check what's available
                available_models = []
                try:
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    print(f"[LLM Service] Available Gemini models: {available_models}")
                except Exception as e:
                    print(f"[LLM Service] Error listing models: {e}")
                    available_models = ["models/gemini-1.5-flash"] # Default fallback
                
                # Create a list of models to try (preferred first, then others)
                models_to_try = []
                for pref in preferred_models:
                    if pref in available_models:
                        models_to_try.append(pref)
                    elif pref.replace("models/", "") in available_models:
                        models_to_try.append(pref.replace("models/", ""))
                
                # Add any other available models that weren't in preferred
                for m in available_models:
                    if m not in models_to_try:
                        models_to_try.append(m)
                
                last_error = None
                for target_model in models_to_try:
                    try:
                        print(f"[LLM Service] Trying Gemini model: {target_model}...")
                        model = genai.GenerativeModel(target_model)
                        
                        generation_config = {
                            "temperature": temperature,
                            "max_output_tokens": max_tokens,
                        }
                        
                        full_prompt = f"You are a legal assistant helping with French administrative law cases.\n\n{prompt}"
                        
                        response = model.generate_content(
                            full_prompt,
                            generation_config=generation_config
                        )
                        
                        print(f"[LLM Service] Gemini API call successful with {target_model}!")
                        return response.text
                    except Exception as model_e:
                        last_error = str(model_e)
                        print(f"[LLM Service] Model {target_model} failed: {last_error}")
                        # If it's a 429 or 404, try the next model in the list
                        continue
                
                if last_error:
                    raise Exception(f"All Gemini models failed. Last error: {last_error}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"[LLM Service] Gemini failed overall: {error_msg}")
                import traceback
                traceback.print_exc()
                
        # 2. Fallback to OpenAI
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
                error_type = type(e).__name__
                error_msg = str(e)
                print(f"[LLM Service] Error generating with OpenAI: {error_type}: {error_msg}")
                import traceback
                traceback.print_exc()
                
                # Check if it's a rate limit error
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    print(f"[LLM Service] OpenAI rate limit hit. Falling back to Groq...")
                else:
                    print(f"[LLM Service] OpenAI error. Falling back to Groq...")
        
        # 3. Fallback to Groq
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
                error_type = type(e).__name__
                error_msg = str(e)
                print(f"[LLM Service] Error generating with Groq: {error_type}: {error_msg}")
                import traceback
                traceback.print_exc()
        
        # All LLMs failed - return error message
        if gemini_key and openai_key and groq_key:
            error_msg = "Error: All LLM providers (Gemini 3, OpenAI, Groq) failed. Please check API keys and quotas."
        elif gemini_key and openai_key:
            error_msg = "Error: Both Gemini 3 and OpenAI failed. Groq API key not configured."
        elif gemini_key and groq_key:
            error_msg = "Error: Both Gemini 3 and Groq failed. OpenAI API key not configured."
        elif openai_key and groq_key:
            error_msg = "Error: Both OpenAI and Groq failed. Gemini 3 API key not configured."
        elif gemini_key:
            error_msg = "Error: Gemini 3 failed. No fallback API keys (OpenAI or Groq) configured."
        elif openai_key:
            error_msg = "Error: OpenAI failed. No fallback API keys (Gemini 3 or Groq) configured."
        elif groq_key:
            error_msg = "Error: Groq failed. No fallback API keys (Gemini 3 or OpenAI) configured."
        else:
            error_msg = "Error: No LLM API key configured. Please set GEMINI_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY in .env file."
        
        print(f"[LLM Service] {error_msg}")
        return error_msg
    
    async def generate_with_citations(
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

        response = await self.generate(prompt, max_tokens=2000)
        
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

