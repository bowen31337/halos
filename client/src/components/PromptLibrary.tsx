import React, { useState, useEffect } from 'react';
import { Plus, Search, Edit, Trash2, Tag, Clock, Eye, Filter } from 'lucide-react';
import { api } from '../services/api';

interface Prompt {
  id: string;
  title: string;
  content: string;
  category: string;
  description?: string;
  tags: string[];
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface Category {
  value: string;
  label: string;
  count: number;
}

export const PromptLibrary: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Form state for create/edit
  const [formState, setFormState] = useState({
    title: '',
    content: '',
    category: 'general',
    description: '',
    tags: '',
  });

  useEffect(() => {
    if (isOpen) {
      loadPrompts();
      loadCategories();
    }
  }, [isOpen]);

  const loadPrompts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getPrompts(selectedCategory || undefined);
      setPrompts(data);
    } catch (err) {
      setError('Failed to load prompts');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await api.getCategories();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadPrompts();
      return;
    }

    setIsLoading(true);
    try {
      const data = await api.searchPrompts(searchQuery);
      setPrompts(data);
    } catch (err) {
      setError('Failed to search prompts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUsePrompt = async (prompt: Prompt) => {
    try {
      await api.usePrompt(prompt.id);
      // Mark as used locally
      setPrompts(prev =>
        prev.map(p => (p.id === prompt.id ? { ...p, usage_count: p.usage_count + 1 } : p))
      );
      // Close the modal and use the prompt content
      onClose();
      // Emit event to parent to insert the prompt content
      window.dispatchEvent(new CustomEvent('use-prompt', { detail: prompt.content }));
    } catch (err) {
      setError('Failed to use prompt');
    }
  };

  const handleEdit = (prompt: Prompt) => {
    setSelectedPrompt(prompt);
    setFormState({
      title: prompt.title,
      content: prompt.content,
      category: prompt.category,
      description: prompt.description || '',
      tags: prompt.tags.join(', '),
    });
    setIsEditing(true);
  };

  const handleDelete = async (prompt: Prompt) => {
    if (!confirm(`Are you sure you want to delete "${prompt.title}"?`)) {
      return;
    }

    try {
      await api.deletePrompt(prompt.id);
      setPrompts(prev => prev.filter(p => p.id !== prompt.id));
    } catch (err) {
      setError('Failed to delete prompt');
    }
  };

  const handleSave = async () => {
    const tags = formState.tags.split(',').map(tag => tag.trim()).filter(Boolean);

    try {
      if (isEditing && selectedPrompt) {
        await api.updatePrompt(selectedPrompt.id, {
          title: formState.title,
          content: formState.content,
          category: formState.category,
          description: formState.description || undefined,
          tags,
        });
        setPrompts(prev =>
          prev.map(p =>
            p.id === selectedPrompt.id
              ? { ...p, ...formState, tags, updated_at: new Date().toISOString() }
              : p
          )
        );
      } else {
        const newPrompt = await api.createPrompt({
          title: formState.title,
          content: formState.content,
          category: formState.category,
          description: formState.description || undefined,
          tags,
        });
        setPrompts(prev => [newPrompt, ...prev]);
      }

      // Reset form
      setFormState({ title: '', content: '', category: 'general', description: '', tags: '' });
      setIsEditing(false);
      setIsCreating(false);
    } catch (err) {
      setError(isEditing ? 'Failed to update prompt' : 'Failed to create prompt');
    }
  };

  const handleCreate = () => {
    setFormState({ title: '', content: '', category: 'general', description: '', tags: '' });
    setIsCreating(true);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {isCreating || isEditing ? (isEditing ? 'Edit Prompt' : 'Create New Prompt') : 'Prompt Library'}
            </h2>
            {!isCreating && !isEditing && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {prompts.length} prompts
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!isCreating && !isEditing && (
              <button
                onClick={handleCreate}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <Plus size={18} />
                New Prompt
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              ×
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="m-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded text-sm">
            {error}
          </div>
        )}

        {/* Create/Edit Form */}
        {(isCreating || isEditing) && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={formState.title}
                  onChange={(e) => setFormState({ ...formState, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Enter prompt title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  value={formState.category}
                  onChange={(e) => setFormState({ ...formState, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="general">General</option>
                  <option value="writing">Writing</option>
                  <option value="coding">Coding</option>
                  <option value="analysis">Analysis</option>
                  <option value="creative">Creative</option>
                  <option value="business">Business</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Content *
              </label>
              <textarea
                value={formState.content}
                onChange={(e) => setFormState({ ...formState, content: e.target.value })}
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Enter your prompt template..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <input
                type="text"
                value={formState.description}
                onChange={(e) => setFormState({ ...formState, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Optional description"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={formState.tags}
                onChange={(e) => setFormState({ ...formState, tags: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="e.g., ai, writing, template"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                {isEditing ? 'Update' : 'Create'}
              </button>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setIsCreating(false);
                  setFormState({ title: '', content: '', category: 'general', description: '', tags: '' });
                }}
                className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white rounded hover:bg-gray-400 dark:hover:bg-gray-500"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* List View */}
        {!isCreating && !isEditing && (
          <>
            {/* Search and Filter */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-4">
              <div className="flex gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Search prompts by title, content, or tags..."
                  />
                </div>
                <button
                  onClick={handleSearch}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Search
                </button>
                <select
                  value={selectedCategory}
                  onChange={(e) => {
                    setSelectedCategory(e.target.value);
                    loadPrompts();
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">All Categories</option>
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Prompts List */}
            <div className="overflow-auto">
              {isLoading ? (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                  Loading prompts...
                </div>
              ) : prompts.length === 0 ? (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                  No prompts found. Create your first prompt!
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {prompts.map((prompt) => (
                    <div key={prompt.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-medium text-gray-900 dark:text-white">{prompt.title}</h3>
                            <span className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded">
                              {prompt.category}
                            </span>
                            <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                              <Clock size={14} />
                              {prompt.usage_count} uses
                            </span>
                          </div>

                          {prompt.description && (
                            <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                              {prompt.description}
                            </p>
                          )}

                          <div className="text-sm text-gray-500 dark:text-gray-400 mb-2 line-clamp-2">
                            {prompt.content}
                          </div>

                          {prompt.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {prompt.tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                                >
                                  <Tag size={12} />
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex gap-2 ml-4">
                          <button
                            onClick={() => handleUsePrompt(prompt)}
                            className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                          >
                            <Eye size={16} />
                            Use
                          </button>
                          <button
                            onClick={() => handleEdit(prompt)}
                            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                          >
                            <Edit size={16} />
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(prompt)}
                            className="flex items-center gap-2 px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                          >
                            <Trash2 size={16} />
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};