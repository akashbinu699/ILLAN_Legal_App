/**
 * Email Timeline Component
 * Add to frontend / src / components / EmailTimeline.tsx
 * 
 * Displays email history with navigation between multiple emails
 */
import { useState } from 'react';
import { ChevronLeft, ChevronRight, Mail, Calendar } from 'lucide-react';

interface EmailMessage {
    id: string;
    subject: string;
    body: string;
    from_email: string;
    created_at: string;
    gmail_message_id?: string;
}

interface EmailTimelineProps {
    emails: EmailMessage[];
}

export const EmailTimeline: React.FC<EmailTimelineProps> = ({ emails }) => {
    const [currentIndex, setCurrentIndex] = useState(0);

    if (!emails || emails.length === 0) {
        return (
            <div className="p-6 text-center text-gray-500 bg-white h-full flex flex-col items-center justify-center">
                <Mail className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No emails in timeline yet</p>
            </div>
        );
    }

    const currentEmail = emails[currentIndex];
    const totalEmails = emails.length;

    const formatDate = (dateStr: string) => {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateStr;
        }
    };

    const goToPrevious = () => {
        setCurrentIndex((prev) => Math.max(0, prev - 1));
    };

    const goToNext = () => {
        setCurrentIndex((prev) => Math.min(totalEmails - 1, prev + 1));
    };

    return (
        <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200 shadow-sm">
            {/* Header with Navigation */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50 flex-shrink-0">
                <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-green-600" />
                    <span className="font-semibold text-gray-700 text-sm">Case Emails</span>
                    <span className="text-xs text-gray-500 bg-gray-200 px-1.5 py-0.5 rounded-full">
                        {currentIndex + 1} / {totalEmails}
                    </span>
                </div>

                {totalEmails > 1 && (
                    <div className="flex items-center gap-2">
                        <button
                            onClick={goToPrevious}
                            disabled={currentIndex === 0}
                            className="p-1 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            title="Previous Email"
                        >
                            <ChevronLeft className="w-4 h-4" />
                        </button>

                        <button
                            onClick={goToNext}
                            disabled={currentIndex === totalEmails - 1}
                            className="p-1 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            title="Next Email"
                        >
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>

            {/* Email Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Email Meta Info */}
                <div className="space-y-1 pb-3 border-b border-gray-100 bg-white">
                    <h3 className="text-base font-bold text-gray-900 leading-tight">
                        {currentEmail.subject || '(No Subject)'}
                    </h3>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-600">
                        <div className="flex items-center gap-1.5 bg-gray-100 px-2 py-1 rounded">
                            <span className="font-medium text-gray-500">From:</span>
                            <span className="font-mono text-gray-800">{currentEmail.from_email}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-gray-500">
                            <Calendar className="w-3 h-3" />
                            <span>{formatDate(currentEmail.created_at)}</span>
                        </div>
                    </div>
                </div>

                {/* Email Body */}
                <div className="prose prose-sm max-w-none text-gray-800">
                    <div className="whitespace-pre-wrap font-sans leading-relaxed text-sm">
                        {currentEmail.body}
                    </div>
                </div>
            </div>

            {/* Quick Navigation (Timeline) */}
            {totalEmails > 1 && (
                <div className="px-3 py-2 border-t border-gray-200 bg-gray-50 flex-shrink-0 overflow-x-auto">
                    <div className="flex gap-2">
                        {emails.map((email, idx) => (
                            <button
                                key={email.id}
                                onClick={() => setCurrentIndex(idx)}
                                className={`flex-shrink-0 px-2 py-1.5 rounded border text-xs transition-all max-w-[150px] text-left group ${idx === currentIndex
                                        ? 'bg-green-50 border-green-500 text-green-900 shadow-sm ring-1 ring-green-500/20'
                                        : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
                                    }`}
                            >
                                <div className={`font-medium truncate ${idx === currentIndex ? 'text-green-700' : 'text-gray-700'}`}>
                                    {email.subject || 'No Subject'}
                                </div>
                                <div className="text-[10px] opacity-75 mt-0.5 truncate">
                                    {formatDate(email.created_at)}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
