import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mail, Download, Maximize2, X } from 'lucide-react';
import { cn } from '../utils/cn';

interface AiDraftPanelProps {
  mode: 'email' | 'letter';
  inputContent: string;
  onInputChange: (val: string) => void;
  outputContent: string;
  onOutputChange: (val: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export const AiDraftPanel: React.FC<AiDraftPanelProps> = ({
  inputContent,
  onInputChange,
  outputContent,
  onOutputChange,
  onGenerate,
  isGenerating
}) => {
  // Maximised state
  const [maximisedPanel, setMaximisedPanel] = useState<'none' | 'input' | 'output'>('none');
  // Resize state
  const [inputWidthPercent, setInputWidthPercent] = useState(50);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  const handleToggleMaximise = (panel: 'input' | 'output') => {
    if (maximisedPanel === panel) {
      setMaximisedPanel('none');
    } else {
      setMaximisedPanel(panel);
    }
  };

  // Resize Handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging.current || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const newLeftWidth = e.clientX - containerRect.left;
    const newPercent = (newLeftWidth / containerRect.width) * 100;

    // Constraints (e.g. min 20% max 80%)
    if (newPercent > 20 && newPercent < 80) {
      setInputWidthPercent(newPercent);
    }
  }, []);

  const handleMouseUp = useCallback(() => {
    isDragging.current = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = '';
  }, [handleMouseMove]);

  // Clean up
  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  return (
    <div className="h-full flex flex-col p-4 overflow-hidden relative">
      <div
        ref={containerRef}
        className="flex-1 flex min-h-0 relative"
      >
        {/* Input Column */}
        <div
          className={cn(
            "flex flex-col min-w-0 transition-all duration-300 pr-2", // Added PR for spacing if needed, but flex gap handles it usually. Wait, replaced Gap with custom handle.
            maximisedPanel === 'output' && "hidden"
          )}
          style={{
            width: maximisedPanel === 'input' ? '100%' : (maximisedPanel === 'none' ? `${inputWidthPercent}%` : '0px'),
            display: maximisedPanel === 'output' ? 'none' : 'flex'
          }}
        >
          <div className="flex justify-between items-center mb-1">
            <h3 className="font-bold text-gray-900">Input</h3>
          </div>
          <div className="flex-1 border border-gray-200 rounded-xl bg-white relative group flex flex-col overflow-hidden">
            <button
              onClick={() => handleToggleMaximise('input')}
              className="absolute top-2 right-2 p-1.5 text-gray-400 hover:text-gray-600 bg-white/50 hover:bg-white rounded transition-colors z-20"
              title={maximisedPanel === 'input' ? "Restore view" : "Maximise input"}
            >
              {maximisedPanel === 'input' ? <X className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
            {/* Input Input Scroll: default (Right) */}
            <div className="flex-1 overflow-y-auto relative h-full">
              <textarea
                className="w-full h-full resize-none border-none focus:ring-0 text-sm font-mono text-gray-800 bg-transparent p-4 block"
                value={inputContent}
                onChange={(e) => onInputChange(e.target.value)}
                style={{ minHeight: '100%' }}
              />
            </div>

          </div>
        </div>

        {/* Resizer Handle */}
        {maximisedPanel === 'none' && (
          <div
            className="w-4 flex items-center justify-center cursor-col-resize hover:bg-gray-50 active:bg-blue-50 transition-colors z-30 select-none flex-shrink-0 -ml-2 -mr-2"
            onMouseDown={handleMouseDown}
          >
            <div className="w-1 h-8 bg-gray-300 rounded-full"></div>
          </div>
        )}

        {/* Output Column */}
        <div
          className={cn(
            "flex flex-col min-w-0 transition-all duration-300 pl-2",
            maximisedPanel === 'input' && "hidden"
          )}
          style={{
            flex: 1, // Output takes remaining space
            display: maximisedPanel === 'input' ? 'none' : 'flex'
          }}
        >
          <div className="flex justify-between items-center mb-1">
            <h3 className="font-bold text-gray-900">Output</h3>
            <div className="flex gap-2">
              {/* NEW: GEN AI BUTTON */}
              <button
                onClick={onGenerate}
                disabled={isGenerating}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
                  isGenerating && "animate-pulse"
                )}
              >
                {isGenerating ? (
                  <>Processing...</>
                ) : (
                  <>
                    <span className="text-lg leading-none">✨</span> Generate
                  </>
                )}
              </button>

              <button className="text-gray-500 hover:text-green-700 bg-gray-50 p-1.5 rounded transition-colors">
                <Mail className="h-4 w-4" />
              </button>
              <button className="text-gray-500 hover:text-green-700 bg-gray-50 p-1.5 rounded transition-colors">
                <Download className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="flex-1 border border-gray-200 rounded-xl bg-white shadow-sm relative group flex flex-col overflow-hidden">
            <button
              onClick={() => handleToggleMaximise('output')}
              className="absolute top-2 right-2 p-1.5 text-gray-400 hover:text-gray-600 bg-white/50 hover:bg-white rounded transition-colors z-20"
              title={maximisedPanel === 'output' ? "Restore view" : "Maximise output"}
            >
              {maximisedPanel === 'output' ? <X className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
            {/* Output Scroll: Left side (RTL wrapper) */}
            <div
              className="flex-1 w-full relative overflow-y-auto"
              style={{ direction: 'rtl' }}
            >
              <div style={{ direction: 'ltr' }} className="min-h-full">
                <textarea
                  className="w-full h-full resize-none border-none focus:ring-0 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap font-sans bg-transparent p-6 overflow-hidden block"
                  value={outputContent}
                  onChange={(e) => onOutputChange(e.target.value)}
                  style={{ minHeight: '100%', height: 'auto' }}
                  rows={Math.max(10, outputContent.split('\n').length)}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
