'use client';

import React, { useState } from 'react';
import {
  Activity,
  Zap,
  Clock,
  Layers,
  Search,
  Filter,
  ArrowRight,
  Database,
  Cpu,
  CheckCircle2,
  FileCode,
  ShieldCheck
} from 'lucide-react';
import { QueryTrace } from '@/types';

interface TraceViewerProps {
  trace: QueryTrace;
}

export function TraceViewer({ trace }: TraceViewerProps) {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'context' | 'response'>('pipeline');

  return (
    <div className="rounded-2xl bg-[#0b0f19] border border-slate-800 overflow-hidden space-y-6 p-6 shadow-2xl">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase tracking-wider block mb-1">
            Trace ID: {trace.id}
          </span>
          <h3 className="text-base font-bold text-white tracking-tight">
            &ldquo;{trace.raw_query}&rdquo;
          </h3>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-right">
            <span className="block text-[9px] uppercase font-bold text-slate-500">Total Latency</span>
            <span className="text-xs font-mono font-bold text-emerald-400">{trace.total_latency_ms.toFixed(0)} ms</span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-right">
            <span className="block text-[9px] uppercase font-bold text-slate-500">Total Tokens</span>
            <span className="text-xs font-mono font-bold text-indigo-400">{trace.total_tokens}</span>
          </div>
        </div>
      </div>

      {/* Latency Breakdown Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-400 font-semibold">
          <span>End-to-End Pipeline Stage Latency</span>
          <span className="font-mono text-slate-300">{trace.total_latency_ms.toFixed(1)}ms</span>
        </div>
        <div className="h-3 rounded-full bg-slate-900 overflow-hidden flex border border-slate-800">
          <div
            style={{ width: `${Math.max(5, (trace.query_transform_ms / (trace.total_latency_ms || 1)) * 100)}%` }}
            className="bg-cyan-500"
            title={`Query Rewrite: ${trace.query_transform_ms.toFixed(1)}ms`}
          />
          <div
            style={{ width: `${Math.max(5, (trace.retrieval_ms / (trace.total_latency_ms || 1)) * 100)}%` }}
            className="bg-indigo-500"
            title={`Hybrid Retrieval (Qdrant + BM25): ${trace.retrieval_ms.toFixed(1)}ms`}
          />
          <div
            style={{ width: `${Math.max(5, (trace.rerank_ms / (trace.total_latency_ms || 1)) * 100)}%` }}
            className="bg-purple-500"
            title={`Cross-Encoder Reranking: ${trace.rerank_ms.toFixed(1)}ms`}
          />
          <div
            style={{ width: `${Math.max(5, (trace.generation_ms / (trace.total_latency_ms || 1)) * 100)}%` }}
            className="bg-emerald-500"
            title={`LLM Generation: ${trace.generation_ms.toFixed(1)}ms`}
          />
        </div>
        <div className="flex flex-wrap gap-4 text-[10px] text-slate-400 font-mono pt-1">
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-cyan-500" /> Rewrite ({trace.query_transform_ms.toFixed(0)}ms)</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-indigo-500" /> Hybrid Retrieval ({trace.retrieval_ms.toFixed(0)}ms)</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-purple-500" /> Rerank ({trace.rerank_ms.toFixed(0)}ms)</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Generation ({trace.generation_ms.toFixed(0)}ms)</span>
        </div>
      </div>

      {/* Interactive Tabs */}
      <div className="flex gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('pipeline')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'pipeline' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Pipeline Stages Flow
        </button>
        <button
          onClick={() => setActiveTab('context')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'context' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Compressed Grounded Context
        </button>
        <button
          onClick={() => setActiveTab('response')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'response' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          LLM Output & Citations ({trace.citations_count})
        </button>
      </div>

      {/* Tab 1: Pipeline Stages Flow */}
      {activeTab === 'pipeline' && (
        <div className="space-y-4">
          {/* Stage 1: Query Transformation */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                <Search className="w-3.5 h-3.5" /> Stage 1: Query Transformation & Coreference
              </span>
              <span className="text-[10px] font-mono text-slate-400">{trace.query_transform_ms.toFixed(1)}ms</span>
            </div>
            <div className="space-y-1 text-xs">
              <p className="text-slate-300"><span className="text-slate-500">Rewritten:</span> {trace.rewritten_query || trace.raw_query}</p>
              {trace.expansion_queries && trace.expansion_queries.length > 0 && (
                <div className="pt-1">
                  <span className="text-[10px] uppercase text-slate-500 font-bold block mb-1">Multi-Query Expansions:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {trace.expansion_queries.map((eq, i) => (
                      <span key={i} className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-indigo-300 border border-slate-700">
                        {eq}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Stage 2: Hybrid Retrieval & Reciprocal Rank Fusion */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-400 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5" /> Stage 2: Hybrid Retrieval & Reciprocal Rank Fusion (RRF)
              </span>
              <span className="text-[10px] font-mono text-slate-400">{trace.retrieval_ms.toFixed(1)}ms</span>
            </div>
            <p className="text-xs text-slate-300">
              Evaluated {trace.vector_candidates_count} dense vector candidates (Qdrant) and {trace.lexical_candidates_count} sparse lexical candidates (BM25 Okapi).
            </p>
            {trace.rrf_candidates && trace.rrf_candidates.length > 0 && (
              <div className="space-y-1.5 pt-2">
                <span className="text-[10px] uppercase text-slate-500 font-bold block">Top RRF Fused Candidates:</span>
                {trace.rrf_candidates.slice(0, 3).map((c: any, i: number) => (
                  <div key={i} className="p-2 rounded-lg bg-slate-950/70 border border-slate-800/80 text-[11px] flex items-center justify-between">
                    <span className="text-slate-200 truncate max-w-sm">{c.document_title || c.chunk_id}</span>
                    <span className="font-mono text-indigo-400 font-bold">RRF: {c.rrf_score ? c.rrf_score.toFixed(4) : 'N/A'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Stage 3: Cross-Encoder Reranking */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-purple-400 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> Stage 3: Neural Cross-Encoder Reranking
              </span>
              <span className="text-[10px] font-mono text-slate-400">{trace.rerank_ms.toFixed(1)}ms</span>
            </div>
            <p className="text-xs text-slate-300">
              Selected top candidate chunks scored against full query context using cross-encoder architecture.
            </p>
          </div>
        </div>
      )}

      {/* Tab 2: Compressed Context */}
      {activeTab === 'context' && (
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">
          {trace.compressed_context || 'No compressed context recorded.'}
        </div>
      )}

      {/* Tab 3: Response & Citations */}
      {activeTab === 'response' && (
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed font-sans">
          {trace.llm_response || 'No response recorded.'}
        </div>
      )}
    </div>
  );
}
