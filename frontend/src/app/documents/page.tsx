'use client';

import React, { useState, useEffect } from 'react';
import { FileText, Plus, Search, Filter, RefreshCw, FolderOpen } from 'lucide-react';
import { api } from '@/lib/api';
import { Document, Collection } from '@/types';
import { DocumentCard } from '@/components/documents/DocumentCard';
import { DocumentUploadModal } from '@/components/documents/DocumentUploadModal';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [docs, cols] = await Promise.all([
        api.getDocuments(selectedCollection || undefined),
        api.getCollections()
      ]);
      setDocuments(docs);
      setCollections(cols);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCollection]);

  const handleReprocess = async (id: string) => {
    try {
      await api.reprocessDocument(id);
      loadData();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document and all its indexed chunks?')) return;
    try {
      await api.deleteDocument(id);
      loadData();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const filteredDocs = documents.filter((d) =>
    d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (d.author && d.author.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (d.abstract && d.abstract.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-indigo-400" />
            Research Document Library
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage, inspect, and re-embed research papers indexed into Qdrant vector database.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            title="Refresh library"
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Ingest Document</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-2xl bg-[#0f172a]/90 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by title, author, or keyword..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedCollection}
            onChange={(e) => setSelectedCollection(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Collections</option>
            {collections.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.document_count})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Document Grid */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-500 animate-pulse">
          Loading indexed research corpus...
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="py-20 text-center rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-3">
          <FileText className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-white">No documents found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {searchQuery ? 'No documents match your query.' : 'Upload research papers (PDF, DOCX, TXT, MD) to get started.'}
          </p>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold shadow-md shadow-indigo-600/20"
          >
            Upload First Document
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDocs.map((doc) => (
            <DocumentCard
              key={doc.id}
              doc={doc}
              onReprocess={handleReprocess}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        collections={collections}
        onUploadSuccess={loadData}
      />
    </div>
  );
}
