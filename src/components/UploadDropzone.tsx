import React, { useCallback } from 'react';
import { Upload } from 'lucide-react';
import { cn } from '../utils/cn';

interface UploadDropzoneProps {
  onFilesSelected: (files: FileList) => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onFilesSelected }) => {
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        onFilesSelected(e.dataTransfer.files);
      }
    },
    [onFilesSelected]
  );

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className={cn(
        "w-full border-2 border-dashed border-green-300 rounded-xl p-8",
        "flex flex-col items-center justify-center text-center cursor-pointer",
        "hover:bg-green-50 transition-colors bg-white shadow-[0px_4px_10px_rgba(0,0,0,0.05)]"
      )}
      onClick={() => document.getElementById('file-upload')?.click()}
    >
      <input
        id="file-upload"
        type="file"
        multiple
        className="hidden"
        onChange={(e) => e.target.files && onFilesSelected(e.target.files)}
      />
      
      <div className="mb-3 p-3 bg-green-100 rounded-full">
         <Upload className="h-8 w-8 text-green-500" />
      </div>
      
      <h3 className="text-lg font-semibold text-gray-800 mb-1">
        Copy of letters from your CAF
      </h3>
      <p className="text-sm text-green-600 font-medium">
        PDF or clear photos. You can also click to select a file.
      </p>
    </div>
  );
};
