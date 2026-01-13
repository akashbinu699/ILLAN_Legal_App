import React from 'react';

export const MissedDeadlinesCard: React.FC = () => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 h-full flex flex-col">
       <h3 className="font-bold text-gray-800 text-sm mb-2">Missed Deadlines</h3>
       
       <div className="flex-1 flex flex-col justify-center">
         <div className="flex justify-between items-baseline mb-1">
             <div className="text-5xl font-bold text-gray-900 tracking-tighter">5</div>
         </div>
         <div className="flex justify-between items-center mb-6">
            <div className="text-sm text-gray-500">cases this month</div>
            <div className="text-xs font-bold text-green-500 bg-green-50 px-2 py-0.5 rounded-full">38% less</div>
         </div>

         <div className="space-y-3 pt-4 border-t border-gray-100">
             <div className="flex justify-between text-xs">
                 <span className="text-gray-500">Previous month</span>
                 <span className="font-bold text-gray-800">8 cases</span>
             </div>
             <div className="flex justify-between text-xs">
                 <span className="text-gray-500">Average delay</span>
                 <span className="font-bold text-gray-800">3 days</span>
             </div>
         </div>
       </div>
    </div>
  );
};
