export type CaseStage =
  | 'Contradictory'
  | 'RAPO'
  | 'Litigation';

export type MainView = 'LAWYER' | 'CLIENT' | 'SUCCESS';

export type ViewMode =
  | 'Case'
  | 'RAG query'
  | 'Email to client'
  | 'Pre Action Letter';

export interface FormErrors {
  email?: string;
  phone?: string;
  file?: string;
  consent?: string;
  [key: string]: string | undefined;
}

export interface AttachedFile {
  name: string;
  mimeType: string;
  base64: string;
}

export interface ClientSubmission {
  id: string;
  email: string;
  phone: string;
  description: string;
  files: AttachedFile[];
  submittedAt: Date;
  status: string;
  stage: string;
  prestations: any[];
  displayName?: string;
  generatedEmailDraft?: string;
  generatedAppealDraft?: string;
  emailPrompt?: string;
  appealPrompt?: string;
}

export type BenefitType =
  | 'APL' | 'RSA' | 'PPA' | 'NOEL' | 'AUUVVC' | 'AMENDE'
  | 'RECOUV' | 'ACADINASS' | 'CAFINASS' | 'MAJO' | 'AAH'
  | 'AEEH' | 'AJPP' | 'AJPA' | 'AVPF' | 'AUTRES';

export interface Document {
  id: string;
  name: string;
  size: string; // e.g. "1.2 MB"
  type: 'pdf' | 'image' | 'other';
  mime_type?: string;
}

export interface Case {
  id: string;
  caseNumber: string; // e.g. "Case1234"
  email: string;
  date: string; // "15 DEC 25"
  time: string; // "2.30pm"
  fullId: string; // "Case1234_email@example.com_DOC1234_15DEC25"
  badges: Array<{ label: string; color: 'red' | 'green' }>; // e.g. "8. ACADINASS"
  client: {
    name: string;
    street: string;
    city: string;
    phone: string;
    email: string;
  };
  benefitType: BenefitType;
  description: string;
  documents: Document[];
  isRead: boolean;
  statusTag: CaseStage; // e.g. "Contradictory" shown in list
}
