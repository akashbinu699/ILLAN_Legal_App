import React from 'react';
import { Download, RefreshCw } from 'lucide-react';
import type { Case, CaseStage, ViewMode } from '../types';
import { cn } from '../utils/cn';

interface CaseHeaderProps {
  caseData: Case;
  viewMode: ViewMode;
  onViewChange: (view: ViewMode) => void;
  onCaseStageChange: (stage: CaseStage) => void;
  onFeedbackToggle: () => void;

}

export const CaseHeader: React.FC<CaseHeaderProps> = ({
  caseData,
  viewMode,
  onViewChange,
  onCaseStageChange,
  onFeedbackToggle,

}) => {
  const caseStages: CaseStage[] = ['Contradictory', 'RAPO', 'Litigation'];

  // Logic to determine if we act as if we are in feedback loop
  const isRightActionActive = viewMode === 'Email to client' || viewMode === 'Pre Action Letter';

  return (
    <div className="bg-white px-6 py-4 space-y-4">
      {/* Row A: Title & Main Download */}
      <div className="flex justify-between items-start">
        <h1 className="text-xl font-bold text-gray-900 tracking-tight">
          {caseData.fullId}
        </h1>
        <button className="bg-red-600 hover:bg-red-700 text-white p-1.5 rounded-md transition-colors">
          <Download className="h-5 w-5" />
        </button>
      </div>

      {/* Row B: Badges */}
      <div className="flex flex-wrap gap-2">
        {caseData.badges.map((badge, idx) => (
          <span
            key={idx}
            className="px-3 py-1 bg-red-700 text-white text-xs font-bold rounded-full shadow-sm"
          >
            {badge.label}
          </span>
        ))}
      </div>

      {/* Row C: 3-Zone Control Row */}
      <div className="flex items-center justify-between border-b border-gray-100 pb-2 text-sm">

        {/* Left Zone: Filter - Removed Type logic from here */}
        <div className="flex items-center gap-4 min-w-0" style={{ flex: '0 0 auto' }}>
          {/* Case Tab (View Mode Switcher) */}
          <button
            onClick={() => onViewChange('Case')}
            className={cn(
              "text-green-600 font-medium whitespace-nowrap",
              viewMode === 'Case' ? "border-b-2 border-green-600" : "hover:text-green-800"
            )}
          >
            {caseData.caseNumber}
          </button>
        </div>

        {/* Center Zone: Stages (Centered) */}
        <div className="flex-1 flex justify-center items-center gap-6">
          {/* Stage Selector (Moved to Center) */}
          <div className="flex items-center gap-1">
            {caseStages.map((stage, idx) => {
              const isSelected = caseData.statusTag === stage;
              return (
                <React.Fragment key={stage}>
                  {idx > 0 && <span className="text-gray-400 font-medium mx-1">—</span>}
                  <button
                    onClick={() => onCaseStageChange(stage)}
                    className={cn(
                      "whitespace-nowrap px-3 py-0.5 rounded-full transition-colors font-medium",
                      isSelected
                        ? "bg-green-600 text-white shadow-sm"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    )}
                  >
                    {stage}
                  </button>
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Right Zone: Actions */}
        <div className="flex items-center gap-3 justify-end min-w-0" style={{ flex: '0 0 auto' }}>




          <button
            onClick={() => onViewChange('RAG query')}
            className={cn(
              "whitespace-nowrap font-medium transition-colors",
              viewMode === 'RAG query' ? "text-gray-900 font-bold" : "text-gray-600 hover:text-gray-900"
            )}
          >
            RAG query
          </button>

          <button
            onClick={() => onViewChange('Email to client')}
            className={cn(
              "whitespace-nowrap font-medium transition-colors",
              viewMode === 'Email to client' ? "text-gray-900 font-bold" : "text-gray-600 hover:text-gray-900"
            )}
          >
            Email to client
          </button>

          <button
            onClick={onFeedbackToggle}
            className={cn(
              "p-1 rounded transition-colors",
              isRightActionActive ? "text-gray-900 bg-gray-50" : "text-gray-500 hover:bg-gray-100"
            )}
            aria-label="Toggle Feedback Loop"
          >
            <RefreshCw className="h-5 w-5" />
          </button>

          <button
            onClick={() => onViewChange('Pre Action Letter')}
            className={cn(
              "whitespace-nowrap font-medium transition-colors",
              viewMode === 'Pre Action Letter' ? "text-gray-900 font-bold" : "text-gray-600 hover:text-gray-900"
            )}
          >
            Pre Action Letter
          </button>
        </div>

      </div>

      {/* Row D: Meta Data */}
      <div className="flex flex-wrap items-start justify-between text-sm py-2">
        {/* Left: Date/Time */}
        <div className="flex gap-2 items-center">
          <div className="flex items-center overflow-hidden border border-green-600 rounded-full text-xs font-medium">
            <span className="bg-white px-3 py-1 text-gray-700">{caseData.date}</span>
            <div className="w-px h-full bg-green-600"></div>
            <span className="bg-white px-3 py-1 text-gray-700">{caseData.time}</span>
          </div>

          <div className="flex flex-col ml-4">
            <span className="text-gray-900">{caseData.client.phone}</span>
            <span className="text-gray-600">{caseData.client.email}</span>
          </div>
        </div>

        {/* Right: Client Info & Actions */}
        <div className="flex items-start gap-4">
          <div className="text-right text-xs">
            <div className="text-gray-900">{caseData.client.name}</div>
            <div className="text-gray-600">{caseData.client.street}</div>
            <div className="text-gray-600">{caseData.client.city}</div>
          </div>


        </div>
      </div>
    </div>
  );
};
