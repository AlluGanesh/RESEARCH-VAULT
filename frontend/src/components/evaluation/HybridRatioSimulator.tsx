'use client';

import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Sparkles,
  Layers,
  Copy,
  Check,
  Search,
  Loader2,
  Database,
  ArrowRight,
  ShieldCheck,
  Tag,
  Clock,
  Zap,
  Play
} from 'lucide-react';
import { api } from '@/lib/api';
import { HybridSimulateResponse } from '@/types';

const PRESET_QUERIES = [
  'How does scaled dot-product attention prevent vanishing gradients in high dimensions?',
  'What special reflection tokens does Self-RAG introduce to regulate retrieval on-demand?',
  'How does Retrieval-Augmented Generation combine parametric BART with non-parametric DPR memory?',
  'WMT 2014 English-to-German translation BLEU benchmark results'
];

export function HybridRatioSimulator() {
  const [denseWeight, setDenseWeight] = useState<number>(0.6);
  const [query, setQuery] = useState<string>(PRESET_QUERIES[0]);
  const [topK, setTopK] = useState<number>(8);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<HybridSimulateResponse | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const sparseWeight = Math.round((1.0 - denseWeight) * 100) / 100;

  const handleSimulate = async () => {
    if (!query.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.simulateHybridRetrieval({
        query: query.trim(),
        dense_weight: denseWeight,
        sparse_weight: sparseWeight,
        k: topK
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Retrieval simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSimulate();
  }, [denseWeight]);

  const handleCopyConfig = () => {
    const config = {
      dense_weight: Number(denseWeight.toFixed(2)),
      sparse_weight: Number(sparseWeight.toFixed(2)),
      rrf_k_constant: 60,
      formula: `S(d) = ${denseWeight.toFixed(2)}/(60 + r_d) + ${sparseWeight.toFixed(2)}/(60 + r_s)`
    };
    navigator.clipboard.writeText(JSON.stringify(config, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Configuration Header Card */}
      <div className="p-6 rounded-3xl bg-[#0f172a] border border-slate-800 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold mb-2">
              <Sliders className="w-3.5 h-3.5" />
              <span>Interactive Hybrid Ratio Simulator</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Retrieval Weight Configuration & Weighted RRF
            </h2>
            <p className="text-xs text-slate-400 mt-0.5 max-w-2xl leading-relaxed">
              Dynamically tune and inspect how fusion weights balance semantic dense search against exact keyword BM25 retrieval. Document ranking follows the weighted Reciprocal Rank Fusion formula: S(d) = w_d / (k + r_d) + w_s / (k + r_s).
            </p>
          </div>

          <button
            onClick={handleCopyConfig}
            className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-all cursor-pointer shrink-0"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-400">Configuration Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 text-slate-400" />
                <span>Copy configuration</span>
              </>
            )}
          </button>
        </div>

        {/* Sliders Workspace */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* Dense Search Slider */}
          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50" />
                Dense Semantic Search
              </span>
              <span className="text-base font-extrabold font-mono text-cyan-400">
                {Math.round(denseWeight * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={denseWeight}
              onChange={(e) => setDenseWeight(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0% (BM25 only)</span>
              <span>Weight: {denseWeight.toFixed(2)}</span>
              <span>100% (Dense only)</span>
            </div>
          </div>

          {/* Sparse BM25 Slider */}
          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50" />
                Sparse BM25 Search
              </span>
              <span className="text-base font-extrabold font-mono text-amber-400">
                {Math.round(sparseWeight * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={sparseWeight}
              onChange={(e) => setDenseWeight(1.0 - parseFloat(e.target.value))}
              className="w-full accent-amber-400 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0% (Dense only)</span>
              <span>Weight: {sparseWeight.toFixed(2)}</span>
              <span>100% (BM25 only)</span>
            </div>
          </div>
        </div>

        {/* Preset Ratios Quick Select */}
        <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">
            Presets:
          </span>
          {[
            { label: '100% BM25', d: 0.0 },
            { label: '70% BM25 / 30% Dense', d: 0.3 },
            { label: '50:50 Balanced', d: 0.5 },
            { label: '60% Dense / 40% BM25 (Default)', d: 0.6 },
            { label: '80% Dense / 20% BM25', d: 0.8 },
            { label: '100% Dense', d: 1.0 },
          ].map((preset, idx) => (
            <button
              key={idx}
              onClick={() => setDenseWeight(preset.d)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                Math.abs(denseWeight - preset.d) < 0.01
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>

        {/* Weighted RRF Formula Banner */}
        <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="font-mono text-slate-300 flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-cyan-400 font-bold">RRF</span>
            <span>
              S(d) = ({denseWeight.toFixed(2)} / (60 + r_d)) + ({sparseWeight.toFixed(2)} / (60 + r_s))
            </span>
          </div>
          <span className="text-[11px] text-slate-400 italic">
            This adjusts fusion weights, not the number of retrieved chunks.
          </span>
        </div>
      </div>

      {/* Query Bar */}
      <div className="p-5 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-cyan-400" />
            Live Query Simulator
          </span>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500">Query preset:</span>
            <select
              onChange={(e) => setQuery(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-[11px] text-slate-300 rounded-lg px-2.5 py-1 focus:outline-none focus:border-cyan-500"
            >
              {PRESET_QUERIES.map((q, i) => (
                <option key={i} value={q}>
                  {q.slice(0, 50)}...
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type research question or technical query..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          />
          <button
            onClick={handleSimulate}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-cyan-600/20 flex items-center gap-2 cursor-pointer transition-all shrink-0"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
            <span>Run Retrieval</span>
          </button>
        </div>
      </div>

      {/* Real-Time Diagnostics Metric Cards */}
      {result && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Overlap @ {result.k}</span>
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-indigo-400">
              {result.overlap_count}
              <span className="text-xs text-slate-500 font-sans ml-1 font-normal">
                ({(result.overlap_ratio * 100).toFixed(0)}%)
              </span>
            </div>
            <span className="text-[10px] text-slate-500 block">Chunks found by both methods</span>
          </div>

          <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Dense-Only Hits</span>
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-cyan-400">
              {result.dense_only_count}
            </div>
            <span className="text-[10px] text-slate-500 block">Unique semantic vector wins</span>
          </div>

          <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Sparse BM25 Hits</span>
              <Database className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400">
              {result.sparse_only_count}
            </div>
            <span className="text-[10px] text-slate-500 block">Unique keyword term matches</span>
          </div>

          <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Retrieval Latency</span>
              <Clock className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {result.latency_ms}ms
            </div>
            <span className="text-[10px] text-slate-500 block">Qdrant + BM25 parallel time</span>
          </div>
        </div>
      )}

      {/* Candidate Chunks Stream Table */}
      {result && (
        <div className="p-6 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Fused Candidate Chunks ({result.candidates.length} Retrieved)
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Individual document chunks re-ranked according to the current {Math.round(denseWeight * 100)}:{Math.round(sparseWeight * 100)} weighted RRF score.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-500">
              Fusion constant k=60
            </span>
          </div>

          <div className="space-y-3">
            {result.candidates.map((cand, idx) => {
              const isOverlap = cand.retrieval_source === 'hybrid_overlap';
              const isDenseOnly = cand.retrieval_source === 'dense_only';
              const isSparseOnly = cand.retrieval_source === 'sparse_only';

              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition-all space-y-2 text-xs"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-lg bg-slate-800 text-slate-300 font-mono text-[11px] font-bold flex items-center justify-center">
                        #{idx + 1}
                      </span>
                      <span className="font-semibold text-slate-200">
                        {cand.document_title || 'Document Chunk'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isOverlap
                            ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30'
                            : isDenseOnly
                            ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                            : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        }`}
                      >
                        {isOverlap ? 'Hybrid Overlap' : isDenseOnly ? 'Dense Only' : 'Sparse BM25 Only'}
                      </span>
                      <span className="font-mono font-bold text-slate-300 text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                        RRF: {cand.rrf_score.toFixed(5)}
                      </span>
                    </div>
                  </div>

                  <p className="text-slate-400 italic text-[11px] leading-relaxed pl-8">
                    "{cand.passage_preview}"
                  </p>

                  <div className="pl-8 flex items-center gap-4 text-[10px] font-mono text-slate-500">
                    {cand.vector_score !== null && cand.vector_score !== undefined && (
                      <span>Vector Cosine: <strong className="text-cyan-400">{cand.vector_score.toFixed(3)}</strong></span>
                    )}
                    {cand.lexical_score !== null && cand.lexical_score !== undefined && (
                      <span>BM25 Score: <strong className="text-amber-400">{cand.lexical_score.toFixed(3)}</strong></span>
                    )}
                    {cand.chunk_id && (
                      <span>ID: {cand.chunk_id.slice(0, 8)}...</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
