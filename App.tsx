import React, { useState, useEffect } from 'react';
import { ClientForm } from './components/ClientForm';
import { LawyerDashboard } from './components/LawyerDashboard';
import { ClientSubmission, CaseStatus, LegalStage } from './types';
import { detectCaseStage, getPromptTemplates, generateSingleDraft } from './services/geminiService';
import { apiClient } from './services/apiClient';

enum View {
    CLIENT = 'CLIENT',
    LAWYER = 'LAWYER',
    SUCCESS = 'SUCCESS'
}

export default function App() {
    const [currentView, setCurrentView] = useState<View>(View.CLIENT);
    const [cases, setCases] = useState<ClientSubmission[]>([]);
    const [useBackend, setUseBackend] = useState<boolean>(true); // Toggle for backend vs direct Gemini
    
    // Load cases from backend on mount
    useEffect(() => {
        if (useBackend) {
            loadCasesFromBackend();
        }
    }, [useBackend]);
    
    const loadCasesFromBackend = async () => {
        try {
            const apiCases = await apiClient.getCases();
            // Convert API cases to ClientSubmission format
            const convertedCases: ClientSubmission[] = apiCases.map(apiCase => ({
                id: apiCase.case_id,
                email: apiCase.email,
                phone: apiCase.phone,
                description: apiCase.description,
                files: [], // Files not included in API response
                submittedAt: new Date(apiCase.submitted_at),
                status: apiCase.status as CaseStatus,
                stage: apiCase.stage as LegalStage,
                prestations: apiCase.prestations || [],
                generatedEmailDraft: apiCase.generatedEmailDraft,
                generatedAppealDraft: apiCase.generatedAppealDraft
            }));
            setCases(convertedCases);
        } catch (error) {
            console.error("Failed to load cases from backend:", error);
            // Fallback to empty array
        }
    };

    const generateCaseId = (index: number) => {
        const year = new Date().getFullYear();
        // Generates CAS-2025-001, CAS-2025-002, etc.
        const sequence = (index + 1).toString().padStart(3, '0');
        return `CAS-${year}-${sequence}`;
    };

    const handleClientSubmit = async (data: Omit<ClientSubmission, 'id' | 'status' | 'submittedAt' | 'stage' | 'prestations' | 'generatedEmailDraft' | 'generatedAppealDraft'>) => {
        if (useBackend) {
            // Use backend API
            try {
                const response = await apiClient.submitCase({
                    email: data.email,
                    phone: data.phone,
                    description: data.description,
                    files: data.files.map(f => ({
                        name: f.name,
                        mimeType: f.mimeType,
                        base64: f.base64
                    }))
                });
                
                // Convert to ClientSubmission format
                const newCase: ClientSubmission = {
                    id: response.case_id,
                    email: response.email,
                    phone: response.phone,
                    description: response.description,
                    files: data.files,
                    submittedAt: new Date(response.submitted_at),
                    status: response.status as CaseStatus,
                    stage: response.stage as LegalStage,
                    prestations: response.prestations || [],
                    generatedEmailDraft: response.generatedEmailDraft,
                    generatedAppealDraft: response.generatedAppealDraft
                };
                
                setCases(prev => [newCase, ...prev]);
                setCurrentView(View.SUCCESS);
                
                // Reload cases after a delay to get updated status
                setTimeout(() => loadCasesFromBackend(), 2000);
            } catch (error) {
                console.error("Backend submission failed:", error);
                alert("Erreur lors de l'envoi. Vérifiez que le backend est démarré.");
            }
        } else {
            // Original direct Gemini API flow
            const newId = generateCaseId(cases.length);
            
            const newCase: ClientSubmission = {
                id: newId,
                submittedAt: new Date(),
                status: CaseStatus.NEW,
                stage: LegalStage.RAPO,
                prestations: [],
                ...data
            };

            setCases(prev => [newCase, ...prev]);
            setCurrentView(View.SUCCESS);

            try {
                const analysisResult = await detectCaseStage(newCase.description, newCase.files);
                
                setCases(prev => prev.map(c => c.id === newCase.id ? { 
                    ...c, 
                    stage: analysisResult.stage,
                    prestations: analysisResult.prestations
                } : c));

                const { emailPrompt, appealPrompt } = getPromptTemplates(analysisResult.stage, "Client", newCase.description);
                
                setCases(prev => prev.map(c => c.id === newCase.id ? { ...c, emailPrompt, appealPrompt } : c));

                const [emailDraft, appealDraft] = await Promise.all([
                    generateSingleDraft(emailPrompt, newCase.files),
                    generateSingleDraft(appealPrompt, newCase.files)
                ]);

                setCases(prev => prev.map(c => {
                    if (c.id === newCase.id) {
                        return {
                            ...c,
                            generatedEmailDraft: emailDraft,
                            generatedAppealDraft: appealDraft,
                            status: CaseStatus.PROCESSING
                        };
                    }
                    return c;
                }));

            } catch (error) {
                console.error("AI Pipeline failed", error);
            }
        }
    };

    const handleUpdateCase = (id: string, updates: Partial<ClientSubmission>) => {
        setCases(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
    };

    const handleRegenerateDraft = async (id: string, type: 'email' | 'appeal', customPrompt: string) => {
        const currentCase = cases.find(c => c.id === id);
        if (!currentCase) return;

        // Save the custom prompt first
        const promptKey = type === 'email' ? 'emailPrompt' : 'appealPrompt';
        handleUpdateCase(id, { [promptKey]: customPrompt });

        try {
            const content = await generateSingleDraft(customPrompt, currentCase.files);
            
            if (type === 'email') {
                handleUpdateCase(id, { generatedEmailDraft: content });
            } else {
                handleUpdateCase(id, { generatedAppealDraft: content });
            }
        } catch (error) {
            console.error("Regeneration failed", error);
            alert("Erreur lors de la régénération.");
        }
    };

    const handleStageChange = async (id: string, newStage: LegalStage) => {
        const currentCase = cases.find(c => c.id === id);
        if (!currentCase) return;

        // 1. Get New Prompts for this stage
        const { emailPrompt, appealPrompt } = getPromptTemplates(newStage, "Client", currentCase.description);

        // 2. Update Stage AND Prompts AND Clear Drafts immediately
        // This visual clear ensures the user sees something is happening
        handleUpdateCase(id, { 
            stage: newStage,
            emailPrompt, 
            appealPrompt,
            generatedEmailDraft: "♻️ Changement de phase... Régénération de l'email...",
            generatedAppealDraft: "♻️ Changement de phase... Régénération du recours..."
        });

        // 3. Regenerate drafts with new prompts
        try {
            const [emailDraft, appealDraft] = await Promise.all([
                generateSingleDraft(emailPrompt, currentCase.files),
                generateSingleDraft(appealPrompt, currentCase.files)
            ]);

            handleUpdateCase(id, { 
                generatedEmailDraft: emailDraft, 
                generatedAppealDraft: appealDraft 
            });
        } catch (e) {
            console.error("Failed to regenerate after stage change", e);
            handleUpdateCase(id, { 
                generatedEmailDraft: "Erreur lors de la régénération.", 
                generatedAppealDraft: "Erreur lors de la régénération."
            });
        }
    };

    return (
        <div className="min-h-screen flex flex-col font-sans">
            <nav className="bg-brand-dark text-white p-4 shadow-md flex justify-between items-center z-10 relative">
                <div className="flex items-center space-x-3">
                     <div className="w-8 h-8 bg-brand-red rounded-sm flex items-center justify-center">
                        <i className="fas fa-balance-scale-left text-white text-sm"></i>
                     </div>
                     <span className="font-semibold text-lg tracking-tight">LegalEase <span className="text-gray-400 font-light">CAF Manager</span></span>
                </div>
                <div className="space-x-4 text-sm">
                    <button 
                        onClick={() => setCurrentView(View.CLIENT)}
                        className={`px-3 py-1 rounded transition-colors ${currentView === View.CLIENT || currentView === View.SUCCESS ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        Vue Client
                    </button>
                    <button 
                        onClick={() => setCurrentView(View.LAWYER)}
                        className={`px-3 py-1 rounded transition-colors ${currentView === View.LAWYER ? 'bg-brand-red text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        Espace Avocat ({cases.filter(c => c.status === CaseStatus.NEW).length})
                    </button>
                </div>
            </nav>

            <main className="flex-1 bg-white">
                {currentView === View.CLIENT && (
                    <div className="bg-gray-100 min-h-full py-8">
                        <div className="text-center mb-8">
                            <h1 className="text-3xl font-light text-brand-dark mb-2">Contestez votre décision CAF</h1>
                            <p className="text-gray-500">Remplissez ce formulaire pour une analyse gratuite de votre dossier.</p>
                        </div>
                        <ClientForm onSubmit={handleClientSubmit} />
                    </div>
                )}

                {currentView === View.SUCCESS && (
                    <div className="flex flex-col items-center justify-center h-full min-h-[60vh] text-center p-8 animate-fade-in-up">
                        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
                            <i className="fas fa-check text-4xl text-green-500"></i>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-800 mb-2">Dossier reçu avec succès</h2>
                        <p className="text-gray-600 max-w-md mb-8">
                            Merci. Notre équipe d'avocats analyse actuellement vos pièces jointes et votre description. Vous recevrez une réponse sous 24h.
                        </p>
                        <button 
                            onClick={() => setCurrentView(View.LAWYER)}
                            className="bg-brand-dark hover:bg-black text-white px-6 py-3 rounded shadow transition-transform transform hover:-translate-y-1"
                        >
                            Accéder à l'Espace Avocat
                        </button>
                    </div>
                )}

                {currentView === View.LAWYER && (
                    <LawyerDashboard 
                        cases={cases} 
                        onUpdateCase={handleUpdateCase}
                        onRegenerateDraft={handleRegenerateDraft}
                        onStageChange={handleStageChange}
                    />
                )}
            </main>
        </div>
    );
}