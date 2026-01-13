import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  subtextIsPositive?: boolean;
  icon: LucideIcon;
  iconColorClass?: string;
  iconBgClass?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({ 
  title, 
  value, 
  subtext, 
  subtextIsPositive = true,
  icon: Icon,
  iconColorClass = "text-white",
  iconBgClass = "bg-green-400"
}) => {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex flex-col justify-between h-32 relative group hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <span className="font-semibold text-gray-700 text-sm">{title}</span>
        <div className={`p-2 rounded-lg ${iconBgClass} ${iconColorClass}`}>
          <Icon size={18} strokeWidth={2.5} />
        </div>
      </div>
      <div>
        <div className="text-3xl font-bold text-gray-800 tracking-tight">{value}</div>
        {subtext && (
          <div className={`text-xs mt-1 font-medium ${subtextIsPositive ? 'text-green-500' : 'text-gray-500'}`}>
            {subtext}
          </div>
        )}
      </div>
    </div>
  );
};
