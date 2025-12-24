/**
 * API client for backend communication.
 * Replaces direct Gemini API calls with backend API calls.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

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
    email: string;
    phone: string;
    description: string;
    submitted_at: string;
    status: string;
    stage: string;
    prestations: Array<{ name: string; isAccepted: boolean }>;
    generatedEmailDraft?: string;
    generatedAppealDraft?: string;
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
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    async submitCase(submission: ApiSubmission): Promise<ApiCase> {
        return this.request<ApiCase>('/submit', {
            method: 'POST',
            body: JSON.stringify(submission),
        });
    }

    async getCases(): Promise<ApiCase[]> {
        return this.request<ApiCase[]>('/cases');
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
}

export const apiClient = new ApiClient();

