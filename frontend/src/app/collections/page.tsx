'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { FolderOpen, Plus, FileText, Trash2, Layers, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { Collection } from '@/types';

export default function CollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#6366f1');
  const [loading, setLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  const loadCollections = async () => {
    try {
      const data = await api.getCollections();
      setCollections(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCollections();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await api.createCollection(name, description, color);
      setName('');
      setDescription('');
      setIsCreating(false);
      loadCollections();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this collection?')) return;
    try {
      await api.deleteCollection(id);
      loadCollections();
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <FolderOpen className="w-6 h-6 text-indigo-400" />
            Knowledge Collections
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Group research documents into thematic knowledge vaults for targeted multi-document RAG.
          </p>
        </div>

        <button
          onClick={() => setIsCreating(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Collection</span>
        </button>
      </div>

      {/* Creation Form Modal / Card */}
      {isCreating && (
        <form onSubmit={handleCreate} className="p-6 rounded-2xl bg-[#0f172a] border border-indigo-500/40 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white">Create New Knowledge Collection</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Collection Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Hallucination Reduction in LLMs"
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Description</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Research focus and scope"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Badge Color</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  className="w-9 h-9 rounded-lg bg-transparent border-0 cursor-pointer"
                />
                <span className="text-xs font-mono text-slate-400">{color}</span>
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreating(false)}
              className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20"
            >
              Save Collection
            </button>
          </div>
        </form>
      )}

      {/* Collections Grid */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-500">Loading collections...</div>
      ) : collections.length === 0 ? (
        <div className="py-20 text-center rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-3">
          <FolderOpen className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-white">No collections created yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Create your first collection to organize your research papers.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {collections.map((col) => (
            <div
              key={col.id}
              className="p-6 rounded-2xl bg-[#0f172a] border border-slate-800 hover:border-indigo-500/40 p-5 transition-all shadow-sm flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div
                    className="w-3.5 h-3.5 rounded-full shadow-md"
                    style={{ backgroundColor: col.color }}
                  />
                  <button
                    onClick={() => handleDelete(col.id)}
                    className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <h3 className="font-bold text-base text-white">{col.name}</h3>
                {col.description && (
                  <p className="text-xs text-slate-400 leading-relaxed">{col.description}</p>
                )}
              </div>

              <div className="pt-6 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-xs font-mono text-indigo-400 font-semibold flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5" />
                  {col.document_count} Papers
                </span>
                <Link
                  href={`/documents?collection_id=${col.id}`}
                  className="text-xs font-semibold text-slate-300 hover:text-indigo-400 transition-colors"
                >
                  Browse Papers &rarr;
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
