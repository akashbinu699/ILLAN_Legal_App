export type CaseStatus = 'NEW' | 'PROCESSING' | 'REVIEWED' | 'SENT';
export const CaseStatus = {
    NEW: 'NEW' as const,
    PROCESSING: 'PROCESSING' as const,
    REVIEWED: 'REVIEWED' as const,
    SENT: 'SENT' as const
};

export type LegalStage = 'CONTROL' | 'RAPO' | 'LITIGATION';
export const LegalStage = {
    CONTROL: 'CONTROL' as const, // Contrôle / Procédure contradictoire
    RAPO: 'RAPO' as const,       // Recours Administratif Préalable Obligatoire
    LITIGATION: 'LITIGATION' as const // Recours Contentieux (Tribunal)
};

export interface AttachedFile {
    name: string;
    mimeType: string;
    base64: string;
}

export interface Prestation {
    name: string;
    isAccepted: boolean;
}

export interface ClientSubmission {
    id: string; // Sequentially formatted, e.g., CAS-2025-001
    email: string;
    phone: string;
    description: string;

    // Multiple files support
    files: AttachedFile[];

    submittedAt: Date;
    status: CaseStatus;

    // The detected or selected stage of the case
    stage: LegalStage;

    // List of detected prestations and their acceptance status
    prestations: Prestation[];

    // Display name for the form (format: (form_number)_DDMMMYY)
    displayName?: string;

    // The generated drafts
    generatedEmailDraft?: string;
    generatedAppealDraft?: string;

    // The prompts used to generate the drafts (editable)
    emailPrompt?: string;
    appealPrompt?: string;
}

export interface FormErrors {
    email?: string;
    phone?: string;
    file?: string;
    consent?: string;
}