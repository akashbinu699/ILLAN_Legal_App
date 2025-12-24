import React, { useState, useEffect, useRef } from 'react';
import { ClientSubmission, CaseStatus, LegalStage } from '../types';
import { QueryInterface } from './QueryInterface';
import { apiClient } from '../services/apiClient';

interface LawyerDashboardProps {
    cases: ClientSubmission[];
    onUpdateCase: (id: string, updates: Partial<ClientSubmission>) => void;
    onRegenerateDraft: (id: string, type: 'email' | 'appeal', customPrompt: string) => Promise<void>;
    onStageChange: (id: string, newStage: LegalStage) => Promise<void>;
}

export const LawyerDashboard: React.FC<LawyerDashboardProps> = ({ cases, onUpdateCase, onRegenerateDraft, onStageChange }) => {
    const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'details' | 'email' | 'appeal' | 'query'>('email');
    const [regenerating, setRegenerating] = useState<'email' | 'appeal' | null>(null);
    const [showPrompt, setShowPrompt] = useState(true);
    
    // Local editing state
    const [emailContent, setEmailContent] = useState('');
    const [appealContent, setAppealContent] = useState('');
    
    // Local prompt editing state
    const [currentEmailPrompt, setCurrentEmailPrompt] = useState('');
    const [currentAppealPrompt, setCurrentAppealPrompt] = useState('');

    const selectedCase = cases.find(c => c.id === selectedCaseId);
    const [loadingCase, setLoadingCase] = useState(false);

    // Refs to track previous values to avoid overwriting user work with same props
    const prevEmailRef = useRef<string | undefined>(undefined);
    const prevAppealRef = useRef<string | undefined>(undefined);
    
    // Debounce timers for auto-save
    const emailSaveTimer = useRef<NodeJS.Timeout | null>(null);
    const appealSaveTimer = useRef<NodeJS.Timeout | null>(null);
    const emailPromptSaveTimer = useRef<NodeJS.Timeout | null>(null);
    const appealPromptSaveTimer = useRef<NodeJS.Timeout | null>(null);

    // Load case from backend when selected
    useEffect(() => {
        if (selectedCaseId) {
            loadCaseFromBackend(selectedCaseId);
        }
    }, [selectedCaseId]);

    // Sync state when case changes or when AI updates the draft
    useEffect(() => {
        if (selectedCase) {
            // Only update local state if the prop changed from outside (e.g. AI finished, or switched case)
            // We ignore updates if they match what we just saved (to prevent loop)
            
            // For Email
            if (selectedCase.generatedEmailDraft !== prevEmailRef.current) {
                setEmailContent(selectedCase.generatedEmailDraft || '');
                prevEmailRef.current = selectedCase.generatedEmailDraft;
            }

            // For Appeal
            if (selectedCase.generatedAppealDraft !== prevAppealRef.current) {
                setAppealContent(selectedCase.generatedAppealDraft || '');
                prevAppealRef.current = selectedCase.generatedAppealDraft;
            }

            // Prompts can just sync directly as they aren't edited as aggressively
            if (selectedCase.emailPrompt !== currentEmailPrompt && selectedCase.emailPrompt) {
                setCurrentEmailPrompt(selectedCase.emailPrompt);
            }
            if (selectedCase.appealPrompt !== currentAppealPrompt && selectedCase.appealPrompt) {
                setCurrentAppealPrompt(selectedCase.appealPrompt);
            }
        }
    }, [selectedCase, selectedCase?.generatedEmailDraft, selectedCase?.generatedAppealDraft, selectedCase?.emailPrompt, selectedCase?.appealPrompt]);

    const loadCaseFromBackend = async (caseId: string) => {
        setLoadingCase(true);
        try {
            const apiCase = await apiClient.getCase(caseId);
            
            // Check if drafts need to be generated
            if (!apiCase.generatedEmailDraft || !apiCase.generatedAppealDraft) {
                // Generate drafts if missing
                try {
                    const updatedCase = await apiClient.generateDrafts(caseId);
                    // Update local state with generated drafts
                    onUpdateCase(caseId, {
                        generatedEmailDraft: updatedCase.generatedEmailDraft,
                        generatedAppealDraft: updatedCase.generatedAppealDraft,
                        emailPrompt: updatedCase.emailPrompt,
                        appealPrompt: updatedCase.appealPrompt
                    });
                } catch (error) {
                    console.error("Failed to generate drafts:", error);
                }
            } else {
                // Update local state with loaded data
                onUpdateCase(caseId, {
                    generatedEmailDraft: apiCase.generatedEmailDraft,
                    generatedAppealDraft: apiCase.generatedAppealDraft,
                    emailPrompt: apiCase.emailPrompt,
                    appealPrompt: apiCase.appealPrompt
                });
            }
        } catch (error) {
            console.error("Failed to load case from backend:", error);
        } finally {
            setLoadingCase(false);
        }
    };

    const handleContentChange = (type: 'email' | 'appeal', newVal: string) => {
        if (type === 'email') setEmailContent(newVal);
        else setAppealContent(newVal);
        
        // Auto-save with debounce (500ms)
        if (!selectedCaseId) return;
        const timerRef = type === 'email' ? emailSaveTimer : appealSaveTimer;
        
        // Clear existing timer
        if (timerRef.current) {
            clearTimeout(timerRef.current);
        }
        
        // Set new timer - capture newVal in closure
        const valueToSave = newVal;
        timerRef.current = setTimeout(() => {
            // Update ref so useEffect doesn't overwrite us with our own data
            if (type === 'email') prevEmailRef.current = valueToSave;
            else prevAppealRef.current = valueToSave;
            
            onUpdateCase(selectedCaseId, type === 'email' 
                ? { generatedEmailDraft: valueToSave }
                : { generatedAppealDraft: valueToSave }
            );
        }, 500);
    };

    const handleBlurSave = (type: 'email' | 'appeal') => {
        if (!selectedCaseId) return;
        const content = type === 'email' ? emailContent : appealContent;
        
        // Clear debounce timer and save immediately
        const timerRef = type === 'email' ? emailSaveTimer : appealSaveTimer;
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
        
        // Update ref so useEffect doesn't overwrite us with our own data
        if (type === 'email') prevEmailRef.current = content;
        else prevAppealRef.current = content;

        onUpdateCase(selectedCaseId, type === 'email' 
            ? { generatedEmailDraft: content }
            : { generatedAppealDraft: content }
        );
    };
    
    const handlePromptChange = (type: 'email' | 'appeal', newVal: string) => {
        if (type === 'email') setCurrentEmailPrompt(newVal);
        else setCurrentAppealPrompt(newVal);
        
        // Auto-save prompt with debounce (1000ms)
        if (!selectedCaseId) return;
        const timerRef = type === 'email' ? emailPromptSaveTimer : appealPromptSaveTimer;
        
        // Clear existing timer
        if (timerRef.current) {
            clearTimeout(timerRef.current);
        }
        
        // Set new timer
        timerRef.current = setTimeout(() => {
            onUpdateCase(selectedCaseId, type === 'email' 
                ? { emailPrompt: newVal }
                : { appealPrompt: newVal }
            );
        }, 1000);
    };

    const handleRegenerateClick = async (type: 'email' | 'appeal') => {
        if (!selectedCaseId) return;
        setRegenerating(type);
        try {
            const promptToUse = type === 'email' ? currentEmailPrompt : currentAppealPrompt;
            await onRegenerateDraft(selectedCaseId, type, promptToUse);
        } finally {
            setRegenerating(null);
        }
    };

    const handleStageClick = async (newStage: LegalStage) => {
        if (selectedCaseId && selectedCase && selectedCase.stage !== newStage) {
            // Immediate action, no confirm dialog to make it feel responsive and "corrective"
            await onStageChange(selectedCaseId, newStage);
        }
    };

    const handleExportOutlook = () => {
        if (!selectedCase) return;
        const emlContent = `To: ${selectedCase.email}\nSubject: Suivi de votre dossier CAF ${selectedCase.id}\nX-Unsent: 1\nContent-Type: text/plain; charset=UTF-8\n\n${emailContent}`;
        const blob = new Blob([emlContent], { type: 'message/rfc822' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `brouillon_email_${selectedCase.id}.eml`;
        link.click();
    };

    const handleExportWord = () => {
        if (!selectedCase) return;
        const header = "<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><title>Export Document</title><style>body { font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 2.0; }</style></head><body>";
        const footer = "</body></html>";
        const paragraphs = appealContent.split('\n').map(p => p.trim() === '' ? '<br/>' : `<p>${p}</p>`).join('');
        const blob = new Blob(['\ufeff', header + paragraphs + footer], { type: 'application/msword' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `recours_caf_${selectedCase.id}.doc`;
        link.click();
    };

    const renderStageSelector = () => {
        if (!selectedCase) return null;
        
        const stages = [
            { id: LegalStage.CONTROL, label: 'Contrôle / Contradictoire', icon: 'fa-search' },
            { id: LegalStage.RAPO, label: 'RAPO (Recours Amiable)', icon: 'fa-gavel' },
            { id: LegalStage.LITIGATION, label: 'Contentieux (Tribunal)', icon: 'fa-balance-scale' },
        ];

        return (
            <div className="flex items-center justify-center space-x-4 bg-white p-4 border-b">
                <span className="text-gray-500 font-medium text-sm uppercase mr-2 tracking-wide">Phase Détectée :</span>
                {stages.map((stage, idx) => {
                    const isActive = selectedCase.stage === stage.id;
                    return (
                        <div key={stage.id} className="flex items-center">
                            <button
                                onClick={() => handleStageClick(stage.id)}
                                className={`flex items-center px-4 py-2 rounded-full text-sm font-bold transition-all cursor-pointer border-2 shadow-sm transform ${
                                    isActive 
                                    ? 'bg-brand-red text-white border-brand-red shadow-md scale-105' 
                                    : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                }`}
                                title="Cliquez pour changer l'étape manuellement"
                            >
                                <i className={`fas ${stage.icon} mr-2`}></i>
                                {stage.label}
                            </button>
                            {idx < stages.length - 1 && (
                                <div className="h-0.5 w-6 bg-gray-200 mx-2"></div>
                            )}
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="flex h-[calc(100vh-64px)] bg-gray-100">
            {/* Sidebar List */}
            <div className="w-1/3 bg-white border-r border-gray-200 overflow-y-auto">
                <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
                    <h2 className="font-bold text-gray-700 uppercase text-sm tracking-wider">Dossiers Entrants</h2>
                    <span className="bg-brand-red text-white text-xs px-2 py-1 rounded-full">{cases.length}</span>
                </div>
                <ul>
                    {cases.map(c => (
                        <li 
                            key={c.id} 
                            onClick={() => setSelectedCaseId(c.id)}
                            className={`p-4 border-b cursor-pointer hover:bg-blue-50 transition-colors ${selectedCaseId === c.id ? 'bg-blue-50 border-l-4 border-l-brand-red' : ''}`}
                        >
                            <div className="flex justify-between mb-1">
                                <span className="font-bold text-gray-800">{c.id}</span>
                                <span className="text-xs text-gray-400">{c.submittedAt.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                            </div>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium truncate w-1/2">{c.email}</span>
                                <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                                    c.stage === LegalStage.CONTROL ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                                    c.stage === LegalStage.RAPO ? 'bg-blue-50 text-blue-700 border-blue-200' :
                                    'bg-red-50 text-red-700 border-red-200'
                                }`}>
                                    {c.stage}
                                </span>
                            </div>
                            {/* Prestations Tags Summary in Sidebar */}
                            <div className="flex flex-wrap gap-1 mb-1">
                                {c.prestations.slice(0, 2).map((p, idx) => (
                                    <span key={idx} className={`text-[10px] px-1.5 py-0.5 rounded border ${p.isAccepted ? 'bg-gray-100 text-gray-600 border-gray-200' : 'bg-red-50 text-red-600 border-red-100'}`}>
                                        {p.name}
                                    </span>
                                ))}
                                {c.prestations.length > 2 && (
                                    <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded border border-gray-200">
                                        +{c.prestations.length - 2}
                                    </span>
                                )}
                            </div>
                            <div className="text-sm text-gray-600 truncate">{c.description || "Aucune description"}</div>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col h-full overflow-hidden">
                {loadingCase ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                        <i className="fas fa-spinner fa-spin text-4xl mb-4"></i>
                        <p className="text-lg">Chargement du dossier...</p>
                    </div>
                ) : selectedCase ? (
                    <>
                        {/* Header */}
                        <div className="bg-white border-b shadow-sm">
                            <div className="p-6 flex justify-between items-start pb-4">
                                <div>
                                    <h1 className="text-2xl font-bold text-gray-800 mb-1">Dossier #{selectedCase.id}</h1>
                                    <div className="flex flex-col space-y-2">
                                        <div className="flex space-x-6 text-sm text-gray-600">
                                            <span><i className="fas fa-envelope mr-2"></i>{selectedCase.email}</span>
                                            <span><i className="fas fa-phone mr-2"></i>{selectedCase.phone}</span>
                                        </div>
                                        <div className="flex flex-wrap gap-2 mt-1">
                                            {selectedCase.prestations.map((p, idx) => (
                                                <span key={idx} className={`text-xs font-bold px-2 py-1 rounded flex items-center ${p.isAccepted ? 'bg-gray-100 text-gray-700' : 'bg-red-100 text-red-700 animate-pulse'}`}>
                                                    <i className={`fas ${p.isAccepted ? 'fa-tag' : 'fa-exclamation-triangle'} mr-1`}></i>
                                                    {p.name}
                                                    {!p.isAccepted && " (Non traité)"}
                                                </span>
                                            ))}
                                            {selectedCase.prestations.length === 0 && (
                                                 <span className="text-xs font-bold bg-gray-100 text-gray-400 px-2 py-1 rounded">
                                                    Aucune prestation identifiée
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex flex-col items-end space-y-2">
                                    {selectedCase.files.length > 0 ? (
                                        selectedCase.files.map((file, idx) => (
                                            <button 
                                                key={idx}
                                                className="bg-white border border-gray-300 text-gray-700 px-3 py-1.5 rounded shadow-sm hover:bg-gray-50 text-xs font-medium flex items-center"
                                                onClick={() => {
                                                    const win = window.open();
                                                    if (win) win.document.write(`<iframe src="data:${file.mimeType};base64,${file.base64}" frameborder="0" style="border:0; width:100%; height:100%;" allowfullscreen></iframe>`);
                                                }}
                                            >
                                                <i className="fas fa-file-alt mr-2 text-brand-red"></i> 
                                                {file.name.length > 20 ? file.name.substring(0,20)+'...' : file.name}
                                            </button>
                                        ))
                                    ) : (
                                        <span className="text-gray-400 italic text-sm">Aucun fichier</span>
                                    )}
                                </div>
                            </div>
                            {renderStageSelector()}
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b bg-gray-50 px-6 pt-4">
                             <button onClick={() => setActiveTab('details')} className={`px-4 py-2 text-sm font-medium rounded-t-lg mr-2 transition-all ${activeTab === 'details' ? 'bg-white text-brand-red border-t border-l border-r' : 'text-gray-500 hover:text-gray-700'}`}>Détails</button>
                            <button onClick={() => setActiveTab('email')} className={`px-4 py-2 text-sm font-medium rounded-t-lg mr-2 flex items-center transition-all ${activeTab === 'email' ? 'bg-white text-brand-red border-t border-l border-r' : 'text-gray-500 hover:text-gray-700'}`}><i className="fas fa-magic mr-2 text-yellow-500"></i> Projet d'Email</button>
                            <button onClick={() => setActiveTab('appeal')} className={`px-4 py-2 text-sm font-medium rounded-t-lg mr-2 flex items-center transition-all ${activeTab === 'appeal' ? 'bg-white text-brand-red border-t border-l border-r' : 'text-gray-500 hover:text-gray-700'}`}><i className="fas fa-balance-scale mr-2 text-blue-500"></i> Projet de Recours</button>
                            <button onClick={() => setActiveTab('query')} className={`px-4 py-2 text-sm font-medium rounded-t-lg mr-2 flex items-center transition-all ${activeTab === 'query' ? 'bg-white text-brand-red border-t border-l border-r' : 'text-gray-500 hover:text-gray-700'}`}><i className="fas fa-search mr-2 text-green-500"></i> RAG Query</button>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 overflow-y-auto p-6 bg-gray-100">
                            {activeTab === 'details' && (
                                <div className="bg-white p-12 shadow-sm rounded-lg max-w-4xl mx-auto">
                                    {selectedCase.prestations.some(p => !p.isAccepted) && (
                                        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
                                            <div className="flex">
                                                <div className="flex-shrink-0">
                                                    <i className="fas fa-exclamation-circle text-red-500"></i>
                                                </div>
                                                <div className="ml-3">
                                                    <p className="text-sm text-red-700 font-bold">
                                                        Attention : Ce dossier contient des prestations non traitées par le cabinet :
                                                    </p>
                                                    <ul className="list-disc ml-5 mt-1 text-sm text-red-700">
                                                        {selectedCase.prestations.filter(p => !p.isAccepted).map((p, i) => (
                                                            <li key={i}>{p.name}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                    
                                    <h3 className="font-bold text-lg mb-4 text-gray-800 border-b pb-2">Prestations Identifiées</h3>
                                    <div className="flex flex-wrap gap-2 mb-8">
                                         {selectedCase.prestations.map((p, idx) => (
                                            <span key={idx} className={`px-3 py-1 rounded text-sm border ${p.isAccepted ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                                                {p.isAccepted ? <i className="fas fa-check-circle mr-2"></i> : <i className="fas fa-times-circle mr-2"></i>}
                                                {p.name}
                                            </span>
                                        ))}
                                    </div>

                                    <h3 className="font-bold text-lg mb-4 text-gray-800 border-b pb-2">Description du Client</h3>
                                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{selectedCase.description || "Pas de description fournie."}</p>
                                </div>
                            )}

                            {activeTab === 'query' && (
                                <div className="max-w-5xl mx-auto">
                                    <QueryInterface caseId={selectedCase.id} />
                                </div>
                            )}

                            {(activeTab === 'email' || activeTab === 'appeal') && (
                                <div className="max-w-5xl mx-auto h-full flex flex-col items-center">
                                    
                                    {/* Control Panel: Prompt Frame + Toolbar */}
                                    <div className="w-full max-w-3xl mb-8 space-y-4">
                                        
                                        {/* Prompt Frame */}
                                        <div className="bg-white rounded-lg shadow-sm border border-gray-300 overflow-hidden">
                                            <div className="bg-gray-100 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                                                <h3 className="text-sm font-bold text-gray-700 flex items-center">
                                                    <i className="fas fa-terminal mr-2 text-gray-500"></i>
                                                    Instructions pour l'IA (Prompt)
                                                </h3>
                                                <button 
                                                    onClick={() => setShowPrompt(!showPrompt)}
                                                    className="text-gray-500 hover:text-brand-dark text-xs font-medium focus:outline-none"
                                                >
                                                    {showPrompt ? 'Masquer' : 'Afficher'}
                                                </button>
                                            </div>
                                            
                                            {showPrompt && (
                                                <div className="p-0 relative">
                                                    <textarea 
                                                        className="w-full h-32 p-4 text-sm font-mono text-gray-700 bg-gray-50 border-none focus:ring-2 focus:ring-inset focus:ring-brand-red/20 outline-none resize-y"
                                                        value={activeTab === 'email' ? currentEmailPrompt : currentAppealPrompt}
                                                        onChange={(e) => handlePromptChange(activeTab, e.target.value)}
                                                        placeholder="Instructions pour la génération..."
                                                    />
                                                    <div className="absolute bottom-2 right-4 text-xs text-gray-400 pointer-events-none">
                                                        Modifiez ci-dessus pour personnaliser la génération
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Toolbar */}
                                        <div className="flex justify-between items-center bg-white p-3 rounded shadow-sm border border-gray-200">
                                            <div className="text-sm text-gray-600 flex items-center">
                                                <i className="fas fa-pen mr-2 text-blue-500"></i>
                                                <span>Document éditable (A4)</span>
                                            </div>
                                            <div className="flex space-x-2">
                                                <button 
                                                    onClick={() => handleRegenerateClick(activeTab)}
                                                    disabled={regenerating === activeTab}
                                                    className={`bg-white text-brand-dark border border-gray-300 px-4 py-2 rounded hover:bg-gray-50 transition-colors text-sm font-bold flex items-center shadow-sm ${regenerating === activeTab ? 'opacity-70 cursor-not-allowed' : ''}`}
                                                    title="Relancer l'IA avec les instructions ci-dessus"
                                                >
                                                    <i className={`fas fa-sync-alt mr-2 ${regenerating === activeTab ? 'fa-spin' : ''}`}></i> 
                                                    {regenerating === activeTab ? 'Régénération...' : 'Régénérer le brouillon'}
                                                </button>
                                                <button 
                                                    onClick={activeTab === 'email' ? handleExportOutlook : handleExportWord}
                                                    className="bg-brand-red text-white px-4 py-2 rounded hover:bg-[#b01938] transition-colors text-sm font-bold flex items-center shadow-sm"
                                                >
                                                    <i className={`fas fa-file-${activeTab === 'email' ? 'export' : 'word'} mr-2`}></i> Exporter
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* A4 Editor Page */}
                                    <div className="w-full max-w-3xl bg-white shadow-lg min-h-[297mm] relative p-12 mb-10 border border-gray-200">
                                        <textarea 
                                            className="w-full h-full min-h-[800px] border-0 focus:ring-0 p-0 text-gray-800 text-lg resize-none outline-none leading-loose bg-white"
                                            style={{ fontFamily: '"Times New Roman", Times, serif' }}
                                            value={activeTab === 'email' ? emailContent : appealContent}
                                            onChange={(e) => handleContentChange(activeTab, e.target.value)}
                                            onBlur={() => handleBlurSave(activeTab)}
                                            placeholder="Le contenu généré apparaîtra ici..."
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                        <i className="fas fa-folder-open text-6xl mb-4 text-gray-200"></i>
                        <p className="text-lg">Sélectionnez un dossier pour commencer.</p>
                    </div>
                )}
            </div>
        </div>
    );
};