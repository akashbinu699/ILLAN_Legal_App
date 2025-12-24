import React, { useState } from 'react';
import { apiClient, ApiQueryResponse } from '../services/apiClient';

interface QueryInterfaceProps {
    caseId?: string;
}

export const QueryInterface: React.FC<QueryInterfaceProps> = ({ caseId }) => {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState<ApiQueryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        setResponse(null);

        try {
            const result = await apiClient.queryRAG({
                query: query.trim(),
                case_id: caseId
            });
            setResponse(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-xl font-bold text-brand-dark mb-4">
                <i className="fas fa-search mr-2"></i>
                RAG Query Interface
            </h2>

            <form onSubmit={handleSubmit} className="mb-4">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Ask a question about the case documents..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-brand-red"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="bg-brand-red text-white px-6 py-2 rounded hover:bg-[#b01938] disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <span><i className="fas fa-spinner fa-spin mr-2"></i>Querying...</span>
                        ) : (
                            <span><i className="fas fa-paper-plane mr-2"></i>Query</span>
                        )}
                    </button>
                </div>
            </form>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                    <i className="fas fa-exclamation-circle mr-2"></i>
                    {error}
                </div>
            )}

            {response && (
                <div className="space-y-4">
                    <div className="bg-gray-50 p-4 rounded border border-gray-200">
                        <h3 className="font-bold text-gray-700 mb-2">Response:</h3>
                        <p className="text-gray-800 whitespace-pre-wrap">{response.response}</p>
                    </div>

                    {response.citations && response.citations.length > 0 && (
                        <div className="bg-blue-50 p-4 rounded border border-blue-200">
                            <h3 className="font-bold text-blue-700 mb-2">
                                <i className="fas fa-book mr-2"></i>
                                Citations ({response.citations.length}):
                            </h3>
                            <ul className="list-disc list-inside space-y-1">
                                {response.citations.map((citation, idx) => (
                                    <li key={idx} className="text-blue-800 text-sm">
                                        Document {citation.document_id}, Page {citation.page_number}
                                        {citation.section_title && `, ${citation.section_title}`}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="text-sm text-gray-500">
                        Retrieved {response.retrieved_chunks} chunks | Query ID: {response.query_id}
                    </div>
                </div>
            )}
        </div>
    );
};

