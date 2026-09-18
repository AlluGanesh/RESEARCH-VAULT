'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, Layers, Send, Loader2, BookOpen, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { ResearchResponse, Collection, Citation } from '@/types';
import { ResearchReportViewer } from '@/components/research/ResearchReportViewer';
import { SourceInspectorDrawer } from '@/components/chat/SourceInspectorDrawer';

export default function ResearchPage() {
  const [query, setQuery] = useState('');
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('');
  
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  useEffect(() => {
    api.getCollections().then(setCollections).catch(console.error);
  }, []);

  const handleRunResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const res = await api.runResearch({
        query: query.trim(),
        collection_id: selectedCollectionId || undefined,
        depth: 'comprehensive'
      });
      setReport(res);
    } catch (err: any) {
      setError(err.message || 'Research synthesis failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multi-Hop Autonomous Research Agent</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Deep Research Mode
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
          Executes automated research planning: decomposes complex topics into structured sub-questions, executes parallel hybrid retrievals, aggregates evidence, detects contradictions, and synthesizes an academic report.
        </p>
      </div>

      {/* Query & Scope Bar */}
      <div className="p-6 rounded-3xl bg-[#0f172a] border border-slate-800 space-y-4 shadow-xl">
        <form onSubmit={handleRunResearch} className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Compare architectural approaches for reducing hallucination in Large Language Models"
                disabled={loading}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors font-medium"
              />
            </div>

            <div className="w-full md:w-64">
              <select
                value={selectedCollectionId}
                onChange={(e) => setSelectedCollectionId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Collections (Corpus-Wide)</option>
                {collections.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-purple-600/20 flex items-center justify-center gap-2 transition-all cursor-pointer flex-shrink-0"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Synthesizing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Execute Research</span>
                </>
              )}
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
            <span className="font-semibold text-slate-500">Suggested Topics:</span>
            {[
              'Approaches for reducing hallucination in LLMs',
              'Scaled dot-product attention in Transformer scaling',
              'Self-reflective retrieval and adaptive generation'
            ].map((topic, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setQuery(topic)}
                className="hover:text-purple-400 hover:underline text-slate-400"
              >
                {topic} •
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state indicator */}
      {loading && (
        <div className="p-12 rounded-3xl bg-[#0b0f19] border border-slate-800 text-center space-y-4">
          <Loader2 className="w-10 h-10 text-purple-400 animate-spin mx-auto" />
          <h3 className="text-sm font-bold text-white">Research Planner in Progress</h3>
          <div className="max-w-md mx-auto space-y-2 text-xs text-slate-400">
            <p className="animate-pulse">1. Decomposing research topic into multi-hop sub-questions...</p>
            <p className="animate-pulse delay-100">2. Executing parallel vector and lexical hybrid retrievals...</p>
            <p className="animate-pulse delay-200">3. Performing cross-document synthesis & contradiction analysis...</p>
          </div>
        </div>
      )}

      {/* Report Viewer */}
      {report && (
        <ResearchReportViewer
          report={report}
          onCitationClick={setSelectedCitation}
        />
      )}

      {/* Source Drawer */}
      <SourceInspectorDrawer
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
