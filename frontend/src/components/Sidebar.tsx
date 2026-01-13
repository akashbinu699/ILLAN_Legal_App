import React, { useState, useEffect, useRef } from 'react';
import { Search, Filter } from 'lucide-react';
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
  selectedBenefits: BenefitType[];
  onBenefitChange: (val: BenefitType[]) => void;
  selectedStages: CaseStage[]; // Changed to array
  onStageChange: (val: CaseStage[]) => void;
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
  selectedStages,
  onStageChange,
}) => {
  // Filter Popover State
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  // Temporary State for Filters (applied only on "APPLY")
  const [tempStages, setTempStages] = useState<CaseStage[]>(selectedStages);
  const [tempBenefits, setTempBenefits] = useState<BenefitType[]>(selectedBenefits);

  // Sync temp state when opening
  useEffect(() => {
    if (isFilterOpen) {
      setTempStages(selectedStages);

      // Handle the logic where empty selectedBenefits means "Effective All" visually if you want, 
      // or just sync exactly what is selected. The requirement says:
      // "If ALL selected, all benefits are considered selected."
      // If the parent passes [], it usually means NO filter (so all).
      // Let's assume parent state [] means ALL.
      if (selectedBenefits.length === 0) {
        setTempBenefits([...BENEFIT_TYPES]);
      } else {
        setTempBenefits(selectedBenefits);
      }
    }
  }, [isFilterOpen, selectedStages, selectedBenefits]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(event.target as Node)) {
        setIsFilterOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleStageToggle = (stage: CaseStage) => {
    if (tempStages.includes(stage)) {
      setTempStages(tempStages.filter(s => s !== stage));
    } else {
      setTempStages([...tempStages, stage]);
    }
  };

  const handleBenefitToggle = (type: BenefitType) => {
    if (tempBenefits.includes(type)) {
      setTempBenefits(tempBenefits.filter(t => t !== type));
    } else {
      setTempBenefits([...tempBenefits, type]);
    }
  };

  const handleAllBenefitsToggle = () => {
    const allSelected = tempBenefits.length === BENEFIT_TYPES.length;
    if (allSelected) {
      setTempBenefits([]); // Clear
    } else {
      setTempBenefits([...BENEFIT_TYPES]);
    }
  };

  const handleApply = () => {
    // 1. Stage
    onStageChange(tempStages);

    // 2. Benefits
    // If current temp is full list, we pass empty array to signify "No filter" (All)
    // or we pass the full list. Based on previous implementation logic:
    if (tempBenefits.length === BENEFIT_TYPES.length || tempBenefits.length === 0) {
      onBenefitChange([]);
    } else {
      onBenefitChange(tempBenefits);
    }

    setIsFilterOpen(false);
  };

  const isAllBenefitsChecked = tempBenefits.length === BENEFIT_TYPES.length;

  return (
    <div className="w-80 h-full bg-white border-r border-gray-200 flex flex-col flex-shrink-0 relative">
      {/* Search & Filter Header */}
      <div className="p-3 border-b border-gray-100 space-y-2">
        {/* Row 1: Search at the top */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search case or email"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-gray-50 border-none rounded-md text-sm focus:ring-1 focus:ring-green-500 outline-none placeholder-gray-400 text-gray-700"
          />
        </div>

        {/* Row 2: Filter Button + Read/Unread Toggle */}
        <div className="flex items-center gap-2">

          {/* Filter Button with Popover */}
          <div className="relative" ref={filterRef}>
            <button
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              className={cn(
                "p-2 rounded-md border text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors",
                isFilterOpen || (selectedStages.length > 0 || selectedBenefits.length > 0) ? "border-green-500 text-green-600 bg-green-50" : "border-gray-200"
              )}
            >
              <Filter className="h-4 w-4" />
            </button>

            {/* The Popover */}
            {isFilterOpen && (
              <div className="absolute top-full left-0 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-xl z-50 p-4 flex flex-col gap-4">

                {/* Section: Stage */}
                <div>
                  <h4 className="text-xs font-bold text-gray-900 mb-2 uppercase tracking-wide">Stage</h4>
                  <div className="flex flex-wrap gap-2">
                    {(['Contradictory', 'RAPO', 'Litigation'] as CaseStage[]).map(stage => (
                      <button
                        key={stage}
                        onClick={() => handleStageToggle(stage)}
                        className={cn(
                          "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
                          tempStages.includes(stage)
                            ? "bg-green-100 border-green-200 text-green-800"
                            : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
                        )}
                      >
                        {stage}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Section: Benefits */}
                <div>
                  <h4 className="text-xs font-bold text-gray-900 mb-2 uppercase tracking-wide">Benefits</h4>
                  <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
                    <button
                      onClick={handleAllBenefitsToggle}
                      className={cn(
                        "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
                        isAllBenefitsChecked
                          ? "bg-green-100 border-green-200 text-green-800"
                          : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
                      )}
                    >
                      ALL
                    </button>
                    {BENEFIT_TYPES.map(type => (
                      <button
                        key={type}
                        onClick={() => handleBenefitToggle(type)}
                        className={cn(
                          "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
                          tempBenefits.includes(type)
                            ? "bg-green-100 border-green-200 text-green-800"
                            : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
                        )}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Apply Button */}
                <div className="pt-2 border-t border-gray-100">
                  <button
                    onClick={handleApply}
                    className="w-full py-2 bg-green-600 text-white text-xs font-bold rounded-md hover:bg-green-700 transition-colors uppercase tracking-wide"
                  >
                    Apply
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Read/Unread Toggle */}
          <div className="flex items-center justify-end flex-1 gap-1">
            <button
              onClick={() => onToggleUnread(false)}
              className={cn(
                "px-3 py-1 rounded text-[10px] font-medium transition-all text-center border mr-1",
                !showUnreadOnly ? "bg-lmGreenDark bg-[#166534] text-white border-[#166534]" : "bg-white text-gray-500 border-gray-200 hover:text-gray-700"
              )}
              style={{ backgroundColor: !showUnreadOnly ? 'rgb(22, 101, 52)' : 'white' }}
            >
              Read
            </button>
            <button
              onClick={() => onToggleUnread(true)}
              className={cn(
                "px-3 py-1 rounded text-[10px] font-medium transition-all text-center border",
                showUnreadOnly ? "bg-lmGreenDark bg-[#166534] text-white border-[#166534]" : "bg-white text-gray-500 border-gray-200 hover:text-gray-700"
              )}
              style={{ backgroundColor: showUnreadOnly ? 'rgb(22, 101, 52)' : 'white' }}
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
              "p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors relative",
              selectedCaseId === c.id ? "bg-green-50/50" : ""
            )}
          >
            {/* Active Indication Strip */}
            {selectedCaseId === c.id && (
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-green-500" />
            )}

            <div className="flex justify-between items-start mb-1 pl-1">
              <div>
                <span className="font-bold text-sm text-gray-900 block">{c.caseNumber}</span>
                <span className="text-xs text-gray-500 block truncate max-w-[120px]" title={c.email}>{c.email}</span>
              </div>
              <div className="text-right">
                <span className="text-xs text-gray-500 font-medium block">{c.date}</span>
                <span className="text-[10px] text-gray-400 block">{c.time}</span>
              </div>
            </div>

            <div className="flex justify-between items-end mt-2 pl-1">
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
              <span className={cn(
                "px-2 py-0.5 text-[10px] font-bold rounded-full whitespace-nowrap",
                c.statusTag === 'RAPO' ? "bg-emerald-100 text-emerald-700" :
                  c.statusTag === 'Litigation' ? "bg-slate-800 text-white" :
                    "bg-green-200 text-green-800"
              )}>
                {c.statusTag}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
