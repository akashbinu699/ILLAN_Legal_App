"""
Email Timeline Component
Add to frontend / src / components / EmailTimeline.tsx

Displays email history with navigation between multiple emails
"""
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
            <div className="p-6 text-center text-gray-500">
                <Mail className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No emails in timeline yet</p>
            </div>
        );
    }

    const currentEmail = emails[currentIndex];
    const totalEmails = emails.length;

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const goToPrevious = () => {
        setCurrentIndex((prev) => Math.max(0, prev - 1));
    };

    const goToNext = () => {
        setCurrentIndex((prev) => Math.min(totalEmails - 1, prev + 1));
    };

    return (
        <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200">
            {/* Header with Navigation */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center gap-2">
                    <Mail className="w-5 h-5 text-green-600" />
                    <span className="font-semibold text-gray-900">Email Timeline</span>
                    <span className="text-sm text-gray-500">
                        ({currentIndex + 1} / {totalEmails})
                    </span>
                </div>

                {totalEmails > 1 && (
                    <div className="flex items-center gap-2">
                        <button
                            onClick={goToPrevious}
                            disabled={currentIndex === 0}
                            className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            aria-label="Previous email"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </button>

                        {/* Email index dots */}
                        <div className="flex gap-1">
                            {emails.map((_, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => setCurrentIndex(idx)}
                                    className={`w-2 h-2 rounded-full transition-colors ${idx === currentIndex
                                            ? 'bg-green-600 w-4'
                                            : 'bg-gray-300 hover:bg-gray-400'
                                        }`}
                                    aria-label={`Go to email ${idx + 1}`}
                                />
                            ))}
                        </div>

                        <button
                            onClick={goToNext}
                            disabled={currentIndex === totalEmails - 1}
                            className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            aria-label="Next email"
                        >
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>
                )}
            </div>

            {/* Email Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Email Meta Info */}
                <div className="space-y-2 pb-4 border-b border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-900">
                        {currentEmail.subject || 'No Subject'}
                    </h3>

                    <div className="flex items-center gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1.5">
                            <Mail className="w-4 h-4" />
                            <span>{currentEmail.from_email}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <Calendar className="w-4 h-4" />
                            <span>{formatDate(currentEmail.created_at)}</span>
                        </div>
                    </div>
                </div>

                {/* Email Body */}
                <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed">
                        {currentEmail.body}
                    </pre>
                </div>
            </div>

            {/* Quick Navigation (Timeline) */}
            {totalEmails > 1 && (
                <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
                    <div className="text-xs text-gray-500 mb-2">Quick Jump:</div>
                    <div className="flex gap-2 overflow-x-auto">
                        {emails.map((email, idx) => (
                            <button
                                key={email.id}
                                onClick={() => setCurrentIndex(idx)}
                                className={`flex-shrink-0 px-3 py-2 rounded text-xs transition-colors ${idx === currentIndex
                                        ? 'bg-green-600 text-white font-medium'
                                        : 'bg-white border border-gray-200 text-gray-700 hover:border-green-400'
                                    }`}
                            >
                                <div className="font-medium truncate max-w-[120px]">
                                    {email.subject || 'No Subject'}
                                </div>
                                <div className="text-xs opacity-75 mt-0.5">
                                    {formatDate(email.created_at).split(',')[0]}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
