'use client';

import React, { useState, useEffect } from 'react';
import {
  Activity,
  Layers,
  Database,
  Clock,
  Zap,
  Search,
  RefreshCw,
  Cpu,
  ShieldCheck,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import { api } from '@/lib/api';
import { ObservabilityStats, QueryTrace } from '@/types';
import { TraceViewer } from '@/components/observability/TraceViewer';

export default function ObservabilityPage() {
  const [stats, setStats] = useState<ObservabilityStats | null>(null);
  const [traces, setTraces] = useState<QueryTrace[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<QueryTrace | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [statsData, tracesData] = await Promise.all([
        api.getObservabilityStats(),
        api.getQueryTraces(50)
      ]);
      setStats(statsData);
      setTraces(tracesData);
      if (tracesData.length > 0 && !selectedTrace) {
        setSelectedTrace(tracesData[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold mb-2">
            <Activity className="w-3.5 h-3.5" />
            <span>Real-time Pipeline Telemetry</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            AI Observability & Trace Inspector
          </h1>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Trace the internal lifecycle of every RAG query from rewrite to hybrid retrieval, cross-encoder reranking, and citation generation.
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-semibold transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Traces</span>
        </button>
      </div>

      {/* Platform Telemetry Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Queries Executed</span>
            <Search className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {stats ? stats.total_queries : traces.length}
          </div>
          <span className="text-[10px] text-slate-500 block">End-to-End Sessions</span>
        </div>

        <div className="p-5 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Avg Retrieval Latency</span>
            <Clock className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {stats ? `${stats.avg_retrieval_latency_ms.toFixed(0)} ms` : '0 ms'}
          </div>
          <span className="text-[10px] text-slate-500 block">Dense + BM25 Fusion</span>
        </div>

        <div className="p-5 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Avg Generation Latency</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-400">
            {stats ? `${stats.avg_generation_latency_ms.toFixed(0)} ms` : '0 ms'}
          </div>
          <span className="text-[10px] text-slate-500 block">LLM Grounded Synthesis</span>
        </div>

        <div className="p-5 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Tokens Consumed</span>
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-purple-400">
            {stats ? stats.total_tokens_consumed.toLocaleString() : 0}
          </div>
          <span className="text-[10px] text-slate-500 block">Prompt + Completion</span>
        </div>
      </div>

      {/* Trace Selector & Detail View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trace List */}
        <div className="p-4 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-2">
            Execution Traces ({traces.length})
          </h3>

          <div className="space-y-1.5 max-h-[550px] overflow-y-auto">
            {traces.map((t) => (
              <div
                key={t.id}
                onClick={() => setSelectedTrace(t)}
                className={`p-3 rounded-xl text-xs cursor-pointer transition-all space-y-1 border ${
                  selectedTrace?.id === t.id
                    ? 'bg-indigo-950/40 border-indigo-500 text-indigo-200'
                    : 'bg-slate-900/60 border-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <p className="font-semibold text-slate-200 truncate">&ldquo;{t.raw_query}&rdquo;</p>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span className="text-emerald-400">{t.total_latency_ms.toFixed(0)}ms</span>
                  <span>{t.citations_count} citations</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Trace Deep Inspector */}
        <div className="lg:col-span-2">
          {selectedTrace ? (
            <TraceViewer trace={selectedTrace} />
          ) : (
            <div className="p-16 text-center rounded-2xl bg-[#0b0f19] border border-slate-800 text-xs text-slate-500">
              Select an execution trace to inspect the RAG pipeline internals.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
