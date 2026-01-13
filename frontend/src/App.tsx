import { useState, useMemo, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { CaseHeader } from './components/CaseHeader';
import { CaseDescriptionPanel } from './components/CaseDescriptionPanel';
import { AiDraftPanel } from './components/AiDraftPanel';
import { RagQueryPanel } from './components/RagQueryPanel';
import { ClientForm } from './components/ClientForm';
import { DashboardView } from './components/dashboard/DashboardView'; // Added Dashboard
import { api } from './services/api';
import type { ViewMode, CaseStage, BenefitType, Case, MainView } from './types';

function App() {
  const [mainView, setMainView] = useState<MainView>('CLIENT');
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');
  const [viewMode, setViewMode] = useState<ViewMode>('Case');
  const [activeLawyerView, setActiveLawyerView] = useState<'dashboard' | 'case'>('dashboard'); // New state
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Filters
  const [selectedBenefits, setSelectedBenefits] = useState<BenefitType[]>([]);
  const [selectedStages, setSelectedStages] = useState<CaseStage[]>([]); // Changed to array

  // Draft State: caseId -> { email: {input, output}, letter: {input, output} }
  const [drafts, setDrafts] = useState<Record<string, {
    email: { input: string; output: string };
    letter: { input: string; output: string };
  }>>({});

  // Local state for cases
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncLoading, setSyncLoading] = useState(false);

  // Fetch cases on mount
  useEffect(() => {
    async function loadCases() {
      try {
        setLoading(true);
        const data = await api.getCases();
        setCases(data);
        if (data.length > 0) {
          setSelectedCaseId(data[0].id);
        }
      } catch (err) {
        console.error("Failed to load cases", err);
        setError("Failed to load cases");
      } finally {
        setLoading(false);
      }
    }
    loadCases();
  }, []);

  const selectedCase = useMemo(() =>
    cases.find(c => c.id === selectedCaseId) || cases[0],
    [selectedCaseId, cases]
  );

  const filteredCases = useMemo(() => {
    return cases.filter(c => {
      // 1. Unread Filter
      if (showUnreadOnly && c.isRead) return false;
      // 2. Search Filter
      if (searchTerm) {
        const lower = searchTerm.toLowerCase();
        const matches = (
          c.caseNumber.toLowerCase().includes(lower) ||
          c.email.toLowerCase().includes(lower) ||
          c.client.name.toLowerCase().includes(lower)
        );
        if (!matches) return false;
      }
      // 3. Benefit Filter
      if (selectedBenefits.length > 0 && !selectedBenefits.includes(c.benefitType)) {
        return false;
      }
      // 4. Stage Filter (Updated)
      if (selectedStages.length > 0) {
        // If 'Unread' is one of the selected stages (legacy check?), ignore? No 'Unread' is not a stage.
        // Match stage
        if (!selectedStages.includes(c.statusTag)) return false;
      }

      return true;
    });
  }, [cases, showUnreadOnly, searchTerm, selectedBenefits, selectedStages]);

  const handleUpdateCaseStage = async (newStage: CaseStage) => {
    try {
      // Optimistic update
      setCases(prev => prev.map(c =>
        c.id === selectedCaseId ? { ...c, statusTag: newStage } : c
      ));

      // API Call
      await api.updateCaseStage(selectedCaseId, newStage);

    } catch (err) {
      console.error("Failed to update stage", err);
      // Revert? (Not implemented for brevity)
    }
  };

  const handleFeedbackToggle = () => {
    if (viewMode === 'Email to client') {
      setViewMode('Pre Action Letter');
    } else if (viewMode === 'Pre Action Letter') {
      setViewMode('Email to client');
    } else {
      setViewMode('Email to client');
    }
  };

  const handleDescriptionChange = (desc: string) => {
    setCases(prev => prev.map(c =>
      c.id === selectedCaseId ? { ...c, description: desc } : c
    ));
    // TODO: persist description change to backend
  };

  const handleSyncGmail = async () => {
    try {
      setSyncLoading(true);
      // Trigger Background Sync
      await api.syncAllGmail();
      alert("Sync started in background! Cases will appear as they are processed.");

      // Poll for updates every 2s for 60s max, or until user stops?
      // Simple logic: Poll 15 times (30 seconds)
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        try {
          const data = await api.getCases();
          // Only update if count changed? Or just update always to show progress
          setCases(prev => {
            if (data.length !== prev.length) {
              return data;
            }
            return prev; // Or data if deep comparison needed
          });
          setCases(data); // Force update

          if (attempts >= 30) {
            clearInterval(interval);
            setSyncLoading(false);
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 2000);

    } catch (err) {
      console.error("Sync trigger failed", err);
      alert("Gmail Sync trigger failed.");
      setSyncLoading(false);
    }
  };

  const handleClientSubmit = async (data: any) => {
    try {
      await api.submitCase(data);
      setMainView('SUCCESS');
    } catch (err) {
      console.error("Submission failed", err);
      alert("Submission failed. Please try again.");
    }
  };

  // Draft Helper
  const getDraftDefaults = (mode: 'email' | 'letter') => {
    const contextTitle = mode === 'email' ? 'Email' : 'Letter';
    return {
      input: `CONTEXTE (${contextTitle}) :

Tu es avocat spécialisé en droit administratif (CAF).
Je rédige pour le compte du Maître Elias BRIKH MAROC.

THEME_REDRESSEMENT
"Encore dois traiter le Cabinet ([R]), et recours dans le cas où il n'a traité pas ([X]) (Generalites)."
Notre cabinet pratique en droit public et ne connaît que des recours et contentieux relatifs aux prestations sociales.

TONE : Professional, clear, concise
AUDIENCE : CAF administration
LONGUEUR : 1 page maximum

REFERENCES JURIDIQUES :
- Code de la sécurité sociale, art. L. 553-1
- Jurisprudence sur les erreurs de calcul CAF
`,
      output: `To: email@example.com

Subject: Contestation de décision de régularisation

Madame, Monsieur,
Je me permets de vous contacter afin de contester.
... (Default text)
`
    };
  };

  const currentDraft = useMemo(() => {
    const caseDrafts = drafts[selectedCaseId] || {
      email: getDraftDefaults('email'),
      letter: getDraftDefaults('letter')
    };
    return viewMode === 'Email to client' ? caseDrafts.email : caseDrafts.letter;
  }, [drafts, selectedCaseId, viewMode]);

  const handleDraftUpdate = (field: 'input' | 'output', value: string) => {
    setDrafts(prev => {
      const caseDrafts = prev[selectedCaseId] || {
        email: getDraftDefaults('email'),
        letter: getDraftDefaults('letter')
      };

      const modeKey = viewMode === 'Email to client' ? 'email' : 'letter';

      return {
        ...prev,
        [selectedCaseId]: {
          ...caseDrafts,
          [modeKey]: {
            ...caseDrafts[modeKey],
            [field]: value
          }
        }
      };
    });
  };

  // Render content logic based on viewMode
  const renderContent = () => {
    if (!selectedCase) return <div className="p-10">No case selected</div>;

    if (viewMode === 'Case') {
      return (
        <CaseDescriptionPanel
          caseData={selectedCase}
          onDescriptionChange={handleDescriptionChange}
        />
      );
    }
    if (viewMode === 'RAG query') {
      return (
        <RagQueryPanel
          caseData={selectedCase}
        />
      );
    }
    if (viewMode === 'Email to client' || viewMode === 'Pre Action Letter') {
      return (
        <AiDraftPanel
          mode={viewMode === 'Email to client' ? 'email' : 'letter'}
          inputContent={currentDraft.input}
          onInputChange={(val) => handleDraftUpdate('input', val)}
          outputContent={currentDraft.output}
          onOutputChange={(val) => handleDraftUpdate('output', val)}
        />
      );
    }
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-10 text-gray-400">
        <div className="text-xl font-bold text-gray-300 mb-2">{viewMode} View</div>
        <p>View content placeholder</p>
      </div>
    );
  };

  if (loading) {
    return <div className="flex h-screen w-screen items-center justify-center">Loading cases...</div>;
  }

  if (error) {
    return <div className="flex h-screen w-screen items-center justify-center text-red-500">{error}</div>;
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-gray-50 font-sans">
      {/* Top App Bar */}
      <header className="h-12 bg-lmGreenDark/90 bg-[#88e4a8] flex items-center justify-between px-4 flex-shrink-0 z-20 shadow-sm relative">
        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => setActiveLawyerView('dashboard')}
        >
          <div className="w-8 h-8 rounded bg-[#166534] flex items-center justify-center text-white font-bold text-sm">
            LM
          </div>
          <span className="text-white font-medium text-lg">Legal Manager</span>
        </div>

        <div className="flex items-center gap-4">
          <nav className="flex bg-white/20 rounded-lg p-1">
            <button
              onClick={() => setMainView('CLIENT')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${mainView === 'CLIENT' || mainView === 'SUCCESS' ? 'bg-white text-green-800 shadow-sm' : 'text-white hover:bg-white/10'}`}
            >
              Client View
            </button>
            <button
              onClick={() => setMainView('LAWYER')}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${mainView === 'LAWYER' ? 'bg-white text-green-800 shadow-sm' : 'text-white hover:bg-white/10'}`}
            >
              Lawyer Space
            </button>
          </nav>
          <button className="text-white hover:text-green-800 font-medium text-sm transition-colors">
            Logout
          </button>
        </div>
      </header>

      {mainView === 'CLIENT' && (
        <main className="flex-1 overflow-y-auto bg-gray-100 py-10">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">Contestez votre décision CAF</h1>
            <p className="text-gray-600">Formulaire d'analyse gratuite de votre dossier</p>
          </div>
          <ClientForm onSubmit={handleClientSubmit} />
        </main>
      )}

      {mainView === 'SUCCESS' && (
        <main className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-white">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Dossier reçu avec succès</h2>
          <p className="text-gray-600 max-w-md mb-8">
            Merci. Notre équipe d'avocats analyse actuellement vos pièces jointes. Vous recevrez une réponse sous 24h.
          </p>
          <button
            onClick={() => setMainView('LAWYER')}
            className="bg-[#166534] text-white px-6 py-3 rounded-lg font-bold hover:bg-green-800 transition-colors"
          >
            Accéder à l'Espace Avocat
          </button>
        </main>
      )}

      {/* Main Layout (Lawyer View) */}
      {mainView === 'LAWYER' && (
        <div className="flex flex-1 overflow-hidden relative">

          {/* Empty State Handling */}
          {cases.length === 0 && !loading ? (
            <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 text-center p-8">
              <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mb-6">
                <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">No Cases Found</h3>
              <p className="text-gray-600 max-w-sm mb-8">
                Your database is currently empty. Click the button below to sync with Gmail and import your cases.
              </p>
              <button
                onClick={handleSyncGmail}
                disabled={syncLoading}
                className="bg-[#166534] text-white px-6 py-3 rounded-lg font-bold hover:bg-green-800 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {syncLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Syncing...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                    Sync from Gmail
                  </>
                )}
              </button>
            </div>
          ) : (
            <>
              {/* Sidebar */}
              <Sidebar
                cases={filteredCases}
                selectedCaseId={selectedCaseId}
                onSelectCase={(id) => {
                  setSelectedCaseId(id);
                  setActiveLawyerView('case');
                }}
                showUnreadOnly={showUnreadOnly}
                onToggleUnread={setShowUnreadOnly}
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
                selectedBenefits={selectedBenefits}
                onBenefitChange={setSelectedBenefits}
                selectedStages={selectedStages}
                onStageChange={setSelectedStages}
              />

              {/* Main Content Area */}
              <main className="flex-1 flex flex-col min-w-0 bg-white">
                {activeLawyerView === 'case' ? (
                  <>
                    <CaseHeader
                      caseData={selectedCase}
                      viewMode={viewMode}
                      onViewChange={setViewMode}
                      onCaseStageChange={handleUpdateCaseStage}
                      onFeedbackToggle={handleFeedbackToggle}
                      onSyncGmail={handleSyncGmail}
                      syncLoading={syncLoading}
                    />

                    <div className="flex-1 overflow-hidden relative bg-white">
                      {renderContent()}
                    </div>
                  </>
                ) : (
                  <DashboardView />
                )}
              </main>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
