import React, { useState } from 'react';
import type { Case } from '../types';
import { DocumentCard } from './DocumentCard';
import { UploadDropzone } from './UploadDropzone';

interface CaseDescriptionPanelProps {
  caseData: Case;
  onDescriptionChange: (val: string) => void;
}

export const CaseDescriptionPanel: React.FC<CaseDescriptionPanelProps> = ({
  caseData,
  onDescriptionChange
}) => {
  const [description, setDescription] = useState(caseData.description);

  // Fix: Sync local state with prop changes when user switches cases
  React.useEffect(() => {
    setDescription(caseData.description);
  }, [caseData.description, caseData.id]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    if (val.length <= 1000) {
      setDescription(val);
      onDescriptionChange(val); // In a real app, might debounce
    }
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6 overflow-y-auto">
      <div>
        <h2 className="text-lg font-bold text-gray-900 mb-3">Case description</h2>
        <div className="relative">
          <textarea
            value={description}
            onChange={handleChange}
            placeholder="Describe the case..."
            className="w-full h-48 p-4 border border-green-500 rounded-xl focus:border-green-600 focus:ring-1 focus:ring-green-600 focus:outline-none resize-none text-green-800"
          />
          <div className="absolute bottom-3 right-4 text-xs text-green-600 font-medium">
            {description.length.toLocaleString()}/1,000
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Files & Attachments</h3>
        {/* Horizontal scroll documents */}
        <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-green-200 scrollbar-track-transparent">
          {caseData.documents.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
        </div>
      </div>

      <div className="pb-10">
        <UploadDropzone onFilesSelected={(files) => console.log(files)} />
      </div>
    </div>
  );
};
