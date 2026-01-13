import React from 'react';
import { Clock } from 'lucide-react';

const AgingRow = ({ label, value, colorClass, widthPercent }: { label: string, value: number, colorClass: string, widthPercent: string }) => (
  <div className="mb-4">
    <div className="flex justify-between text-xs font-semibold text-gray-500 mb-1.5">
       <div className="flex items-center gap-1.5">
         <Clock size={12} />
         <span>{label}</span>
       </div>
       <span className="text-gray-900 font-bold">{value}</span>
    </div>
    <div className="h-2.5 w-full bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${colorClass}`} style={{ width: widthPercent }}></div>
    </div>
  </div>
);

export const CaseAgingBreakdownCard: React.FC = () => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 h-full flex flex-col justify-between">
      <h3 className="font-bold text-gray-800 text-sm mb-6">Case Aging Breakdown</h3>
      
      <div className="space-y-1">
        <AgingRow label="0-7 days" value={12} colorClass="bg-green-300" widthPercent="100%" />
        <AgingRow label="7-30 days" value={8} colorClass="bg-green-600" widthPercent="60%" />
        <AgingRow label="30+ days" value={5} colorClass="bg-slate-800" widthPercent="35%" />
      </div>

      <div className="flex justify-between items-center text-xs text-gray-500 mt-4 pt-4 border-t border-gray-100">
          <span>Avg. case age</span>
          <span className="font-bold text-gray-900">14.2 days</span>
      </div>
    </div>
  );
};
