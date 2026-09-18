'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  FileText,
  ArrowLeft,
  Bookmark,
  Layers,
  Database,
  RefreshCw,
  Trash2,
  CheckCircle2,
  Calendar,
  User,
  Hash
} from 'lucide-react';
import { api } from '@/lib/api';
import { Document } from '@/types';

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDocument = async () => {
    try {
      const data = await api.getDocument(id);
      setDocument(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) loadDocument();
  }, [id]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await api.deleteDocument(id);
      router.push('/documents');
    } catch (e: any) {
      alert(e.message);
    }
  };

  if (loading) {
    return <div className="py-20 text-center text-xs text-slate-500">Loading document metadata & chunks...</div>;
  }

  if (error || !document) {
    return (
      <div className="p-8 text-center space-y-4">
        <p className="text-rose-400 text-sm">{error || 'Document not found'}</p>
        <Link href="/documents" className="text-xs text-indigo-400 underline">
          Return to Library
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Back button */}
      <Link
        href="/documents"
        className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-400 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Document Library</span>
      </Link>

      {/* Header Banner */}
      <div className="p-8 rounded-3xl bg-[#0f172a] border border-slate-800 space-y-4 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 uppercase">
                {document.file_type}
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" /> {document.status}
              </span>
            </div>
            <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
              {document.title}
            </h1>
            {document.author && (
              <p className="text-xs text-slate-400 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-500" />
                <span>{document.author}</span>
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDelete}
              className="px-3 py-1.5 rounded-xl bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/20 text-xs font-semibold transition-colors flex items-center gap-1.5"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete</span>
            </button>
          </div>
        </div>

        {/* Abstract */}
        {document.abstract && (
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Abstract</span>
            <p className="text-xs text-slate-300 leading-relaxed font-serif">
              {document.abstract}
            </p>
          </div>
        )}

        {/* Ingestion Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <span className="block text-[10px] uppercase font-bold text-slate-500">Pages</span>
            <span className="text-base font-bold font-mono text-white">{document.page_count}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <span className="block text-[10px] uppercase font-bold text-slate-500">Indexed Chunks</span>
            <span className="text-base font-bold font-mono text-indigo-400">{document.chunk_count}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <span className="block text-[10px] uppercase font-bold text-slate-500">Total Tokens</span>
            <span className="text-base font-bold font-mono text-white">{document.token_count.toLocaleString()}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <span className="block text-[10px] uppercase font-bold text-slate-500">Vector Index</span>
            <span className="text-base font-bold font-mono text-emerald-400">Qdrant Active</span>
          </div>
        </div>
      </div>

      {/* Structure-Aware Chunks Inspector */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            Structure-Aware Indexed Chunks ({document.chunks ? document.chunks.length : document.chunk_count})
          </h2>
          <span className="text-xs text-slate-500">
            Ordered by document reading sequence & section hierarchy
          </span>
        </div>

        <div className="space-y-3">
          {document.chunks && document.chunks.length > 0 ? (
            document.chunks.map((chunk) => (
              <div
                key={chunk.id}
                className="p-5 rounded-2xl bg-[#0b0f19] border border-slate-800/90 hover:border-indigo-500/40 transition-all space-y-3"
              >
                {/* Chunk Header Badges */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800/60 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-md bg-slate-800 text-indigo-400 font-mono font-bold text-[10px] flex items-center justify-center">
                      #{chunk.chunk_index + 1}
                    </span>
                    <span className="font-semibold text-slate-200">
                      {chunk.section}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 font-mono text-[11px] text-slate-400">
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      Page {chunk.page_number}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-indigo-300">
                      {chunk.token_count} tokens
                    </span>
                  </div>
                </div>

                {/* Context Header */}
                {chunk.context_header && (
                  <div className="text-[11px] font-mono text-slate-500 bg-slate-950/80 px-3 py-1 rounded-lg border border-slate-900">
                    {chunk.context_header}
                  </div>
                )}

                {/* Content */}
                <p className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-wrap">
                  {chunk.content}
                </p>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-500 italic py-6 text-center">
              No chunks extracted. Click Reprocess to re-ingest.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
