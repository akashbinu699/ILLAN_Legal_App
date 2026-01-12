import type { Case, CaseStage } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
    async getCases(): Promise<Case[]> {
        const response = await fetch(`${API_BASE_URL}/cases`);
        if (!response.ok) throw new Error('Failed to fetch cases');
        const data = await response.json();

        // Transform backend EmailGroupResponse[] -> Frontend Case[]
        // Backend returns list of groups, each group has 'cases' list.
        // We need to flatten this for the current frontend structure which expects a single list of cases?
        // Wait, the frontend App.tsx uses `mockCases` which is an array of `Case`.

        const allCases: Case[] = [];

        data.forEach((group: any) => {
            group.cases.forEach((c: any) => {
                // Map Backend CaseResponse to Frontend Case
                const submittedDate = new Date(c.submitted_at);

                allCases.push({
                    id: c.id,
                    caseNumber: c.case_id,
                    email: c.email,
                    date: submittedDate.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' }).toUpperCase(),
                    time: submittedDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }).toLowerCase(),
                    fullId: c.display_name || c.case_id,
                    badges: [], // Map prestations/benefits to badges
                    client: {
                        name: c.email.split('@')[0], // Placeholder name
                        street: 'Unknown',
                        city: 'Unknown',
                        phone: c.phone || '',
                        email: c.email
                    },
                    benefitType: 'AUTRES', // Default, logic to map prestations needed
                    description: c.description,
                    documents: [
                        {
                            id: 'doc1',
                            name: c.display_name ? c.display_name.split('_')[2] || 'Document' : 'Document',
                            size: 'Unknown',
                            type: 'pdf'
                        }
                    ],
                    isRead: c.status !== 'NEW',
                    statusTag: mapStage(c.stage)
                });
            });
        });

        return allCases;
    },

    async updateCaseStage(caseId: string, stage: CaseStage) {
        // caseId here is likely the Mongo ID since we mapped it to `id` above.
        // Backend expects `PATCH /case/{id}`.
        // Check backend: `update_case` searches by `case_id` (CAS_...) but fallbacks to Mongo ID. 
        // Ideally we send the ID we stored in `id`.

        // Map frontend stage to backend stage
        const backendStage = stage === 'Contradictory' ? 'CONTROL' : stage === 'Litigation' ? 'LITIGATION' : 'RAPO';

        const response = await fetch(`${API_BASE_URL}/case/${caseId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stage: backendStage })
        });
        return response.json();
    },

    async query(queryText: string, caseId?: string) {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: queryText, case_id: caseId })
        });
        if (!response.ok) throw new Error('Query failed');
        return response.json();
    },

    async submitCase(data: { email: string; phone: string; description: string; files: any[] }) {
        const response = await fetch(`${API_BASE_URL}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Submission failed');
        }
        return response.json();
    },

    async syncGmail(caseId: string) {
        const response = await fetch(`${API_BASE_URL}/sync-gmail-case/${caseId}`, {
            method: 'POST',
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Sync failed');
        }
        return response.json();
    }
};

function mapStage(backendStage: string): CaseStage {
    if (backendStage === 'CONTROL') return 'Contradictory';
    if (backendStage === 'LITIGATION') return 'Litigation';
    return 'RAPO';
}
