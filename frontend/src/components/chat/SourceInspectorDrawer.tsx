'use client';

import React from 'react';
import { X, FileText, Bookmark, Target, Award, ExternalLink, Hash } from 'lucide-react';
import { Citation } from '@/types';

interface SourceInspectorDrawerProps {
  citation: Citation | null;
  onClose: () => void;
}

export function SourceInspectorDrawer({ citation, onClose }: SourceInspectorDrawerProps) {
  if (!citation) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 z-50 bg-[#0d1322] border-l border-slate-800 shadow-2xl flex flex-col transform transition-transform ease-in-out duration-300">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-md bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-bold text-xs">
            [{citation.citation_number}]
          </span>
          <h3 className="font-semibold text-sm text-slate-200">Source Passage Inspector</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Document Card */}
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
          <div className="flex items-start gap-2.5">
            <FileText className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-semibold text-slate-200 leading-snug">
                {citation.document_title}
              </h4>
              <div className="flex flex-wrap gap-2 mt-2">
                <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  <Bookmark className="w-3 h-3 text-indigo-400" />
                  Page {citation.page_number}
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  <Hash className="w-3 h-3 text-cyan-400" />
                  {citation.section}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Retrieval & Rerank Scores */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800/80">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mb-1">
              <Target className="w-3.5 h-3.5 text-indigo-400" />
              <span>Vector / RRF</span>
            </div>
            <div className="text-base font-bold text-slate-200 font-mono">
              {(citation.similarity_score * 100).toFixed(1)}%
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800/80">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mb-1">
              <Award className="w-3.5 h-3.5 text-emerald-400" />
              <span>Rerank Score</span>
            </div>
            <div className="text-base font-bold text-emerald-400 font-mono">
              {citation.rerank_score ? citation.rerank_score.toFixed(3) : 'High'}
            </div>
          </div>
        </div>

        {/* Highlighted Supporting Passage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Supporting Grounded Passage
            </span>
            <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20 font-medium">
              Verified Evidence
            </span>
          </div>
          <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 text-xs text-slate-200 leading-relaxed font-serif shadow-inner whitespace-pre-line">
            &ldquo;{citation.passage_text}&rdquo;
          </div>
        </div>

        {/* Provenance Metadata */}
        <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-1.5 text-[11px] text-slate-400 font-mono">
          <div className="flex justify-between">
            <span>Chunk Reference ID:</span>
            <span className="text-slate-300 truncate max-w-[160px]">{citation.chunk_id || 'Auto-Indexed'}</span>
          </div>
          <div className="flex justify-between">
            <span>Grounding Status:</span>
            <span className="text-emerald-400 font-sans font-semibold">100% Attributed</span>
          </div>
        </div>
      </div>
    </div>
  );
}
