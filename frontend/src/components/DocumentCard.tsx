import React from 'react';
import { Download, FileText } from 'lucide-react';
import type { Document } from '../types';

interface DocumentCardProps {
  document: Document;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document }) => {
  /* State for Modal Preview */
  const [isPreviewOpen, setIsPreviewOpen] = React.useState(false);

  const previewUrl = `http://localhost:8000/api/document/${document.id}/download?inline=true`;
  const downloadUrl = `http://localhost:8000/api/document/${document.id}/download`;
  const isPdf = document.type === 'pdf' || document.mime_type?.includes('pdf');
  const isImage = document.type === 'image' || document.mime_type?.includes('image');

  const handleOpenPreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsPreviewOpen(true);
  };

  const handleClosePreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsPreviewOpen(false);
  };

  return (
    <>
      <div 
        onClick={handleOpenPreview}
        className="flex-shrink-0 w-48 p-3 border border-green-500 rounded-lg bg-white relative flex flex-col justify-between h-40 transition-shadow hover:shadow-lg cursor-pointer"
      >
        <div>
          <FileText className="h-6 w-6 text-teal-800 mb-2" />
          <p className="text-xs font-medium text-gray-800 line-clamp-4 leading-tight break-words">
            {document.name}
          </p>
        </div>

        <div className="flex justify-between items-end mt-2">
          <span className="text-[10px] font-bold text-gray-500">{document.size}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              window.open(downloadUrl, '_blank');
            }}
            className="p-1.5 bg-green-300 hover:bg-green-400 text-white rounded transition-colors group"
            title="Download Document"
          >
            <Download className="h-4 w-4 text-green-800 group-hover:text-green-900" />
          </button>
        </div>
      </div>

      {/* Full Screen Preview Modal */}
      {isPreviewOpen && (
        <div 
          className="fixed inset-0 z-[9999] bg-black/80 flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={handleClosePreview}
        >
          <div 
            className="bg-white w-full max-w-5xl h-[90vh] rounded-xl flex flex-col overflow-hidden shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
               <h3 className="font-semibold text-gray-700 truncate pr-4">{document.name}</h3>
               <div className="flex items-center gap-2">
                  <button
                    onClick={() => window.open(downloadUrl, '_blank')}
                    className="flex items-center gap-1 text-sm bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 transition"
                  >
                    <Download className="h-4 w-4" /> Download
                  </button>
                  <button 
                    onClick={handleClosePreview}
                    className="text-gray-500 hover:text-red-500 transition p-1"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  </button>
               </div>
            </div>

            {/* Content */}
            <div className="flex-1 bg-gray-100 overflow-auto flex items-center justify-center p-4">
              {isImage ? (
                 <img 
                   src={previewUrl} 
                   alt="Preview" 
                   className="max-w-full max-h-full object-contain shadow-md rounded" 
                 />
              ) : isPdf ? (
                 <iframe 
                   src={previewUrl}
                   className="w-full h-full border-none rounded shadow-sm bg-white"
                   title="PDF Preview" 
                 />
              ) : (
                <div className="text-center text-gray-500">
                   <p className="mb-2">Preview not available for this file type.</p>
                   <button 
                      onClick={() => window.open(downloadUrl, '_blank')}
                      className="text-blue-600 hover:underline"
                   >
                     Download to view
                   </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
