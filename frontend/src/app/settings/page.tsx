'use client';

import React, { useState } from 'react';
import { Settings, ShieldCheck, Cpu, Database, Save, CheckCircle2 } from 'lucide-react';

export default function SettingsPage() {
  const [llmProvider, setLlmProvider] = useState('openai');
  const [embeddingProvider, setEmbeddingProvider] = useState('sentence-transformers');
  const [rerankerType, setRerankerType] = useState('cross-encoder');
  const [chunkSize, setChunkSize] = useState(500);
  const [topK, setTopK] = useState(7);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
          <Settings className="w-6 h-6 text-indigo-400" />
          RAG Pipeline Engine Settings
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure multi-provider LLM endpoints, local SentenceTransformers embeddings, Qdrant index parameters, and cross-encoder rerankers.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* LLM & Embeddings Card */}
        <div className="p-6 rounded-3xl bg-[#0f172a] border border-slate-800 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            Inference & Embeddings Architecture
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                LLM Provider Abstraction
              </label>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="openai">OpenAI (GPT-4o-mini / GPT-4o)</option>
                <option value="gemini">Google Gemini (Gemini-1.5-Flash)</option>
                <option value="ollama">Ollama (Local LLaMA 3 / Mistral)</option>
                <option value="local">Local Grounded Fallback Engine</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Embedding Model Provider
              </label>
              <select
                value={embeddingProvider}
                onChange={(e) => setEmbeddingProvider(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="sentence-transformers">SentenceTransformers (all-MiniLM-L6-v2, 384-dim)</option>
                <option value="openai">OpenAI (text-embedding-3-small, 1536-dim)</option>
                <option value="gemini">Gemini (text-embedding-004, 768-dim)</option>
                <option value="ollama">Ollama (nomic-embed-text)</option>
                <option value="fast-numpy">Fast NumPy Projection Provider</option>
              </select>
            </div>
          </div>
        </div>

        {/* Retrieval & Reranker Hyperparameters */}
        <div className="p-6 rounded-3xl bg-[#0f172a] border border-slate-800 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-400" />
            Hybrid Retrieval & Reranking Tuning
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Reranker Engine
              </label>
              <select
                value={rerankerType}
                onChange={(e) => setRerankerType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="cross-encoder">Cross-Encoder (ms-marco-MiniLM-L-6-v2)</option>
                <option value="heuristic">BM25 + Token Overlap Heuristic</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Top-K Final Reranked Chunks
              </label>
              <input
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Chunk Size (Tokens)
              </label>
              <input
                type="number"
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-between pt-2">
          {saved && (
            <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-semibold">
              <CheckCircle2 className="w-4 h-4" /> Settings updated!
            </span>
          )}
          <div className="ml-auto">
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 flex items-center gap-2 transition-all cursor-pointer"
            >
              <Save className="w-4 h-4" />
              <span>Save Configuration</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
