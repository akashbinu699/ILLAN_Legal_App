import React from 'react';
import { Briefcase, CheckSquare, Clock, Scale } from 'lucide-react';
import { KpiCard } from './KpiCard';
import { ChartCardCaseInsights } from './ChartCardCaseInsights';
import { ChartCardStageDistributions } from './ChartCardStageDistributions';
import { CaseAgingBreakdownCard } from './CaseAgingBreakdownCard';
import { DeadlinePrioritiesCard } from './DeadlinePrioritiesCard';
import { MissedDeadlinesCard } from './MissedDeadlinesCard';
import { UsageRestrictionsCard } from './UsageRestrictionsCard';

export const DashboardView: React.FC = () => {
  return (
    <div className="p-6 bg-gray-50 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6 pl-1">Dashboard</h1>
      
      <div className="flex flex-col gap-6 w-full">
        {/* Row 1: KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KpiCard 
            title="Total Cases" 
            value={154} 
            subtext="+12% from last month"
            icon={Briefcase}
            iconBgClass="bg-emerald-100"
            iconColorClass="text-emerald-600"
          />
          <KpiCard 
            title="Case Replied" 
            value={132} 
            subtext="+8% from last month"
            icon={CheckSquare}
            iconBgClass="bg-green-100"
            iconColorClass="text-green-600"
          />
          <KpiCard 
            title="Pending Response" 
            value={12} 
            subtext=""
            icon={Clock}
            iconBgClass="bg-green-100"
            iconColorClass="text-green-600"
          />
          <KpiCard 
            title="Active Disputes" 
            value={56} 
            subtext=""
            icon={Scale}
            iconBgClass="bg-green-100"
            iconColorClass="text-green-600"
          />
        </div>

        {/* Row 2: Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[400px]">
           <ChartCardCaseInsights />
           <ChartCardStageDistributions />
        </div>

        {/* Row 3: Medium Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
           <div className="h-full min-h-[260px]">
             <CaseAgingBreakdownCard />
           </div>
           <div className="h-full min-h-[260px]">
             <DeadlinePrioritiesCard />
           </div>
           <div className="h-full min-h-[260px]">
             <MissedDeadlinesCard />
           </div>
        </div>

        {/* Row 4: Usage Restrictions */}
        <div className="w-full">
            <UsageRestrictionsCard />
        </div>

        {/* Bottom Spacer */}
        <div className="h-10"></div>
      </div>
    </div>
  );
};
