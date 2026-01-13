import React from 'react';
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, YAxis } from 'recharts';
import { Filter, Calendar } from 'lucide-react';

const data = [
  { name: 'Contradictory', value: 50, color: '#86efac' }, // Light green
  { name: 'RAPO', value: 40, color: '#10b981' }, // Medium green
  { name: 'Litigation', value: 25, color: '#0f4c5c' }, // Dark green/blue
];

export const ChartCardStageDistributions: React.FC = () => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="font-bold text-lg text-gray-800">Legal Stage Distributions</h3>
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

      {/* Chart */}
      <div className="flex-1 w-full min-h-[220px] flex items-end">
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={data} margin={{ top: 0, right: 0, left: -25, bottom: 0 }} barSize={60}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis 
                dataKey="name" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#6b7280', fontSize: 11, fontWeight: 500 }} 
                dy={10}
            />
             <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                interval={0}
                domain={[0, 60]}
                ticks={[0, 10, 20, 30, 40, 50]}
            />
            <Tooltip 
                 cursor={{fill: 'transparent'}}
                 contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
