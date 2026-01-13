import React from 'react';
import { Download, FileText } from 'lucide-react';
import type { Document } from '../types';

interface DocumentCardProps {
  document: Document;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document }) => {
  return (
    <div className="flex-shrink-0 w-48 p-3 border border-green-500 rounded-lg bg-white relative flex flex-col justify-between h-40">
      <div>
        <FileText className="h-6 w-6 text-teal-800 mb-2" />
        <p className="text-xs font-medium text-gray-800 line-clamp-4 leading-tight break-words">
          {document.name}
        </p>
      </div>

      <div className="flex justify-between items-end mt-2">
        <span className="text-[10px] font-bold text-gray-500">{document.size}</span>
        <button
          onClick={() => window.open(`http://localhost:8000/api/document/${document.id}/download`, '_blank')}
          className="p-1.5 bg-green-300 hover:bg-green-400 text-white rounded transition-colors group"
          title="Download Document"
        >
          <Download className="h-4 w-4 text-green-800 group-hover:text-green-900" />
        </button>
      </div>
    </div>
  );
};
