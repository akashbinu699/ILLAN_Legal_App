"""Draft generation service using Google Gemini API."""
import os
import base64
from typing import List, Dict, Optional, Tuple
from backend.config import settings

# Knowledge base - same as frontend
KNOWLEDGE_BASE = """THEME,RENSEIGNEMENTS
"Recours dont traite le cabinet (✅), et recours dont il ne traite pas (❌) (Généralités)","Notre cabinet pratique en droit public et ne connait que des recours et contentieux administratifs. Nous ne traitons pas des affaires qui relèvent du tribunal judiciaire. Par ailleurs, nous ne traitons pas non plus des prestations relatives au handicap, ou celles ne relevant pas du tribunal administratif (AAH, AEEH, AJPP, AJPA, AVPF, etc.)."
"""

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Draft generation will not work.")

class DraftGenerationService:
    """Service for generating email and appeal drafts using Gemini API."""
    
    def __init__(self):
        if not settings.gemini_api_key:
            print("Warning: GEMINI_API_KEY not set. Draft generation will not work.")
            self.client = None
        elif GEMINI_AVAILABLE:
            genai.configure(api_key=settings.gemini_api_key)
            self.client = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.client = None
    
    def _file_to_part(self, file_data: Dict) -> Dict:
        """Convert file data to Gemini part format."""
        return {
            "inline_data": {
                "mime_type": file_data.get("mimeType", "application/pdf"),
                "data": file_data.get("base64", "")
            }
        }
    
    async def detect_case_stage(
        self, 
        description: str, 
        files: List[Dict]
    ) -> Tuple[str, List[Dict]]:
        """
        Detect legal stage and prestations.
        Returns: (stage, prestations)
        """
        if not self.client:
            return ("RAPO", [{"name": "Non identifiée", "isAccepted": True}])
        
        parts = []
        
        # Add files
        for file in files:
            parts.append(self._file_to_part(file))
        
        if files:
            parts.append({"text": "Documents fournis par le client ci-dessus."})
        
        prompt = f"""
CONTEXTE:
Tu es avocat spécialisé en droit administratif (CAF). 
Tu rédiges pour le compte de Maître Ilan BRUN-VARGAS.

RÉFÉRENCE JURIDIQUE INTERNE (BASE DE CONNAISSANCES):
{KNOWLEDGE_BASE}

TÂCHE:
Analyse la description et les documents fournis pour déterminer:
1. La phase juridique: CONTROL (Contrôle/Procédure contradictoire), RAPO (Recours Administratif Préalable Obligatoire), ou LITIGATION (Recours Contentieux/Tribunal)
2. Les prestations concernées (RSA, APL, Prime d'activité, etc.) et si elles sont acceptées par le cabinet

DESCRIPTION CLIENT: "{description}"

Réponds UNIQUEMENT avec un JSON valide au format suivant:
{{
    "stage": "CONTROL" | "RAPO" | "LITIGATION",
    "prestations": [
        {{"name": "RSA", "isAccepted": true}},
        {{"name": "APL", "isAccepted": true}}
    ]
}}
"""
        parts.append({"text": prompt})
        
        try:
            response = self.client.generate_content(parts)
            import json
            # Extract JSON from response
            text = response.text.strip()
            # Remove markdown code blocks if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            
            result = json.loads(text)
            stage = result.get("stage", "RAPO")
            prestations = result.get("prestations", [{"name": "Non identifiée", "isAccepted": True}])
            return (stage, prestations)
        except Exception as e:
            print(f"Error detecting case stage: {e}")
            return ("RAPO", [{"name": "Non identifiée", "isAccepted": True}])
    
    def _get_prompt_templates(self, stage: str, client_name: str, description: str) -> Tuple[str, str]:
        """Get prompt templates for email and appeal based on stage."""
        context_header = f"""
CONTEXTE:
Tu es avocat spécialisé en droit administratif (CAF). 
Tu rédiges pour le compte de Maître Ilan BRUN-VARGAS.
Écris à la première personne comme si c'était moi, sous forme de paragraphes clairs, évite le jargon, pas plus d'un niveau de bullet-points.

RÉFÉRENCE JURIDIQUE INTERNE (BASE DE CONNAISSANCES):
{KNOWLEDGE_BASE}
Utilise cette base pour citer les bons articles de loi et vérifier les délais/procédures applicables.

STYLE & FORMATTAGE (IMPÉRATIF):
- Format APA Strict : Police standard, double interligne.
- AUCUN MARKDOWN (Pas de gras **, pas de titres ##, pas d'italique).
- TEXTE BRUT uniquement.
- TITRES DE SECTIONS EN MAJUSCULES (ex: OBJET, FAITS, DISCUSSION).
- Ton : structuré, clair, concis, engageant, et accessible pour le grand public.

DESCRIPTION CLIENT: "{description}"
NOM CLIENT: {client_name or "[Nom du Client]"}
"""
        
        # Email prompts
        if stage == "CONTROL":
            email_prompt = f"""
{context_header}

TÂCHE : Rédige un email au client couvrant ces points (à la 1ère personne) :
1. ACCUSÉ DE RÉCEPTION.
2. RAPPEL DE LA SITUATION TELLE QUE JE LA COMPRENDS : Contrôle CAF effectué, réception courrier "procédure contradictoire", incohérences/constatations soulevées.
3. RECOURS : Expliquer qu'il y a un délai de 10 jours pour les observations un fois le courrier "procédure contradictoire" reçu. Prochaine étape = décision de la Caf sur les constatations et éventuelles observations (indu).
4. PROCHAINE ÉTAPE : Inviter le client à recontacter dès réception de la décision de la Caf pour renseigner sur possiblités de contestation.
Salutations distinguées.
"""
        elif stage == "RAPO":
            email_prompt = f"""
{context_header}

TÂCHE : Rédige un email au client couvrant ces points (à la 1ère personne) :
1. ACCUSÉ DE RÉCEPTION et récapitulatif des sommes réclamées.
2. OBSERVATIONS SUR LE BIEN-FONDÉ : Identifier pourquoi la CAF réclame (séjour, ressources), et les eventuelles réponses/arguments factuels fournis par le client.
3. VOIES DE RECOURS : Expliquer les destinataires différents pour les prestations concernées (Président CD pour RSA, Directeur CAF pour APL, CRA pour Prime d'activité). Délai en principe de 2 mois. Expliquer l'envoi en LRAR.
4. REMISE DE DETTE : Possible en parallèle, indépendant du bien-fondé. Repose uniquement sur situation financière et bonne foi (indisponible si l'administration retient la fraude, il faut alors la contester au préalable devant le tribunal administratif).
5. PROPOSITION D'ACCOMPAGNEMENT : Peut l'accompagner et rédiger RAPO(s) pour le client. Honoraires peuvent être pris en charge par assurance protection juridique (généralement incluse avec leur assurance habitation), ou peut prendre les honoraires à leure charge. L'aide juridictionnelle n'est pas dispobile pour cette étape du recours. Alternativement, je pourrai lui proposer gratuitement un modèle de recours duquel partir.
6. ACTION : Inviter à indiquer ce que souhaite faire (accompagnement ou pas) et que peut joindre les Conditions Générales/Contrat de son assurance afin que renseigne sur couvert ou non pour ce type de litiges.
Salutations distinguées.
"""
        else:  # LITIGATION
            email_prompt = f"""
{context_header}

TÂCHE : Rédige un email au client pour la phase contentieuse (à la 1ère personne) :
1. ACCUSÉ DE RÉCEPTION. Le RAPO a été rejeté (ou silence gardé).
2. SAISINE DU TRIBUNAL ADMINISTRATIF : C'est la prochaine étape. Délai de 2 mois.
3. PROCÉDURE : Essentiellement écrite, via Télérecours Citoyens.
4. PROPOSITION D'ACCOMPAGNEMENT. Financement des honoraires. Devant le tribunal administratif, la procédure est essentiellement écrite, et vous pouvez déposer votre recours vous-même via la plateforme en ligne Télérecours Citoyens. Un avocat n'est pas obligatoire, mais si vous le souhaitez, je peux prendre votre dossier. Il existe plusieurs solutions pour le financement : • Prendre les honoraires à votre charge personnelle. • Demander l'aide juridictionnelle si vos ressources sont modestes (vous devez préparer le dossier et le déposer au bureau d'aide juridictionnelle). • Utiliser votre assurance habitation (qui comporte une clause de protection juridique). C'est souvent la voie préférée et la plus rapide. Vous pouvez m'envoyer une copie de votre contrat d'assurance habitation pour que je vous confirme les garanties et contacte l'assureur si nécessaire.
5. DEMANDE DE CONFIRMATION du souhait de poursuivre ensemble ou non le contentieux. Peut me fournir les Conditions Générales/Contrat de son assurance afin que renseigne sur couvert ou non pour ce type de litiges.
Salutations distinguées.
"""
        
        # Appeal prompts (simplified - full version would match frontend)
        if stage == "CONTROL":
            appeal_prompt = f"""
{context_header}
TÂCHE : Rédige une note succincte de "OBSERVATIONS SUITE À PROCÉDURE CONTRADICTOIRE". Redige comme si c'etait le client, sans jargon juridique et sans mots inutiles/tournures lourdes. En language "FALC", facile a lire et a comprendre.
Structure :
- EN-TÊTE (Client)
- OBJET : OBSERVATIONS SUITE AU CONTRÔLE N°[Numéro]
- FAITS : Chronologie simple.
- RÉPONSE AUX CONSTATATIONS : Argumentation factuelle contre les incohérences (résidence, isolement, ressources, etc.).
- CONCLUSION : Demande d'abandon des constatations et de la procédure de rectification.
"""
        elif stage == "RAPO":
            appeal_prompt = f"""
{context_header}
TÂCHE : Rédige un "RECOURS ADMINISTRATIF PRÉALABLE OBLIGATOIRE" (RAPO).
Destinataire : Président de la Commission de Recours Amiable (ou Président Conseil Départemental) selon la prestation identifiée dans la Base de Connaissances.

Structure du courrier:
- EN-TÊTE avec coordonnées client
- OBJET : Recours administratif contre un indu
- 1. Demande d'annulation (argumentation factuelle)
- 2. Demande de remise de dette (subsidiaire)
- 3. Demande de transmission du rapport de contrôle
- 4. Suspension du recouvrement
- CONCLUSION avec salutations
"""
        else:  # LITIGATION
            appeal_prompt = f"""
{context_header}
TÂCHE : Rédige un projet de "Requête Introductive d'Instance" devant le Tribunal Administratif.

Structure:
- I. FAITS ET PROCÉDURE (chronologie)
- II. RECEVABILITÉ
- III. DISCUSSION
  - A. Sur la régularité externe
  - B. Sur le bien-fondé de l'indu
  - C. Sur la remise gracieuse (subsidiaire)
- IV. CONCLUSIONS (dispositif)
"""
        
        return (email_prompt.strip(), appeal_prompt.strip())
    
    async def generate_single_draft(
        self, 
        prompt: str, 
        files: List[Dict]
    ) -> str:
        """Generate a single draft (email or appeal) using the prompt."""
        if not self.client:
            return "Draft generation not available. Please configure GEMINI_API_KEY."
        
        parts = []
        
        # Add files
        for file in files:
            parts.append(self._file_to_part(file))
        
        if files:
            parts.append({"text": "RÉFÉRENCE : Documents du dossier (à utiliser pour extraire dates, montants, motifs, etc)."})
        
        # Add prompt
        parts.append({"text": prompt})
        
        try:
            response = self.client.generate_content(parts)
            return response.text or ""
        except Exception as e:
            print(f"Error generating draft: {e}")
            return f"Erreur lors de la génération: {str(e)}"
    
    async def generate_drafts(
        self,
        description: str,
        files: List[Dict],
        client_name: str = "Client"
    ) -> Dict:
        """
        Complete draft generation pipeline.
        Returns: {
            'stage': str,
            'prestations': List[Dict],
            'email_prompt': str,
            'appeal_prompt': str,
            'email_draft': str,
            'appeal_draft': str
        }
        """
        # Step 1: Detect stage and prestations
        stage, prestations = await self.detect_case_stage(description, files)
        
        # Step 2: Get prompts
        email_prompt, appeal_prompt = self._get_prompt_templates(stage, client_name, description)
        
        # Step 3: Generate drafts in parallel (simulated with sequential for now)
        email_draft = await self.generate_single_draft(email_prompt, files)
        appeal_draft = await self.generate_single_draft(appeal_prompt, files)
        
        return {
            'stage': stage,
            'prestations': prestations,
            'email_prompt': email_prompt,
            'appeal_prompt': appeal_prompt,
            'email_draft': email_draft,
            'appeal_draft': appeal_draft
        }

# Global instance
draft_generation_service = DraftGenerationService()

