import React, { useState } from 'react';
import type { Case } from '../types';
import { DocumentCard } from './DocumentCard';
import { UploadDropzone } from './UploadDropzone';
import { ChevronLeft, ChevronRight, Mail } from 'lucide-react';

interface CaseDescriptionPanelProps {
  caseData: Case;
  onDescriptionChange: (val: string) => void;
}

export const CaseDescriptionPanel: React.FC<CaseDescriptionPanelProps> = ({
  caseData,
  onDescriptionChange
}) => {
  const [description, setDescription] = useState(caseData.description);
  const [emailIndex, setEmailIndex] = useState(0);

  // Sync state with props
  React.useEffect(() => {
    setDescription(caseData.description);
    setEmailIndex(0); // Reset index on new case
  }, [caseData.description, caseData.id]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    if (val.length <= 1000) {
      setDescription(val);
      onDescriptionChange(val); 
    }
  };

  const hasEmails = caseData.emails && caseData.emails.length > 0;
  const currentEmail = hasEmails ? caseData.emails![emailIndex] : null;

  const handleNextEmail = () => {
    if (hasEmails && emailIndex < caseData.emails!.length - 1) {
      setEmailIndex(prev => prev + 1);
    }
  };

  const handlePrevEmail = () => {
    if (hasEmails && emailIndex > 0) {
      setEmailIndex(prev => prev - 1);
    }
  };
  
  const formatDate = (dateStr?: string) => {
      if (!dateStr) return '';
      try {
          return new Date(dateStr).toLocaleDateString();
      } catch (e) { return dateStr; }
  };

  // Helper to hide generic subjects
  const isGenericSubject = (subject?: string) => {
      if (!subject) return true;
      const lower = subject.toLowerCase();
      return lower.includes('new case #') || lower.includes('formulaire simplifié');
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6 overflow-y-auto">
      <div>
        <div className="flex items-center justify-between mb-3">
            {hasEmails ? (
                <div className="flex items-center gap-3">
                   <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                     <Mail className="w-5 h-5 text-gray-500" />
                     Email {emailIndex + 1}
                     <span className="text-sm font-normal text-gray-500">of {caseData.emails!.length}</span>
                   </h2>
                   
                   {/* Navigation Arrows */}
                   <div className="flex bg-gray-100 rounded-lg p-1 gap-1">
                      <button 
                        onClick={handlePrevEmail}
                        disabled={emailIndex === 0}
                        className="p-1 rounded hover:bg-white disabled:opacity-30 transition-all shadow-sm disabled:shadow-none"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={handleNextEmail}
                        disabled={emailIndex === caseData.emails!.length - 1}
                        className="p-1 rounded hover:bg-white disabled:opacity-30 transition-all shadow-sm disabled:shadow-none"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                   </div>
                </div>
            ) : (
                <h2 className="text-lg font-bold text-gray-900">Case description</h2>
            )}
        </div>

        <div className="relative">
          {hasEmails && currentEmail ? (
             <div className="w-full h-80 p-4 border border-gray-200 rounded-xl bg-white overflow-y-auto shadow-sm">
                <div className="mb-4 pb-3 border-b border-gray-100">
                    {!isGenericSubject(currentEmail.subject) && (
                        <div className="font-semibold text-gray-900 text-lg mb-1">{currentEmail.subject}</div>
                    )}
                    <div className="flex justify-between text-xs text-gray-500">
                        <span>From: {currentEmail.from_email}</span>
                        <span>{formatDate(currentEmail.created_at)}</span>
                    </div>
                </div>
                <div className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed font-sans">
                    {currentEmail.body}
                </div>
             </div>
          ) : (
            <>
              <textarea
                value={description}
                onChange={handleChange}
                placeholder="Describe the case..."
                className="w-full h-48 p-4 border border-green-500 rounded-xl focus:border-green-600 focus:ring-1 focus:ring-green-600 focus:outline-none resize-none text-green-800"
              />
              <div className="absolute bottom-3 right-4 text-xs text-green-600 font-medium">
                {description.length.toLocaleString()}/1,000
              </div>
            </>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Files & Attachments</h3>
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
