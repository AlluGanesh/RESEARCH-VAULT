'use client';

import React, { useState, useEffect } from 'react';
import { Columns, FileText, CheckCircle2, Loader2, AlertCircle, Plus } from 'lucide-react';
import { api } from '@/lib/api';
import { Document, CompareResponse, Citation } from '@/types';
import { ComparisonMatrix } from '@/components/compare/ComparisonMatrix';
import { SourceInspectorDrawer } from '@/components/chat/SourceInspectorDrawer';

export default function ComparePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [customQuestion, setCustomQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  useEffect(() => {
    api.getDocuments().then((docs) => {
      setDocuments(docs);
      if (docs.length >= 2) {
        setSelectedDocIds([docs[0].id, docs[1].id]);
      } else if (docs.length === 1) {
        setSelectedDocIds([docs[0].id]);
      }
    }).catch(console.error);
  }, []);

  const toggleDocSelection = (id: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const handleRunComparison = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedDocIds.length < 1) {
      setError('Please select at least 1 document to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    setComparison(null);

    try {
      const res = await api.compareDocuments({
        document_ids: selectedDocIds,
        question: customQuestion.trim() || undefined
      });
      setComparison(res);
    } catch (err: any) {
      setError(err.message || 'Comparison failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold mb-2">
          <Columns className="w-3.5 h-3.5" />
          <span>Cross-Paper Comparative Analysis</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Document Comparison Matrix
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
          Select multiple research papers to automatically extract and compare methodologies, dataset benchmarks, key findings, and architectural trade-offs side-by-side.
        </p>
      </div>

      {/* Document Selection Grid */}
      <div className="p-6 rounded-3xl bg-[#0f172a] border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Select Documents to Compare ({selectedDocIds.length} Selected)
          </h3>
          <span className="text-xs text-slate-500">Pick 2 to 5 research papers</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <div
                key={doc.id}
                onClick={() => toggleDocSelection(doc.id)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-start justify-between gap-2 ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500/60 shadow-sm'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase block">
                    {doc.file_type} • {doc.chunk_count} chunks
                  </span>
                  <h4 className="text-xs font-semibold text-slate-200 line-clamp-2">
                    {doc.title}
                  </h4>
                  {doc.author && (
                    <p className="text-[11px] text-slate-500 line-clamp-1">{doc.author}</p>
                  )}
                </div>

                <div
                  className={`w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 transition-colors ${
                    isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-800 border border-slate-700'
                  }`}
                >
                  {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                </div>
              </div>
            );
          })}
        </div>

        {/* Custom Comparison Focus Prompt */}
        <form onSubmit={handleRunComparison} className="pt-2 flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={customQuestion}
            onChange={(e) => setCustomQuestion(e.target.value)}
            placeholder="Focus inquiry: (e.g. Compare evaluation datasets, model architectures, and latency trade-offs)"
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={loading || selectedDocIds.length < 1}
            className="px-6 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-cyan-600/20 flex items-center justify-center gap-2 transition-all cursor-pointer flex-shrink-0"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Comparing...</span>
              </>
            ) : (
              <>
                <Columns className="w-4 h-4" />
                <span>Generate Matrix</span>
              </>
            )}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <ComparisonMatrix
          comparison={comparison}
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
