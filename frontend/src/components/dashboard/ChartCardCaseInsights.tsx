import React from 'react';
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell, YAxis, CartesianGrid } from 'recharts';
import { Filter, Calendar } from 'lucide-react';

const data = [
  { name: 'Jan', value: 13 },
  { name: 'Feb', value: 18 },
  { name: 'Mar', value: 16 },
  { name: 'Apr', value: 11 },
  { name: 'May', value: 23 },
  { name: 'Jun', value: 3 },
];

export const ChartCardCaseInsights: React.FC = () => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="font-bold text-lg text-gray-800">Case Insights</h3>
          <p className="text-sm text-gray-400">Last 6 months</p>
        </div>
        <div className="flex gap-2">
           <button className="flex items-center gap-1 bg-gray-100 hover:bg-gray-200 text-gray-400 px-2 py-1 rounded text-xs font-medium transition-colors">
             <Calendar size={12} />
             <span>Select a date range</span>
           </button>
           <button className="p-1.5 bg-white text-gray-400 hover:text-gray-600 rounded">
             <Filter size={16} />
           </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex gap-4 mb-6">
        <div className="bg-white border border-gray-100 rounded-lg p-3 flex-1 shadow-sm">
            <div className="text-gray-500 text-xs font-medium mb-1">Total Cases</div>
            <div className="text-2xl font-bold text-gray-800">84</div>
            <div className="text-green-500 text-xs font-bold mt-1">+8.6%</div>
        </div>
         <div className="bg-white border border-gray-100 rounded-lg p-3 flex-1 shadow-sm">
            <div className="text-gray-500 text-xs font-medium mb-1">Avg. Daily</div>
            <div className="text-2xl font-bold text-gray-800">10.4</div>
            <div className="text-gray-400 text-xs mt-1">per day (180d)</div>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 w-full min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 0, right: 0, left: -25, bottom: 0 }} barSize={34}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis 
                dataKey="name" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#9ca3af', fontSize: 12 }} 
                dy={10}
            />
            <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                interval={0}
                domain={[0, 25]}
                ticks={[0, 5, 10, 15, 20, 25]}
            />
            <Tooltip 
                cursor={{fill: 'transparent'}}
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill="#86efac" />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
