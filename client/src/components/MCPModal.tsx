import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Edit2, CheckCircle, XCircle, Loader2, Server, Zap } from 'lucide-react';
import { api } from '../services/api';

interface MCPServer {
  id: string;
  name: string;
  server_type: string;
  config: Record<string, any>;
  description?: string;
  is_active: boolean;
  health_status?: string;
  last_health_check?: string;
  available_tools: string[];
  usage_count: number;
}

interface ServerType {
  type: string;
  label: string;
  description: string;
  config_fields: string[];
}

interface MCPModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MCPModal: React.FC<MCPModalProps> = ({ isOpen, onClose }) => {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [serverTypes, setServerTypes] = useState<ServerType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [testingServerId, setTestingServerId] = useState<string | null>(null);

  // Form state
  const [formState, setFormState] = useState({
    name: '',
    server_type: 'filesystem',
    description: '',
    config: {} as Record<string, any>,
  });

  const [editingServer, setEditingServer] = useState<MCPServer | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadServers();
      loadServerTypes();
    }
  }, [isOpen]);

  const loadServers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listMCPServers();
      setServers(data);
    } catch (err) {
      setError('Failed to load MCP servers');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadServerTypes = async () => {
    try {
      const data = await api.listMCPServerTypes();
      setServerTypes(data);
    } catch (err) {
      console.error('Failed to load server types');
    }
  };

  const handleCreateServer = async () => {
    setIsLoading(true);
    try {
      await api.createMCPServer(formState);
      await loadServers();
      setIsCreating(false);
      resetForm();
    } catch (err) {
      setError('Failed to create server');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateServer = async () => {
    if (!editingServer) return;

    setIsLoading(true);
    try {
      await api.updateMCPServer(editingServer.id, {
        name: formState.name,
        config: formState.config,
        description: formState.description,
      });
      await loadServers();
      setEditingServer(null);
      resetForm();
    } catch (err) {
      setError('Failed to update server');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteServer = async (serverId: string) => {
    if (!confirm('Are you sure you want to delete this server?')) return;

    setIsLoading(true);
    try {
      await api.deleteMCPServer(serverId);
      await loadServers();
    } catch (err) {
      setError('Failed to delete server');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestServer = async (serverId: string) => {
    setTestingServerId(serverId);
    try {
      const result = await api.testMCPServer(serverId);
      alert(result.message);
      await loadServers(); // Reload to get updated health status
    } catch (err) {
      setError('Failed to test server');
      console.error(err);
    } finally {
      setTestingServerId(null);
    }
  };

  const resetForm = () => {
    setFormState({
      name: '',
      server_type: 'filesystem',
      description: '',
      config: {},
    });
    setIsCreating(false);
    setEditingServer(null);
  };

  const handleEditClick = (server: MCPServer) => {
    setEditingServer(server);
    setFormState({
      name: server.name,
      server_type: server.server_type,
      description: server.description || '',
      config: server.config,
    });
    setIsCreating(true);
  };

  const getServerTypeLabel = (type: string) => {
    const serverType = serverTypes.find(st => st.type === type);
    return serverType?.label || type;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-[var(--background)] rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[var(--border)]">
          <div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">MCP Servers</h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Manage Model Context Protocol servers for external tool integrations
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--surface)] rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-[var(--text-secondary)]" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm">
              {error}
            </div>
          )}

          {!isCreating ? (
            <>
              {/* Server List */}
              <div className="mb-6">
                <button
                  onClick={() => setIsCreating(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary)]/90 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Add Server
                </button>
              </div>

              {isLoading && servers.length === 0 ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
                </div>
              ) : servers.length === 0 ? (
                <div className="text-center py-12">
                  <Server className="w-12 h-12 text-[var(--text-secondary)] mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">No MCP Servers</h3>
                  <p className="text-[var(--text-secondary)] mb-4">
                    Add your first MCP server to enable external tool integrations
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {servers.map((server) => (
                    <div
                      key={server.id}
                      className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-lg"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-medium text-[var(--text-primary)]">{server.name}</h3>
                            {server.is_active ? (
                              <span className="flex items-center gap-1 text-xs px-2 py-1 bg-green-500/20 text-green-500 rounded-full">
                                <CheckCircle className="w-3 h-3" />
                                Active
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-xs px-2 py-1 bg-gray-500/20 text-gray-500 rounded-full">
                                <XCircle className="w-3 h-3" />
                                Inactive
                              </span>
                            )}
                            {server.health_status === 'healthy' && (
                              <span className="flex items-center gap-1 text-xs px-2 py-1 bg-green-500/20 text-green-500 rounded-full">
                                <CheckCircle className="w-3 h-3" />
                                Healthy
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-[var(--text-secondary)] mb-2">
                            {getServerTypeLabel(server.server_type)}
                          </p>
                          {server.description && (
                            <p className="text-sm text-[var(--text-secondary)] mb-2">
                              {server.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-xs text-[var(--text-secondary)]">
                            <span>{server.available_tools?.length || 0} tools</span>
                            <span>Used {server.usage_count} times</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleTestServer(server.id)}
                            disabled={testingServerId === server.id}
                            className="p-2 hover:bg-[var(--background)] rounded-lg transition-colors"
                            title="Test connection"
                          >
                            {testingServerId === server.id ? (
                              <Loader2 className="w-4 h-4 text-[var(--primary)] animate-spin" />
                            ) : (
                              <Zap className="w-4 h-4 text-[var(--text-secondary)]" />
                            )}
                          </button>
                          <button
                            onClick={() => handleEditClick(server)}
                            className="p-2 hover:bg-[var(--background)] rounded-lg transition-colors"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4 text-[var(--text-secondary)]" />
                          </button>
                          <button
                            onClick={() => handleDeleteServer(server.id)}
                            className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <>
              {/* Create/Edit Form */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-[var(--text-primary)] mb-4">
                    {editingServer ? 'Edit MCP Server' : 'Add MCP Server'}
                  </h3>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Server Name
                  </label>
                  <input
                    type="text"
                    value={formState.name}
                    onChange={(e) => setFormState({ ...formState, name: e.target.value })}
                    className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--text-primary)]"
                    placeholder="My Filesystem Server"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Server Type
                  </label>
                  <select
                    value={formState.server_type}
                    onChange={(e) => setFormState({ ...formState, server_type: e.target.value, config: {} })}
                    disabled={!!editingServer}
                    className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--text-primary)] disabled:opacity-50"
                  >
                    {serverTypes.map((type) => (
                      <option key={type.type} value={type.type}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-sm text-[var(--text-secondary)] mt-1">
                    {serverTypes.find(st => st.type === formState.server_type)?.description}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    value={formState.description}
                    onChange={(e) => setFormState({ ...formState, description: e.target.value })}
                    className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--text-primary)] resize-none"
                    rows={2}
                    placeholder="Describe what this server does..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Configuration
                  </label>
                  <div className="space-y-2">
                    {serverTypes.find(st => st.type === formState.server_type)?.config_fields.map((field) => (
                      <div key={field}>
                        <label className="block text-sm text-[var(--text-secondary)] mb-1">
                          {field.charAt(0).toUpperCase() + field.slice(1)}
                        </label>
                        <input
                          type="text"
                          value={formState.config[field] || ''}
                          onChange={(e) =>
                            setFormState({
                              ...formState,
                              config: { ...formState.config, [field]: e.target.value },
                            })
                          }
                          className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--text-primary)]"
                          placeholder={field}
                        />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={editingServer ? handleUpdateServer : handleCreateServer}
                    disabled={isLoading || !formState.name}
                    className="flex-1 px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary)]/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Saving...
                      </span>
                    ) : editingServer ? (
                      'Update Server'
                    ) : (
                      'Create Server'
                    )}
                  </button>
                  <button
                    onClick={resetForm}
                    className="px-4 py-2 border border-[var(--border)] text-[var(--text-primary)] rounded-lg hover:bg-[var(--surface)] transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
