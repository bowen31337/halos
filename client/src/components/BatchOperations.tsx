import React, { useState, useCallback } from 'react';
import { Check, X, Download, Trash2, Archive, Pin, FolderOpen, Loader2 } from 'lucide-react';

interface BatchOperationsProps {
  selectedIds: string[];
  onClearSelection: () => void;
  onOperationComplete: (result: BatchResult) => void;
}

interface BatchResult {
  success: boolean;
  operation: string;
  total_requested: number;
  total_processed: number;
  successful: string[];
  failed: Array<[string, string]>;
  processing_time_seconds: number;
}

type BatchOperation = 'export' | 'delete' | 'archive' | 'unarchive' | 'pin' | 'unpin';

export const BatchOperations: React.FC<BatchOperationsProps> = ({
  selectedIds,
  onClearSelection,
  onOperationComplete
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [currentOperation, setCurrentOperation] = useState<BatchOperation | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'markdown' | 'csv'>('json');
  const [progress, setProgress] = useState(0);

  const handleBatchOperation = useCallback(async (operation: BatchOperation) => {
    if (selectedIds.length === 0) return;

    // Show confirmation for destructive operations
    if (operation === 'delete') {
      setCurrentOperation(operation);
      setShowConfirm(true);
      return;
    }

    await executeOperation(operation);
  }, [selectedIds]);

  const executeOperation = useCallback(async (operation: BatchOperation) => {
    setIsLoading(true);
    setCurrentOperation(operation);
    setProgress(0);

    try {
      if (operation === 'export') {
        // Handle export separately (different endpoint)
        await handleExport();
      } else {
        const response = await fetch('/api/batch/conversations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_ids: selectedIds,
            operation: operation
          })
        });

        if (!response.ok) {
          throw new Error(`Operation failed: ${response.statusText}`);
        }

        const result: BatchResult = await response.json();
        setProgress(100);
        onOperationComplete(result);

        // Clear selection on successful operation
        if (result.success) {
          onClearSelection();
        }
      }
    } catch (error) {
      console.error('Batch operation error:', error);
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
      setCurrentOperation(null);
      setProgress(0);
      setShowConfirm(false);
    }
  }, [selectedIds, onClearSelection, onOperationComplete]);

  const handleExport = useCallback(async () => {
    try {
      const response = await fetch(`/api/batch/conversations/export?conversation_ids=${selectedIds.join(',')}&export_format=${exportFormat}`);

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      const result = await response.json();

      // If file_url is provided, trigger download
      if (result.file_url) {
        window.open(result.file_url, '_blank');
      }

      // If file_data is provided (base64), trigger download
      if (result.file_data) {
        const binaryString = atob(result.file_data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `batch_export_${exportFormat}_${Date.now()}.${exportFormat}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }

      onOperationComplete(result);
      onClearSelection();
    } catch (error) {
      console.error('Export error:', error);
      throw error;
    }
  }, [selectedIds, exportFormat, onOperationComplete, onClearSelection]);

  const operationButtons = [
    { op: 'archive' as BatchOperation, icon: Archive, label: 'Archive', color: 'bg-blue-500 hover:bg-blue-600' },
    { op: 'unarchive' as BatchOperation, icon: FolderOpen, label: 'Unarchive', color: 'bg-gray-500 hover:bg-gray-600' },
    { op: 'pin' as BatchOperation, icon: Pin, label: 'Pin', color: 'bg-amber-500 hover:bg-amber-600' },
    { op: 'export' as BatchOperation, icon: Download, label: 'Export', color: 'bg-green-500 hover:bg-green-600' },
    { op: 'delete' as BatchOperation, icon: Trash2, label: 'Delete', color: 'bg-red-500 hover:bg-red-600' },
  ];

  if (selectedIds.length === 0) {
    return null;
  }

  return (
    <>
      {/* Batch Operations Bar */}
      <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
        <div className="bg-gray-900 dark:bg-gray-800 text-white rounded-lg shadow-xl p-4 flex items-center gap-4">
          {/* Selection Count */}
          <div className="flex items-center gap-2 border-r border-gray-600 pr-4">
            <span className="text-sm font-medium">
              {selectedIds.length} {selectedIds.length === 1 ? 'conversation' : 'conversations'} selected
            </span>
          </div>

          {/* Operation Buttons */}
          <div className="flex items-center gap-2">
            {operationButtons.map(({ op, icon: Icon, label, color }) => (
              <button
                key={op}
                onClick={() => handleBatchOperation(op)}
                disabled={isLoading}
                className={`
                  ${color} ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
                  px-3 py-2 rounded-lg flex items-center gap-2 text-sm font-medium
                  transition-all duration-200
                `}
                title={label}
              >
                {isLoading && currentOperation === op ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}

            {/* Export Format Selector (shows when export is hovered/clicked) */}
            {currentOperation === 'export' && !showConfirm && (
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as any)}
                className="bg-gray-700 text-white px-2 py-2 rounded text-sm"
                disabled={isLoading}
              >
                <option value="json">JSON</option>
                <option value="markdown">Markdown</option>
                <option value="csv">CSV</option>
              </select>
            )}
          </div>

          {/* Clear Selection */}
          <button
            onClick={onClearSelection}
            disabled={isLoading}
            className="ml-2 text-gray-400 hover:text-white transition-colors"
            title="Clear selection"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Indicator */}
        {isLoading && progress > 0 && (
          <div className="mt-2 bg-gray-800 rounded-full h-1 overflow-hidden">
            <div
              className="bg-blue-500 h-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      {showConfirm && currentOperation === 'delete' && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
              Delete {selectedIds.length} {selectedIds.length === 1 ? 'Conversation' : 'Conversations'}?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              This action cannot be undone. Are you sure you want to delete the selected conversations?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowConfirm(false);
                  setCurrentOperation(null);
                }}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => executeOperation('delete')}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Result Display Component
export const BatchOperationResult: React.FC<{
  result: BatchResult;
  onClose: () => void;
}> = ({ result, onClose }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="fixed top-4 right-4 z-50 max-w-md w-full">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            {result.success ? (
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                <Check className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            ) : (
              <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900 rounded-full flex items-center justify-center">
                <X className="w-6 h-6 text-amber-600 dark:text-amber-400" />
              </div>
            )}
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {result.success ? 'Operation Complete' : 'Operation Partially Failed'}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {result.operation.charAt(0).toUpperCase() + result.operation.slice(1)}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Total requested:</span>
            <span className="font-medium text-gray-900 dark:text-white">{result.total_requested}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Successful:</span>
            <span className="font-medium text-green-600 dark:text-green-400">{result.successful.length}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Failed:</span>
            <span className="font-medium text-red-600 dark:text-red-400">{result.failed.length}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Processing time:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {result.processing_time_seconds.toFixed(2)}s
            </span>
          </div>
        </div>

        {result.failed.length > 0 && (
          <details className="mb-4">
            <summary
              className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer hover:text-gray-900 dark:hover:text-white"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? 'Hide' : 'Show'} failed items
            </summary>
            {showDetails && (
              <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
                {result.failed.map(([id, error]) => (
                  <div
                    key={id}
                    className="text-xs bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 p-2 rounded"
                  >
                    <span className="font-mono">{id.slice(0, 8)}...</span>: {error}
                  </div>
                ))}
              </div>
            )}
          </details>
        )}

        <button
          onClick={onClose}
          className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg transition-colors font-medium"
        >
          Close
        </button>
      </div>
    </div>
  );
};
