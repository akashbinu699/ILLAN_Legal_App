# Documentation: Tagging Strategy for Benefits and Case Stages

This document outlines the logic used by the Legal Manager application to automatically tag cases with their **Social Benefits (Prestations)** and determine their **Legal Stage**.

## 1. Overview
When a new case is imported (via Gmail Sync), the system analyzes the case description (email body and subject) to extract key information.
This analysis is performed in two steps:
1.  **AI Analysis (Gemini):** The primary method uses a Large Language Model to understand context and nuance.
2.  **Heuristic Fallback:** If the AI is unavailable (e.g., API errors) or uncertain, a keyword-based fallback system ensures every case is still tagged correctly.

---

## 2. Benefit Tagging (Prestations)

The system identifies specific social benefits mentioned in the case. Tags are displayed as colored badges on the case card.

| Benefit Code | Label | Keywords / Context |
| :--- | :--- | :--- |
| **RSA** | Revenu de Solidarité Active | "RSA", "Revenu de solidarité", "Socle" |
| **APL** | Aide Personnalisée au Logement | "APL", "Logement", "AL", "Allocation logement" |
| **PPA** | Prime d'Activité | "PPA", "Prime d'activité" |
| **AAH** | Allocation Adulte Handicapé | "AAH", "Handicap", "MDPH" |
| **AEEH** | Alloc. Education Enfant Handicapé | "AEEH", "Enfant handicapé" |
| **AJPP** | Alloc. Journalière Présence Parentale | "AJPP", "Présence parentale" |
| **AJPA** | Alloc. Journalière Proche Aidant | "AJPA", "Proche aidant" |
| **AVPF** | Assurance Vieillesse Parents au Foyer | "AVPF", "Retraite", "Cotisation retraite" |
| **NOEL** | Prime de Noël | "Prime de Noël", "Noël" |
| **AMENDE** | Amende Administrative | "Amende", "Fraude", "Pénalité" |
| **AUTRES** | Autres / Indéterminé | "Dette", "Trop perçu", "Indu", "CAF" (without specific benefit), "Enfant", "ARS" |

**Rules:**
*   **Multiple Tags:** A simple case can have multiple tags (e.g., `RSA` + `APL` if both are mentioned).
*   **Default Tag:** If the email mentions "Dette CAF" or "Trop perçu" but does not specify *which* benefit, it defaults to **AUTRES**.

---

## 3. Case Stage Determination

The system classifies the procedural stage of the case.

### A. Litigation (Contentieux)
**Definition:** The case typically involves a court, a judgment, or a formal appeal against a decision already made.
*   **Keywords:**
    *   "TRIBUNAL"
    *   "JUGEMENT" (Judgment)
    *   "CONTENTIEUX"
    *   "APPEL" (Appeal against a judgment)

### B. RAPO (Recours Administratif Préalable Obligatoire)
**Definition:** The client is contesting an administrative decision (e.g., a debt notification) *before* going to court. This is the mandatory administrative appeal phase.
*   **Keywords:**
    *   "CRA" (Commission de Recours Amiable)
    *   "RECOURS" (Appeal/Recourse)
    *   "COMMISSION"
    *   "CONTESTATION"

### C. Contradictory (Phase Contradictoire)
**Definition:** The initial phase. The client has received a letter, a request for information, or a notification of debt, and is exchanging information with the administration (CAF, Department) to explain their situation *before* a formal contested decision is locked in.
*   **Default Behavior:** Any case that does not strictly match the keywords for *Litigation* or *RAPO* defaults to **Contradictory**.
*   **Context:**
    *   "Dette" (Debt)
    *   "Trop perçu" (Overpayment)
    *   "Explications" (Explanations)
    *   "Justificatifs" (Proof documents)

---

## 4. Technical Implementation Details

### Location
*   **Logic:** `backend/services/llm_service.py` -> `analyze_case_stage_and_benefits` and `_heuristic_analysis`.
*   **Frontend Mapping:** `frontend/src/services/api.ts` -> `mapStage`.

### Fallback Logic
The robustness of the system relies on the fallback:
1.  **Try AI:** "Read this email and determine Stage and Benefits."
2.  **Catch Error:** If AI fails (401, 404, Rate Limit), catch the exception.
3.  **Run Heuristics:** Scan the text for the keywords listed above.
    *   *Example:* Text contains "Tribunal" -> Stage = `Litigation`.
    *   *Example:* Text contains "Dette CAF" -> Benefit = `AUTRES`.
