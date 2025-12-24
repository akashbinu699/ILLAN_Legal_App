import React, { useState, useEffect } from 'react';
import { apiClient, ApiQueryResponse, QueryHistory } from '../services/apiClient';

interface QueryInterfaceProps {
    caseId?: string;
}

export const QueryInterface: React.FC<QueryInterfaceProps> = ({ caseId }) => {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState<ApiQueryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);
    
    // Load query history on mount and when caseId changes
    useEffect(() => {
        if (caseId) {
            loadQueryHistory();
        } else {
            setQueryHistory([]);
        }
    }, [caseId]);
    
    const loadQueryHistory = async () => {
        if (!caseId) return;
        setLoadingHistory(true);
        try {
            const history = await apiClient.getCaseQueries(caseId);
            setQueryHistory(history);
            
            // If there's a most recent query, show it
            if (history.length > 0 && !response) {
                const latest = history[0];
                setQuery(latest.query_text);
                setResponse({
                    response: latest.response_text,
                    citations: latest.citations || [],
                    retrieved_chunks: latest.retrieved_chunk_ids?.length || 0,
                    query_id: latest.id
                });
                setSelectedHistoryId(latest.id);
            }
        } catch (err) {
            console.error("Failed to load query history:", err);
        } finally {
            setLoadingHistory(false);
        }
    };
    
    const handleSelectHistory = (historyItem: QueryHistory) => {
        setQuery(historyItem.query_text);
        setResponse({
            response: historyItem.response_text,
            citations: historyItem.citations || [],
            retrieved_chunks: historyItem.retrieved_chunk_ids?.length || 0,
            query_id: historyItem.id
        });
        setSelectedHistoryId(historyItem.id);
        setError(null);
    };

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
            setSelectedHistoryId(result.query_id);
            
            // Reload query history to include the new query
            if (caseId) {
                await loadQueryHistory();
            }
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

            {queryHistory.length > 0 && (
                <div className="mb-4 bg-gray-50 p-4 rounded border border-gray-200">
                    <h3 className="text-sm font-bold text-gray-700 mb-2 flex items-center">
                        <i className="fas fa-history mr-2"></i>
                        Query History ({queryHistory.length})
                    </h3>
                    <div className="max-h-40 overflow-y-auto space-y-1">
                        {queryHistory.map((item) => (
                            <button
                                key={item.id}
                                onClick={() => handleSelectHistory(item)}
                                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                                    selectedHistoryId === item.id
                                        ? 'bg-brand-red text-white'
                                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="truncate flex-1">{item.query_text}</span>
                                    <span className="text-xs ml-2 opacity-70">
                                        {new Date(item.created_at).toLocaleString()}
                                    </span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            )}

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

