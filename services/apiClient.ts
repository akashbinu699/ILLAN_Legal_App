/**
 * API client for backend communication.
 * Replaces direct Gemini API calls with backend API calls.
 */
// Auto-detect backend URL based on current hostname
const getBackendUrl = () => {
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }
    // Use current hostname (works for both localhost and network IP)
    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    return `http://${hostname}:8000/api`;
};

const API_BASE_URL = getBackendUrl();

export interface ApiSubmission {
    email: string;
    phone: string;
    description: string;
    files: Array<{
        name: string;
        mimeType: string;
        base64: string;
    }>;
}

export interface ApiCase {
    id: number;
    case_id: string;
    cas_number?: number;
    email: string;
    phone: string;
    description: string;
    submitted_at: string;
    status: string;
    stage: string;
    prestations: Array<{ name: string; isAccepted: boolean }>;
    display_name?: string;  // Format: (form_number)_DDMMMYY
    generatedEmailDraft?: string;
    generatedAppealDraft?: string;
    emailPrompt?: string;
    appealPrompt?: string;
}

export interface EmailGroup {
    email: string;
    cas_number?: number;
    cas_display_name?: string;  // Format: CAS-{number}_{email}
    cases: ApiCase[];
}

export interface CaseUpdate {
    generatedEmailDraft?: string;
    generatedAppealDraft?: string;
    emailPrompt?: string;
    appealPrompt?: string;
    stage?: string;
    status?: string;
}

export interface QueryHistory {
    id: number;
    query_text: string;
    response_text: string;
    citations: Array<{
        document_id: number;
        page_number: number;
        section_title?: string;
        clause_number?: string;
        chunk_id: number;
    }>;
    retrieved_chunk_ids?: any[];
    created_at: string;
}

export interface ApiQuery {
    query: string;
    case_id?: string;
}

export interface ApiQueryResponse {
    response: string;
    citations: Array<{
        document_id: number;
        page_number: number;
        section_title?: string;
        clause_number?: string;
        chunk_id: number;
    }>;
    retrieved_chunks: number;
    query_id: number;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;
                try {
                    const error = await response.json();
                    // Handle different error response formats
                    if (typeof error === 'string') {
                        errorMessage = error;
                    } else if (error.detail) {
                        // FastAPI validation errors can be a list or a string
                        if (Array.isArray(error.detail)) {
                            errorMessage = error.detail.map((e: any) => {
                                if (typeof e === 'string') return e;
                                if (e.msg) return `${e.loc?.join('.') || ''}: ${e.msg}`;
                                return JSON.stringify(e);
                            }).join(', ');
                        } else {
                            errorMessage = String(error.detail);
                        }
                    } else if (error.message) {
                        errorMessage = String(error.message);
                    } else {
                        errorMessage = JSON.stringify(error);
                    }
                } catch (parseError) {
                    errorMessage = response.statusText || `HTTP ${response.status} error`;
                }
                throw new Error(errorMessage);
            }

            return response.json();
        } catch (error) {
            // Handle network errors (backend not running, CORS, etc.)
            if (error instanceof TypeError) {
                // Check for specific fetch-related errors
                const errorMsg = error.message.toLowerCase();
                if (errorMsg.includes('fetch') || errorMsg.includes('network') || errorMsg.includes('failed')) {
                    throw new Error(`Cannot connect to backend at ${url}. Make sure the backend server is running on port 8000.`);
                }
            }
            // Re-throw other errors as-is
            throw error;
        }
    }

    async submitCase(submission: ApiSubmission): Promise<ApiCase> {
        return this.request<ApiCase>('/submit', {
            method: 'POST',
            body: JSON.stringify(submission),
        });
    }

    async getCases(): Promise<EmailGroup[]> {
        return this.request<EmailGroup[]>('/cases');
    }

    async getCase(caseId: string): Promise<ApiCase> {
        return this.request<ApiCase>(`/case/${caseId}`);
    }

    async queryRAG(query: ApiQuery): Promise<ApiQueryResponse> {
        return this.request<ApiQueryResponse>('/query', {
            method: 'POST',
            body: JSON.stringify(query),
        });
    }

    async updateCase(caseId: string, update: CaseUpdate): Promise<ApiCase> {
        return this.request<ApiCase>(`/case/${caseId}`, {
            method: 'PATCH',
            body: JSON.stringify(update),
        });
    }

    async generateDrafts(caseId: string): Promise<ApiCase> {
        return this.request<ApiCase>(`/case/${caseId}/generate-drafts`, {
            method: 'POST',
        });
    }

    async getCaseQueries(caseId: string): Promise<QueryHistory[]> {
        return this.request<QueryHistory[]>(`/case/${caseId}/queries`);
    }

    async generateDraft(caseId: string, prompt: string, draftType: 'email' | 'appeal'): Promise<{ draft: string; prompt: string }> {
        return this.request<{ draft: string; prompt: string }>(`/case/${caseId}/generate-draft`, {
            method: 'POST',
            body: JSON.stringify({
                prompt: prompt,
                draft_type: draftType
            }),
        });
    }

    async detectStage(description: string, files: Array<{ name: string; mimeType: string; base64: string }> = []): Promise<{ stage: string; prestations: Array<{ name: string; isAccepted: boolean }> }> {
        return this.request<{ stage: string; prestations: Array<{ name: string; isAccepted: boolean }> }>('/detect-stage', {
            method: 'POST',
            body: JSON.stringify({
                description: description,
                files: files
            }),
        });
    }
}

export const apiClient = new ApiClient();

