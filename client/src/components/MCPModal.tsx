import { useState, useEffect } from 'react'
import { useMCPStore, MCPServer } from '../stores/mcpStore'

interface MCPModalProps {
  onClose: () => void
}

type TabType = 'servers' | 'add' | 'types'

export function MCPModal({ onClose }: MCPModalProps) {
  const {
    servers,
    serverTypes,
    isLoading,
    error,
    fetchServers,
    fetchServerTypes,
    createServer,
    deleteServer,
    testServer,
    testConnection,
    getServerTools,
  } = useMCPStore()

  const [activeTab, setActiveTab] = useState<TabType>('servers')
  const [selectedServer, setSelectedServer] = useState<MCPServer | null>(null)
  const [serverTools, setServerTools] = useState<any>(null)

  // Form state for adding server
  const [formData, setFormData] = useState({
    name: '',
    server_type: '',
    config: {} as Record<string, any>,
    description: '',
  })

  // Test connection result
  const [testResult, setTestResult] = useState<any>(null)

  useEffect(() => {
    fetchServers()
    fetchServerTypes()
  }, [fetchServers, fetchServerTypes])

  const handleCreateServer = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createServer(formData)
      setFormData({ name: '', server_type: '', config: {}, description: '' })
      setTestResult(null)
      setActiveTab('servers')
    } catch (err) {
      // Error handled by store
    }
  }

  const handleTestConnection = async () => {
    if (!formData.server_type) return
    try {
      const result = await testConnection(formData.server_type, formData.config)
      setTestResult(result)
    } catch (err) {
      // Error handled by store
    }
  }

  const handleTestExistingServer = async (server: MCPServer) => {
    try {
      const result = await testServer(server.id)
      alert(`Server test result: ${result.status}\n${result.message}`)
    } catch (err) {
      // Error handled by store
    }
  }

  const handleGetServerTools = async (server: MCPServer) => {
    try {
      const result = await getServerTools(server.id)
      setServerTools(result)
      setSelectedServer(server)
    } catch (err) {
      // Error handled by store
    }
  }

  const handleDeleteServer = async (id: string) => {
    if (confirm('Are you sure you want to delete this MCP server?')) {
      try {
        await deleteServer(id)
        if (selectedServer?.id === id) {
          setSelectedServer(null)
          setServerTools(null)
        }
      } catch (err) {
        // Error handled by store
      }
    }
  }

  const updateConfigField = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      config: { ...prev.config, [field]: value },
    }))
  }

  const selectedTypeConfigFields = serverTypes.find(
    (t) => t.type === formData.server_type
  )?.config_fields || []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border-primary)]">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">MCP Server Management</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-[var(--error)]/10 border border-[var(--error)] text-[var(--error)] rounded-lg">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-[var(--border-primary)]">
          <button
            onClick={() => setActiveTab('servers')}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'servers'
                ? 'text-[var(--primary)] border-b-2 border-[var(--primary)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            Servers
          </button>
          <button
            onClick={() => setActiveTab('add')}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'add'
                ? 'text-[var(--primary)] border-b-2 border-[var(--primary)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            Add Server
          </button>
          <button
            onClick={() => setActiveTab('types')}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'types'
                ? 'text-[var(--primary)] border-b-2 border-[var(--primary)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            Server Types
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading && <div className="text-center py-8 text-[var(--text-secondary)]">Loading...</div>}

          {/* Servers Tab */}
          {activeTab === 'servers' && !isLoading && (
            <div className="space-y-4">
              {servers.length === 0 ? (
                <div className="text-center py-8 text-[var(--text-secondary)]">
                  No MCP servers configured yet. Add one to get started.
                </div>
              ) : (
                servers.map((server) => (
                  <div
                    key={server.id}
                    className="border border-[var(--border-primary)] rounded-lg p-4 hover:border-[var(--primary)] transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-[var(--text-primary)]">{server.name}</h3>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--surface-elevated)] text-[var(--text-secondary)]">
                            {server.server_type}
                          </span>
                          {server.is_active ? (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--success)]/20 text-[var(--success)]">
                              Active
                            </span>
                          ) : (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--text-secondary)]/20 text-[var(--text-secondary)]">
                              Inactive
                            </span>
                          )}
                        </div>
                        {server.description && (
                          <p className="text-sm text-[var(--text-secondary)] mt-1">{server.description}</p>
                        )}
                        <div className="text-xs text-[var(--text-secondary)] mt-2 flex gap-4">
                          {server.health_status && (
                            <span>Health: {server.health_status}</span>
                          )}
                          {server.last_health_check && (
                            <span>Last check: {new Date(server.last_health_check).toLocaleString()}</span>
                          )}
                          <span>Usage: {server.usage_count}</span>
                        </div>
                        {server.available_tools.length > 0 && (
                          <div className="text-xs mt-2">
                            <span className="text-[var(--text-secondary)]">Tools: </span>
                            <span className="text-[var(--text-primary)]">{server.available_tools.join(', ')}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => handleTestExistingServer(server)}
                          className="px-3 py-1.5 text-sm bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] rounded-lg transition-colors"
                          title="Test connection"
                        >
                          Test
                        </button>
                        <button
                          onClick={() => handleGetServerTools(server)}
                          className="px-3 py-1.5 text-sm bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] rounded-lg transition-colors"
                          title="Get available tools"
                        >
                          Tools
                        </button>
                        <button
                          onClick={() => handleDeleteServer(server.id)}
                          className="px-3 py-1.5 text-sm bg-[var(--error)]/10 hover:bg-[var(--error)]/20 text-[var(--error)] rounded-lg transition-colors"
                          title="Delete server"
                        >
                          Delete
                        </button>
                      </div>
                    </div>

                    {/* Tools Display */}
                    {serverTools?.server_id === server.id && (
                      <div className="mt-4 p-3 bg-[var(--surface-elevated)] rounded-lg">
                        <div className="text-sm font-medium text-[var(--text-primary)] mb-2">
                          Available Tools ({serverTools.count})
                        </div>
                        {serverTools.tools.length > 0 ? (
                          <div className="grid grid-cols-2 gap-2">
                            {serverTools.tools.map((tool: string, idx: number) => (
                              <div key={idx} className="text-xs bg-[var(--bg-primary)] px-2 py-1 rounded border border-[var(--border-primary)]">
                                {tool}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-xs text-[var(--text-secondary)]">No tools available</div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Add Server Tab */}
          {activeTab === 'add' && !isLoading && (
            <form onSubmit={handleCreateServer} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  Server Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--surface-elevated)] border border-[var(--border-primary)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)]"
                  placeholder="My MCP Server"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  Server Type
                </label>
                <select
                  value={formData.server_type}
                  onChange={(e) => {
                    setFormData({ ...formData, server_type: e.target.value, config: {} })
                    setTestResult(null)
                  }}
                  className="w-full px-3 py-2 bg-[var(--surface-elevated)] border border-[var(--border-primary)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)]"
                  required
                >
                  <option value="">Select a server type...</option>
                  {serverTypes.map((type) => (
                    <option key={type.type} value={type.type}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {formData.server_type && (
                <div className="space-y-3 p-4 bg-[var(--surface-elevated)] rounded-lg border border-[var(--border-primary)]">
                  <div className="text-sm font-medium text-[var(--text-primary)]">Configuration</div>
                  {selectedTypeConfigFields.map((field) => (
                    <div key={field}>
                      <label className="block text-xs text-[var(--text-secondary)] mb-1">
                        {field}
                      </label>
                      <input
                        type="text"
                        value={(formData.config as any)[field] || ''}
                        onChange={(e) => updateConfigField(field, e.target.value)}
                        className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)] text-sm"
                        placeholder={field}
                        required
                      />
                    </div>
                  ))}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--surface-elevated)] border border-[var(--border-primary)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)]"
                  rows={2}
                  placeholder="Brief description of what this server does"
                />
              </div>

              {/* Test Connection Result */}
              {testResult && (
                <div className={`p-3 rounded-lg border ${
                  testResult.status === 'success'
                    ? 'bg-[var(--success)]/10 border-[var(--success)] text-[var(--success)]'
                    : 'bg-[var(--error)]/10 border-[var(--error)] text-[var(--error)]'
                }`}>
                  <div className="font-medium mb-1">{testResult.message}</div>
                  {testResult.available_tools && (
                    <div className="text-xs mt-1">
                      Available tools: {testResult.available_tools.join(', ')}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={!formData.server_type || isLoading}
                  className="px-4 py-2 bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] rounded-lg transition-colors disabled:opacity-50"
                >
                  Test Connection
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 bg-[var(--primary)] hover:opacity-90 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {isLoading ? 'Creating...' : 'Create Server'}
                </button>
              </div>
            </form>
          )}

          {/* Server Types Tab */}
          {activeTab === 'types' && !isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {serverTypes.map((type) => (
                <div
                  key={type.type}
                  className="border border-[var(--border-primary)] rounded-lg p-4 hover:border-[var(--primary)] transition-colors"
                >
                  <h3 className="font-medium text-[var(--text-primary)] mb-1">{type.label}</h3>
                  <p className="text-sm text-[var(--text-secondary)] mb-3">{type.description}</p>
                  <div className="text-xs">
                    <span className="text-[var(--text-secondary)]">Config fields: </span>
                    <span className="text-[var(--text-primary)]">{type.config_fields.join(', ')}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
