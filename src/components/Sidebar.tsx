import React, { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown } from 'lucide-react';
import type { Case, BenefitType, CaseStage } from '../types';
import { cn } from '../utils/cn';

interface SidebarProps {
  cases: Case[];
  selectedCaseId: string;
  onSelectCase: (id: string) => void;
  showUnreadOnly: boolean;
  onToggleUnread: (showUnread: boolean) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  selectedBenefits: BenefitType[]; // Changed to array
  onBenefitChange: (val: BenefitType[]) => void;
  selectedStage: CaseStage | 'All' | null;
  onStageChange: (val: CaseStage | 'All') => void;
}

const BENEFIT_TYPES: BenefitType[] = [
  'APL', 'RSA', 'PPA', 'NOEL', 'AUUVVC', 'AMENDE', 'RECOUV', 'ACADINASS', 
  'CAFINASS', 'MAJO', 'AAH', 'AEEH', 'AJPP', 'AJPA', 'AVPF', 'AUTRES'
];

export const Sidebar: React.FC<SidebarProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  showUnreadOnly,
  onToggleUnread,
  searchTerm,
  onSearchChange,
  selectedBenefits,
  onBenefitChange,
  selectedStage,
  onStageChange,
}) => {
  // Benefit Dropdown State
  const [isBenefitOpen, setIsBenefitOpen] = useState(false);
  const [tempBenefits, setTempBenefits] = useState<BenefitType[]>([]);
  const benefitRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (benefitRef.current && !benefitRef.current.contains(event.target as Node)) {
        setIsBenefitOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Sync temp benefits when opening
  useEffect(() => {
    if (isBenefitOpen) {
      if (selectedBenefits.length === 0) {
        // If empty (All selected logically), fill checkboxes
        setTempBenefits([...BENEFIT_TYPES]);
      } else {
        setTempBenefits(selectedBenefits);
      }
    }
  }, [isBenefitOpen, selectedBenefits]);

  const handleBenefitToggle = (type: BenefitType) => {
    if (tempBenefits.includes(type)) {
      setTempBenefits(tempBenefits.filter(t => t !== type));
    } else {
      setTempBenefits([...tempBenefits, type]);
    }
  };

  const handleAllToggle = () => {
    if (tempBenefits.length === BENEFIT_TYPES.length) {
      setTempBenefits([]); // Clear all
    } else {
      setTempBenefits([...BENEFIT_TYPES]); // Select all
    }
  };

  const handleApplyBenefits = () => {
    // If all are selected, or none (which defaults to all), pass empty array to App (optimisation/logic)
    if (tempBenefits.length === BENEFIT_TYPES.length || tempBenefits.length === 0) {
        onBenefitChange([]);
    } else {
        onBenefitChange(tempBenefits);
    }
    setIsBenefitOpen(false);
  };

  const isAllChecked = tempBenefits.length === BENEFIT_TYPES.length;

  return (
    <div className="w-80 h-full bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
      {/* Search & Filter Header */}
      <div className="p-4 border-b border-gray-100 space-y-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search case or email"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-gray-50 border-none rounded-md text-sm focus:ring-1 focus:ring-green-500 outline-none"
          />
        </div>

        {/* Filter Toggle & Type */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 w-full">
             {/* Benefit Multi-Select */}
             <div className="flex-1 min-w-0 relative" ref={benefitRef}>
                <button
                  onClick={() => setIsBenefitOpen(!isBenefitOpen)}
                  className="w-full bg-gray-50 border border-gray-200 text-gray-700 py-1 pl-2 pr-2 rounded focus:outline-none focus:ring-1 focus:ring-green-500 text-xs font-medium flex justify-between items-center"
                >
                  <span>Benefit</span>
                  <ChevronDown className="h-3 w-3 text-gray-500" />
                </button>
                
                {isBenefitOpen && (
                  <div className="absolute top-full left-0 mt-1 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-50 flex flex-col">
                    <div className="max-h-60 overflow-y-auto p-2 space-y-1">
                      {/* All Option */}
                      <label className="flex items-center space-x-2 p-1 hover:bg-gray-50 rounded cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={isAllChecked}
                          onChange={handleAllToggle}
                          className="rounded text-green-600 focus:ring-green-500 h-3 w-3"
                        />
                        <span className="text-xs font-medium text-gray-700">All</span>
                      </label>
                      <div className="h-px bg-gray-100 my-1"></div>
                      {/* Individual Options */}
                      {BENEFIT_TYPES.map(type => (
                         <label key={type} className="flex items-center space-x-2 p-1 hover:bg-gray-50 rounded cursor-pointer">
                           <input 
                             type="checkbox" 
                             checked={tempBenefits.includes(type)}
                             onChange={() => handleBenefitToggle(type)}
                             className="rounded text-green-600 focus:ring-green-500 h-3 w-3"
                           />
                           <span className="text-xs text-gray-700">{type}</span>
                         </label>
                      ))}
                    </div>
                    {/* Apply Button */}
                    <div className="p-2 border-t border-gray-100 flex justify-end">
                       <button
                         onClick={handleApplyBenefits}
                         className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
                       >
                         Apply
                       </button>
                    </div>
                  </div>
                )}
             </div>
             
             {/* Stage Dropdown */}
             <div className="flex-1 min-w-0">
                <div className="relative w-full">
                     <select
                      value={selectedStage === 'All' ? '' : selectedStage || ''}
                      onChange={(e) => onStageChange(e.target.value as CaseStage | 'All')}
                      className="w-full appearance-none bg-gray-50 border border-gray-200 text-gray-700 py-1 pl-2 pr-6 rounded focus:outline-none focus:ring-1 focus:ring-green-500 text-xs font-medium cursor-pointer relative z-10 bg-transparent"
                    >
                      <option value="" disabled hidden>Stage</option>
                      <option value="All">All</option>
                      <option value="Contradictory">Contradictory</option>
                      <option value="RAPO">RAPO</option>
                      <option value="Litigation">Litigation</option>
                    </select>
                     {/* Custom Arrow */}
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none z-0">
                      <ChevronDown className="h-3 w-3 text-gray-500" />
                    </div>
                </div>
             </div>
          </div>

          <div className="flex bg-gray-100 rounded-lg p-1 w-full relative">
            <button
              onClick={() => onToggleUnread(false)}
              className={cn(
                "flex-1 py-1 rounded-md text-xs font-medium transition-all text-center z-10",
                !showUnreadOnly ? "bg-green-600 text-white shadow-sm" : "bg-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              Read
            </button>
            <button
              onClick={() => onToggleUnread(true)}
              className={cn(
                "flex-1 py-1 rounded-md text-xs font-medium transition-all text-center z-10",
                showUnreadOnly ? "bg-green-600 text-white shadow-sm" : "bg-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              Unread
            </button>
          </div>
        </div>
      </div>

      {/* Case List */}
      <div className="flex-1 overflow-y-auto">
        {cases.map((c) => (
          <div
            key={c.id}
            onClick={() => onSelectCase(c.id)}
            className={cn(
              "p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors",
              selectedCaseId === c.id ? "bg-green-50 border-l-4 border-l-lm-active" : "border-l-4 border-l-transparent"
            )}
          >
            <div className="flex justify-between items-start mb-1">
              <div>
                <span className="font-bold text-sm text-gray-900 block">{c.caseNumber}</span>
                <span className="text-xs text-gray-500 block truncate max-w-[120px]" title={c.email}>{c.email}</span>
              </div>
              <div className="text-right">
                <span className="text-xs text-gray-500 font-medium block">{c.date}</span>
                <span className="text-[10px] text-gray-400 block">{c.time}</span>
              </div>
            </div>
            
            <div className="flex justify-between items-end mt-2">
              <div className="flex flex-wrap gap-1 max-w-[65%]">
                {c.badges.map((badge, idx) => (
                  <span 
                    key={idx}
                    className="px-1.5 py-0.5 rounded-full bg-red-600 text-[9px] font-bold text-white whitespace-nowrap"
                  >
                    {badge.label}
                  </span>
                ))}
              </div>
              <span className="px-2 py-0.5 bg-green-200 text-green-800 text-[10px] font-semibold rounded-full whitespace-nowrap">
                {c.statusTag}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

