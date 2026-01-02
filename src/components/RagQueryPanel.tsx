import React, { useState } from 'react';
import { Send, User, Bot, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import type { Case } from '../types';
import { cn } from '../utils/cn';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

interface RagQueryPanelProps {
    caseData: Case;
}

export const RagQueryPanel: React.FC<RagQueryPanelProps> = ({ caseData }) => {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleSend = async () => {
        if (!query.trim()) return;

        const userMessage = { role: 'user' as const, content: query };
        setMessages(prev => [...prev, userMessage]);
        setQuery('');
        setIsLoading(true);

        try {
            const result = await api.query(query, caseData.caseNumber);
            const assistantMessage = {
                role: 'assistant' as const,
                content: result.response
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (err) {
            console.error("Query failed", err);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "Sorry, I encountered an error while processing your request."
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 text-center px-10">
                        <Bot className="h-12 w-12 mb-4 opacity-20" />
                        <p className="text-lg font-medium text-gray-500">Legal Assistant</p>
                        <p className="text-sm">Ask questions about this case's documents and legal context.</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={cn(
                            "flex gap-3 max-w-[85%]",
                            msg.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
                        )}
                    >
                        <div className={cn(
                            "w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center",
                            msg.role === 'user' ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                        )}>
                            {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                        </div>
                        <div className={cn(
                            "px-4 py-2 rounded-2xl text-sm shadow-sm",
                            msg.role === 'user'
                                ? "bg-green-600 text-white rounded-tr-none"
                                : "bg-gray-100 text-gray-800 rounded-tl-none border border-gray-200"
                        )}>
                            {msg.content}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex gap-3 mr-auto max-w-[85%]">
                        <div className="w-8 h-8 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center animate-pulse">
                            <Bot className="h-4 w-4" />
                        </div>
                        <div className="px-4 py-3 rounded-2xl bg-gray-100 border border-gray-200 rounded-tl-none overflow-hidden">
                            <div className="flex gap-1">
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-gray-100">
                <div className="relative flex items-center">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask the legal assistant..."
                        disabled={isLoading}
                        className="w-full bg-gray-50 border border-gray-200 rounded-full py-3 pl-5 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all disabled:opacity-50"
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !query.trim()}
                        className="absolute right-2 p-1.5 bg-green-600 text-white rounded-full hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                        {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                    </button>
                </div>
                <p className="text-[10px] text-gray-400 mt-2 text-center uppercase tracking-wider font-semibold">
                    AI generated response • Always verify with original documents
                </p>
            </div>
        </div>
    );
};
