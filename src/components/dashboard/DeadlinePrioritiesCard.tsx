import React from 'react';
import { AlertTriangle, Clock, CheckCircle2 } from 'lucide-react';

const PriorityRow = ({ label, value, bgClass, icon: Icon }: { label: string, value: number, bgClass: string, icon: any }) => (
  <div className={`${bgClass} rounded-lg p-3 flex justify-between items-center text-white mb-3 shadow-sm`}>
    <div className="flex items-center gap-3">
        <div className="rounded-full border-2 border-white/30 p-1">
            <Icon size={14} strokeWidth={3} />
        </div>
        <span className="font-medium text-sm">{label}</span>
    </div>
    <span className="font-bold text-lg">{value}</span>
  </div>
);

export const DeadlinePrioritiesCard: React.FC = () => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 h-full">
      <h3 className="font-bold text-gray-800 text-sm mb-4">Deadline Priorities</h3>
      
      <div className="flex flex-col justify-center h-[80%]">
        <PriorityRow label="Within 3 days" value={8} bgClass="bg-green-400" icon={AlertTriangle} />
        <PriorityRow label="Within 5 days" value={15} bgClass="bg-green-500" icon={Clock} />
        <PriorityRow label="More than 5 days" value={32} bgClass="bg-green-600/80" icon={CheckCircle2} />
      </div>
    </div>
  );
};
