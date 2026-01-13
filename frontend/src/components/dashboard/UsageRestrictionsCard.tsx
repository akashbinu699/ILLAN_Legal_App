import React from 'react';
import { Sparkles, Mail, Cloud, Database } from 'lucide-react';

const UsageRow = ({ icon: Icon, label, value, max, limitStr }: { icon: any, label: string, value: number, max: number, limitStr: string }) => {
    const percentage = Math.min((value / max) * 100, 100);
    return (
        <div className="mb-5 last:mb-0">
            <div className="flex justify-between items-center text-xs mb-2">
                <div className="flex items-center gap-2 font-bold text-gray-700">
                    <Icon size={14} className="text-gray-400" />
                    <span>{label}</span>
                </div>
                <span className="text-gray-500 font-medium">{limitStr}</span>
            </div>
            <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                <div 
                    className="h-full bg-slate-800 rounded-full transition-all duration-500" 
                    style={{ width: `${percentage}%` }}
                ></div>
            </div>
        </div>
    );
};

export const UsageRestrictionsCard: React.FC = () => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="mb-6">
          <h3 className="font-bold text-gray-800 text-sm">Usage Restrictions</h3>
          <p className="text-xs text-gray-400 mt-1">API & Storage limits</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
         <UsageRow 
            icon={Sparkles} 
            label="Gemini API Tokens" 
            value={75000} 
            max={100000} 
            limitStr="75,000 / 100,000 tokens" 
         />
         <UsageRow 
            icon={Mail} 
            label="Gmail API Fetch" 
            value={350} 
            max={1000} 
            limitStr="350 / 1,000 requests" 
         />
         <UsageRow 
            icon={Cloud} 
            label="Cloud Storage" 
            value={257.48}
            max={1024} 
            limitStr="257.48 / 1,024 GB" 
         />
         <UsageRow 
            icon={Database} 
            label="Local Storage" 
            value={457.48} 
            max={500} 
            limitStr="457.48 / 500 GB" 
         />
      </div>
    </div>
  );
};
