'use client';

import React from 'react';
import Link from 'next/link';
import { FileText, Bookmark, Database, Trash2, RefreshCw, Layers, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { Document } from '@/types';

interface DocumentCardProps {
  doc: Document;
  onReprocess: (id: string) => void;
  onDelete: (id: string) => void;
}

export function DocumentCard({ doc, onReprocess, onDelete }: DocumentCardProps) {
  const getStatusBadge = () => {
    switch (doc.status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" /> Indexed
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertTriangle className="w-3 h-3" /> Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" /> {doc.status}
          </span>
        );
    }
  };

  return (
    <div className="rounded-xl bg-[#0f172a]/90 border border-slate-800 hover:border-indigo-500/40 p-5 transition-all shadow-sm hover:shadow-indigo-500/5 flex flex-col justify-between group">
      <div>
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono border border-slate-700">
            {doc.file_type}
          </span>
          {getStatusBadge()}
        </div>

        {/* Title & Author */}
        <Link href={`/documents/${doc.id}`} className="block group-hover:text-indigo-400 transition-colors">
          <h3 className="font-bold text-sm text-slate-100 line-clamp-2 leading-snug mb-1">
            {doc.title}
          </h3>
        </Link>

        {doc.author && (
          <p className="text-xs text-slate-400 line-clamp-1 mb-3">
            {doc.author}
          </p>
        )}

        {doc.abstract && (
          <p className="text-xs text-slate-400/90 line-clamp-2 leading-relaxed mb-4">
            {doc.abstract}
          </p>
        )}
      </div>

      {/* Metadata Stats Footer */}
      <div className="pt-4 border-t border-slate-800/80 space-y-3">
        <div className="grid grid-cols-3 gap-2 text-center text-[11px] font-mono">
          <div className="p-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="block text-slate-500 text-[9px] uppercase font-sans font-semibold">Pages</span>
            <span className="font-bold text-slate-300">{doc.page_count}</span>
          </div>
          <div className="p-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="block text-slate-500 text-[9px] uppercase font-sans font-semibold">Chunks</span>
            <span className="font-bold text-indigo-400">{doc.chunk_count}</span>
          </div>
          <div className="p-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="block text-slate-500 text-[9px] uppercase font-sans font-semibold">Tokens</span>
            <span className="font-bold text-slate-300">{doc.token_count.toLocaleString()}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between gap-2">
          <Link
            href={`/documents/${doc.id}`}
            className="flex-1 text-center py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
          >
            Inspect Chunks
          </Link>

          <button
            onClick={() => onReprocess(doc.id)}
            title="Reprocess & Re-embed"
            className="p-1.5 rounded-lg bg-slate-800/50 hover:bg-indigo-600/20 hover:text-indigo-400 text-slate-400 border border-slate-800 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => onDelete(doc.id)}
            title="Delete Document"
            className="p-1.5 rounded-lg bg-slate-800/50 hover:bg-rose-600/20 hover:text-rose-400 text-slate-400 border border-slate-800 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
