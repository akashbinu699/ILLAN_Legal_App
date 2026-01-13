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
        """Generate using Gemini (User requested no OpenAI)."""
        
        # Helper to try generation
        def try_generate(model_name):
            print(f"[LLM Service] Trying Gemini model: {model_name}...")
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                f"You are a legal assistant helping with French administrative law cases.\n\n{prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            return response.text

        # List of models to try
        models = ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro"]
        
        last_error = None
        for m in models:
            try:
                return try_generate(m)
            except Exception as e:
                print(f"[LLM Service] Failed with {m}: {e}")
                last_error = e
        
        return f"Error: Gemini analysis failed. {last_error}"
    
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

    async def analyze_case_stage_and_benefits(
        self,
        description: str,
        files_content: List[str] = None
    ) -> Dict:
        """
        Analyze case description to determine stage and benefits.
        Returns a dict with 'stage' and 'benefits' keys.
        """
        benefits_list = [
            'APL', 'RSA', 'PPA', 'NOEL', 'AUUVVC', 'AMENDE', 
            'RECOUV', 'ACADINASS', 'CAFINASS', 'MAJO', 'AAH', 
            'AEEH', 'AJPP', 'AJPA', 'AVPF', 'AUTRES'
        ]
        
        stages_list = ['Contradictory', 'RAPO', 'Litigation']
        
        # Knowledge Base Loading
        knowledge_base = ""
        try:
            # Try to load from external file
            import os
            # Assuming llm_service.py is in backend/services/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            kb_path = os.path.join(current_dir, '..', 'knowledge_base.md')
            
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    knowledge_base = f.read()
                print(f"[LLM] Loaded external knowledge base from {kb_path}")
        except Exception as e:
            print(f"[LLM] Error reading knowledge base file: {e}")

        if not knowledge_base:
            # Default Knowledge Base
            knowledge_base = """
            REFERENCE DES PRESTATIONS ET PROCEDURES :
            
            1. [APL] Aides personnelles au logement (APL / ALS) et Prime de déménagement.
               - Procédure : Recours amiable devant la CRA (2 mois) puis Tribunal Administratif (2 mois).
               
            2. [RSA] Revenu de solidarité active.
               - Procédure : Recours amiable devant le Président du Conseil Départemental (2 mois) puis Tribunal Administratif (2 mois).
               
            3. [PPA] Prime d’activité.
               - Procédure : Recours amiable devant la CRA (2 mois) puis Tribunal Administratif (2 mois).
               
            4. [NOEL] Primes de Noël (Primes exceptionnelles de fin d’année).
               - Procédure : Recours amiable devant le Directeur de la Caf puis Tribunal Administratif.
               
            5. [AUUVVC] Aide universelle d’urgence aux victimes de violence conjugale.
               - Procédure : Recours amiable devant la CRA puis Tribunal Administratif.
               
            6. [AMENDE] Amende administrative pour fausse déclaration ou omission délibérée.
               - Context : Pénalité financière pour fraude.
               - Procédure : Tribunal Administratif direct (2 mois).
               
            7. [RECOUV] Recouvrement d’une créance assise et liquidée par une collectivité territoriale (ex: indu RSA du Département).
               - Context : Titre exécutoire, opposition à contrainte.
               - Procédure : Tribunal Administratif (2 mois) pour contester le bien-fondé.
               
            8. [ACADINASS] Suspension des allocations familiales pour inassiduité par l'inspecteur d'academie.
               - Context : Absentéisme scolaire sanctionné par l'académie.
               
            9. [CAFINASS] Suspension des allocations familiales pour inassiduité par la CAF.
               - Context : Suite à la décision académique.
               
            10. [MAJO] Majoration forfaitaire de 10% de l’indu pour réparation du préjudice.
                - Context : Pénalité sur indu frauduleux.
                - Procédure : Tribunal Judiciaire.
                
            11. [AAH] Allocation aux adultes handicapés.
                - Procédure : Recours amiable MDPH/CRA puis Tribunal Judiciaire.
                
            12. [AEEH] Allocation d’éducation de l’enfant handicapé.
                - Procédure : Recours amiable MDPH/CRA puis Tribunal Judiciaire.
                
            13. [AJPP] Allocation journalière de présence parentale.
                - Procédure : Recours amiable CMRA/CRA puis Tribunal Judiciaire.
                
            14. [AJPA] Allocation journalière du proche aidant.
                - Procédure : Recours amiable CRA puis Tribunal Judiciaire.
                
            15. [AVPF] Assurance vieillesse des parents au foyer.
                - Context : Cotisation retraite pour aidant familial/parent au foyer.
                - Procédure : Recours amiable MDPH/CRA puis Tribunal Judiciaire.
                
            16. [AUTRES] Autres prestations ou indéterminé.
                - Context : Allocations familiales, ARS, PAJE, ou "Dette CAF"/"Trop perçu" sans précision du type d'aide.
            """
        
        # Prepare file content context if available
        files_context = ""
        if files_content:
            files_context = "\n\n**Contenu des pièces jointes :**\n"
            for i, content in enumerate(files_content):
                # Truncate content to avoid token overflow? Let's limit to 2000 chars per file for safety
                files_context += f"[Document {i+1}]: {content[:3000]}...\n\n"

        prompt = f"""
        CONTEXTE :
        Tu es avocat spécialisé en droit administratif (CAF).
        Tu rédiges pour le compte de Maître Ilan BRUN-VARGAS.
        
        BASE DE CONNAISSANCES DU CABINET (Ce que nous traitons ou non) :
        {knowledge_base}
        
        DESCRIPTION DU CAS PAR LE CLIENT :
        "{description}"
        
        {files_context}
        
        TÂCHE :
        Analysez les documents et la description pour :
        1. Identifier l'étape précise de la procédure (stage).
        2. Identifier TOUTES les prestations concernées (RSA, APL, AAH, etc.). Il peut y en avoir plusieurs.
        
        RÈGLES DE CLASSIFICATION (STAGE) :
        1. Contradictory : Phase initiale (demande, contrôle, lettre d'information, invitation à observations, pas d'indu formel encore).
        2. RAPO : Recours Administratif Préalable Obligatoire. Notification d'indu, révision de droits, délai de 2 mois ouvert pour CRA/Président CD.
        3. Litigation : RAPO rejeté (explicite ou implicite), saisine Tribunal Administratif.
        
        RÈGLES D'ACCEPTATION :
        Regardez la colonne "Reference" dans la Base de Connaissances pour voir si nous traitons ce type de dossier.
        
        Retournez UNIQUEMENT le JSON suivant :
        {{
            "stage": "Contradictory" | "RAPO" | "Litigation",
            "prestations": [
                {{ "name": "CODE_PRESTATION", "isAccepted": true | false }}
            ]
        }}
        """
        
        try:
            response = await self.generate(prompt, temperature=0.1)
            
            # Clean response to ensure it's valid JSON
            import json
            import re
            
            # Find JSON block
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                json_str = match.group()
                result = json.loads(json_str)
                
                # Validate stage
                stage = result.get('stage', 'Contradictory')
                # Map back if LLM uses slightly different terms (though prompt says Contradictory/RAPO/Litigation)
                if stage.upper() == 'CONTROL': stage = 'Contradictory' # Handle User's screenshot term just in case
                
                if stage not in stages_list and stage != 'Contradictory':
                     # Fallback
                     if 'RAPO' in stage.upper(): stage = 'RAPO'
                     elif 'LITIGATION' in stage.upper() or 'TRIBUNAL' in stage.upper(): stage = 'Litigation'
                     else: stage = 'Contradictory'
                
                # Extract benefits list from the new object format
                raw_prestations = result.get('prestations', [])
                valid_benefits = []
                for p in raw_prestations:
                    # p is { "name": "RSA", "isAccepted": true }
                    name = p.get('name', '').upper()
                    if name in benefits_list:
                        valid_benefits.append(name)
                    # Handle "AUTRES" mapping if needed
                    elif "AUTRE" in name:
                        if "AUTRES" not in valid_benefits: valid_benefits.append("AUTRES")
                
                return {
                    "stage": stage,
                    "benefits": valid_benefits
                }
            else:
                print(f"[LLM Analysis] Could not parse JSON from response. Falling back to heuristics.")
                return self._heuristic_analysis(description)
                
        except Exception as e:
            print(f"[LLM Analysis] Error: {e}. Falling back to heuristics.")
            return self._heuristic_analysis(description)
                
        except Exception as e:
            print(f"[LLM Analysis] Error during analysis: {e}. Falling back to heuristics.")
            return self._heuristic_analysis(description)

    def _heuristic_analysis(self, description: str) -> Dict:
        """Fallback method using keywords if LLM fails."""
        desc_upper = description.upper()
        
        # 1. Detect Stage
        stage = "Contradictory" # Default
        if "TRIBUNAL" in desc_upper or "JUGEMENT" in desc_upper or "CONTENTIEUX" in desc_upper:
            stage = "Litigation"
        elif "CRA" in desc_upper or "RECOURS" in desc_upper or "COMMISSION" in desc_upper or "CONTESTATION" in desc_upper:
            stage = "RAPO"
            
        # 2. Detect Benefits
        benefits = []
        keywords = {
            "RSA": "RSA",
            "REVENU DE SOLIDARITE": "RSA",
            "APL": "APL",
            "ALS": "APL",
            "LOGEMENT": "APL",
            "PPA": "PPA",
            "PRIME D'ACTIVITE": "PPA",
            "AAH": "AAH",
            "HANDICAP": "AAH",
            "AEEH": "AEEH",
            "ENFANT": "AUTRES", # Generic
            "AJPP": "AJPP",
            "AJPA": "AJPA",
            "AVPF": "AVPF",
            "RETRAITE": "AVPF",
            "NOEL": "NOEL",
            "PRIME DE NOEL": "NOEL",
            "AMENDE": "AMENDE",
            "FRAUDE": "AMENDE",
            "INDU": "AUTRES",
            "DETTE": "AUTRES",
            "TROP PERCU": "AUTRES",
            "CAF": "AUTRES"
        }
        
        for key, code in keywords.items():
            if key in desc_upper:
                if code not in benefits:
                    benefits.append(code)
        
        # Deduplicate 'AUTRES' if we have specific ones? 
        # Actually logic says if we have specifics, we might still have AUTRES if vague terms are present.
        # But let's keep it simple.
        
        return {"stage": stage, "benefits": benefits}

# Global instance
llm_service = LLMService()

