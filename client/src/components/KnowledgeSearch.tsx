import React, { useState, useCallback, useEffect } from 'react';
import { Search, File, FileText, Database, X, Filter } from 'lucide-react';

interface SearchResult {
  id: string;
  filename: string;
  project_id: string;
  file_size: number;
  content_type: string | null;
  content_preview: string;
  created_at: string;
  updated_at: string;
}

interface KnowledgeSearchProps {
  projectId?: string;
  onFileSelect?: (fileId: string) => void;
  className?: string;
}

export const KnowledgeSearch: React.FC<KnowledgeSearchProps> = ({
  projectId,
  onFileSelect,
  className = '',
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [contentType, setContentType] = useState<string>('all');

  const searchKnowledgeBase = useCallback(async (searchQuery: string) => {
    if (!searchQuery || searchQuery.length < 2) {
      setResults([]);
      setTotal(0);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({ q: searchQuery });
      if (projectId) params.append('project_id', projectId);

      const response = await fetch(`/api/search/knowledge?${params}`);
      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setResults(data.files || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      searchKnowledgeBase(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query, searchKnowledgeBase]);

  const handleClear = () => {
    setQuery('');
    setResults([]);
    setTotal(0);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (contentType: string | null) => {
    if (!contentType) return <File className="w-5 h-5" />;
    if (contentType.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />;
    if (contentType.includes('text')) return <FileText className="w-5 h-5 text-blue-500" />;
    if (contentType.includes('image')) return <File className="w-5 h-5 text-green-500" />;
    return <Database className="w-5 h-5 text-gray-500" />;
  };

  const filteredResults = results.filter(file => {
    if (contentType === 'all') return true;
    if (!file.content_type) return contentType === 'other';
    if (contentType === 'pdf') return file.content_type.includes('pdf');
    if (contentType === 'text') return file.content_type.includes('text');
    if (contentType === 'image') return file.content_type.includes('image');
    return true;
  });

  return (
    <div className={`knowledge-search ${className}`}>
      {/* Search Header */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-lg font-semibold">Knowledge Base Search</h3>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            title="Toggle filters"
          >
            <Filter className="w-4 h-4" />
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search in project files and documents..."
            className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          />
          {query && (
            <button
              onClick={handleClear}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => setContentType('all')}
              className={`px-3 py-1 text-sm rounded ${
                contentType === 'all'
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setContentType('pdf')}
              className={`px-3 py-1 text-sm rounded ${
                contentType === 'pdf'
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              PDFs
            </button>
            <button
              onClick={() => setContentType('text')}
              className={`px-3 py-1 text-sm rounded ${
                contentType === 'text'
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              Text
            </button>
            <button
              onClick={() => setContentType('image')}
              className={`px-3 py-1 text-sm rounded ${
                contentType === 'image'
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              Images
            </button>
          </div>
        )}

        {/* Results Count */}
        {query && !loading && (
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Found {total} {total === 1 ? 'file' : 'files'}
          </p>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
        </div>
      )}

      {/* Search Results */}
      <div className="space-y-2">
        {filteredResults.map((file) => (
          <div
            key={file.id}
            onClick={() => onFileSelect?.(file.id)}
            className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-orange-500 dark:hover:border-orange-500 cursor-pointer transition-colors"
          >
            <div className="flex items-start gap-3">
              <div className="mt-1 flex-shrink-0">
                {getFileIcon(file.content_type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {file.filename}
                  </h4>
                  <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                    {formatFileSize(file.file_size)}
                  </span>
                </div>

                {/* Content Preview */}
                {file.content_preview && (
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                    {file.content_preview}
                  </p>
                )}

                {/* Metadata */}
                <div className="mt-2 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                  {file.content_type && (
                    <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
                      {file.content_type.split('/')[1]?.toUpperCase() || 'FILE'}
                    </span>
                  )}
                  <span>
                    {new Date(file.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Empty State */}
        {query && !loading && filteredResults.length === 0 && (
          <div className="py-8 text-center">
            <Database className="mx-auto w-12 h-12 text-gray-400 mb-2" />
            <p className="text-gray-600 dark:text-gray-400">
              No documents found for "{query}"
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
              Try different keywords or check your filters
            </p>
          </div>
        )}

        {/* Initial State */}
        {!query && (
          <div className="py-8 text-center">
            <Search className="mx-auto w-12 h-12 text-gray-400 mb-2" />
            <p className="text-gray-600 dark:text-gray-400">
              Search your project knowledge base
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
              Find files, documents, and extracted content
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeSearch;
