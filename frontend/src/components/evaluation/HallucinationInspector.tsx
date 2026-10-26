'use client';

import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Play,
  RotateCcw,
  Sparkles,
  ChevronDown,
  ChevronUp,
  FileText,
  BookmarkCheck,
  Scale,
  Award,
  Loader2,
  Copy,
  Check
} from 'lucide-react';
import { api } from '@/lib/api';
import { HallucinationReport, HumanBenchmarkReport } from '@/types';

const SAMPLE_PRESETS = [
  {
    name: 'Sample 1: Realistic Transformer Answer (1 Unsupported Claim)',
    query: 'What is the architecture and performance of the Transformer model?',
    answer: `The Transformer relies entirely on self-attention mechanisms, dispensing with recurrence and convolutions entirely [1]. It was evaluated on the WMT 2014 English-to-German translation task where the big model achieved a state-of-the-art BLEU score of 28.4 [1]. Additionally, the architecture incorporates multi-head attention to attend to information from different representation subspaces [1]. The authors also demonstrated zero-shot quantum language reasoning on IBM Q-System processors.`
  },
  {
    name: 'Sample 2: Contradicted Numeric Claim',
    query: 'What BLEU score did the big Transformer model achieve?',
    answer: `On the WMT 2014 English-to-German translation task, the Transformer achieved a state-of-the-art BLEU score of 52.4 [1]. The model relies on scaled dot-product attention to prevent gradients from vanishing in high dimensions [1].`
  },
  {
    name: 'Sample 3: Self-RAG & Reflection Tokens (Fully Grounded)',
    query: 'How does Self-RAG mitigate hallucination?',
    answer: `Self-RAG introduces special reflection tokens including [Retrieve], [IsRel], [IsSup], and [IsUse] [1]. The framework enables language models to adaptively retrieve passages on-demand rather than retrieving unconditionally [1]. Across open-domain QA and reasoning benchmarks like ARC and GSM8K, Self-RAG significantly outperforms standard RAG while reducing unnecessary retrieval steps by over 60% [1].`
  }
];

export function HallucinationInspector() {
  const [query, setQuery] = useState(SAMPLE_PRESETS[0].query);
  const [answerText, setAnswerText] = useState(SAMPLE_PRESETS[0].answer);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<HallucinationReport | null>(null);
  const [expandedClaimId, setExpandedClaimId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Human benchmark states
  const [benchLoading, setBenchLoading] = useState(false);
  const [benchReport, setBenchReport] = useState<HumanBenchmarkReport | null>(null);
  const [showBenchModal, setShowBenchModal] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleRunAudit = async () => {
    if (!answerText.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.detectHallucinations({
        answer_text: answerText,
        query: query.trim() || undefined
      });
      setReport(res);
      if (res.verified_claims.length > 0) {
        setExpandedClaimId(res.verified_claims[0].claim_id);
      }
    } catch (err: any) {
      setError(err.message || 'Hallucination audit execution failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunHumanBenchmark = async () => {
    setBenchLoading(true);
    try {
      const res = await api.runHumanBenchmark();
      setBenchReport(res);
      setShowBenchModal(true);
    } catch (err: any) {
      setError(err.message || 'Failed running human gold benchmark.');
    } finally {
      setBenchLoading(false);
    }
  };

  const loadPreset = (preset: typeof SAMPLE_PRESETS[0]) => {
    setQuery(preset.query);
    setAnswerText(preset.answer);
    setReport(null);
  };

  return (
    <div className="space-y-6">
      {/* Visual Pipeline Banner */}
      <div className="p-5 rounded-2xl bg-[#0f172a] border border-slate-800 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold mb-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Claim-Level Verification Engine</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Sentence-Level Hallucination Detection & Scoring
            </h2>
            <p className="text-xs text-slate-400 mt-0.5 max-w-2xl">
              Deconstructs generated AI answers into discrete atomic claims, verifies each claim against retrieved evidence passages, and calculates the true Hallucination Rate: (Unsupported + Contradicted) / Total Claims.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRunHumanBenchmark}
              disabled={benchLoading}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-all cursor-pointer"
            >
              {benchLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
              ) : (
                <Award className="w-3.5 h-3.5 text-amber-400" />
              )}
              <span>Evaluate vs Human Gold Labels</span>
            </button>
          </div>
        </div>

        {/* Verification Pipeline Step Flow */}
        <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-2 pt-4 border-t border-slate-800/80 text-[11px]">
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-400 flex items-center justify-center font-bold text-[10px]">1</div>
            <div>
              <span className="font-semibold text-slate-300 block">Claim Extraction</span>
              <span className="text-[10px] text-slate-500">Atomic clause isolation</span>
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-cyan-600/30 text-cyan-400 flex items-center justify-center font-bold text-[10px]">2</div>
            <div>
              <span className="font-semibold text-slate-300 block">Evidence Match</span>
              <span className="text-[10px] text-slate-500">Cited passage attribution</span>
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-purple-600/30 text-purple-400 flex items-center justify-center font-bold text-[10px]">3</div>
            <div>
              <span className="font-semibold text-slate-300 block">NLI Verification</span>
              <span className="text-[10px] text-slate-500">Supported vs Contradicted</span>
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-emerald-600/30 text-emerald-400 flex items-center justify-center font-bold text-[10px]">4</div>
            <div>
              <span className="font-semibold text-slate-300 block">Scoring & Citations</span>
              <span className="text-[10px] text-slate-500">Separates false & unsupported</span>
            </div>
          </div>
        </div>
      </div>

      {/* Input Workspace & Presets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-5 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-400" />
              Generated AI Answer to Audit
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-slate-500">Load sample:</span>
              <select
                onChange={(e) => {
                  const idx = parseInt(e.target.value);
                  if (!isNaN(idx)) loadPreset(SAMPLE_PRESETS[idx]);
                }}
                className="bg-slate-900 border border-slate-800 text-[11px] text-slate-300 rounded-lg px-2.5 py-1 focus:outline-none focus:border-indigo-500"
              >
                {SAMPLE_PRESETS.map((p, i) => (
                  <option key={i} value={i}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-400">Target Query / Prompt Context</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What is the architecture of the Transformer model?"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-400">AI Response Content (with citations [1], [2])</label>
            <textarea
              rows={5}
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder="Paste generated response text here..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-xs text-slate-200 font-sans focus:outline-none focus:border-indigo-500 leading-relaxed"
            />
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <button
              onClick={() => {
                setAnswerText('');
                setReport(null);
              }}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              Clear Text
            </button>
            <button
              onClick={handleRunAudit}
              disabled={loading || !answerText.trim()}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 flex items-center gap-2 transition-all cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying Claims & NLI Evidence...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Inspect & Score Hallucinations</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Live Scorecards Panel */}
        <div className="p-5 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Answer Reliability
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                {report ? `${report.execution_time_ms}ms` : 'Ready'}
              </span>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3">
              {/* Hallucination Rate */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block">Hallucination Rate</span>
                <div className={`text-2xl font-extrabold font-mono ${
                  report
                    ? report.hallucination_rate === 0
                      ? 'text-emerald-400'
                      : report.hallucination_rate > 25
                      ? 'text-rose-400'
                      : 'text-amber-400'
                    : 'text-slate-400'
                }`}>
                  {report ? `${report.hallucination_rate}%` : '—'}
                </div>
                <span className="text-[9px] text-slate-500 block">Unsupported + Contradicted</span>
              </div>

              {/* Claim Support */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block">Claim Support</span>
                <div className="text-2xl font-extrabold font-mono text-emerald-400">
                  {report ? `${report.claim_support_rate}%` : '—'}
                </div>
                <span className="text-[9px] text-slate-500 block">Directly Grounded</span>
              </div>

              {/* Contradiction Rate */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block">Contradiction Rate</span>
                <div className={`text-2xl font-extrabold font-mono ${
                  report && report.contradiction_rate > 0 ? 'text-rose-400' : 'text-slate-400'
                }`}>
                  {report ? `${report.contradiction_rate}%` : '—'}
                </div>
                <span className="text-[9px] text-slate-500 block">Explicitly Refuted</span>
              </div>

              {/* Claims Checked */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block">Claims Checked</span>
                <div className="text-2xl font-extrabold font-mono text-cyan-400">
                  {report ? report.total_claims : '—'}
                </div>
                <span className="text-[9px] text-slate-500 block">
                  {report ? `${report.supported_count} of ${report.total_claims} supported` : 'Sentence level'}
                </span>
              </div>
            </div>
          </div>

          {/* Mathematical Formula Footnote */}
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 text-[10px] text-slate-400 font-mono space-y-1">
            <div className="text-slate-300 font-semibold">Reliability Formula:</div>
            <div>Hallucination Rate = (Unsupported + Contradicted) / Total Claims × 100</div>
          </div>
        </div>
      </div>

      {/* Claim Breakdown Inspection Table */}
      {report && (
        <div className="p-6 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Claim Verification Audit ({report.verified_claims.length} Claims Identified)
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Every atomic proposition extracted from the response with its verification verdict, citation ground, and evidence passage snippet.
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                {report.supported_count} Supported
              </span>
              <span className="inline-flex items-center gap-1 text-rose-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                {report.contradicted_count} Contradicted
              </span>
              <span className="inline-flex items-center gap-1 text-amber-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                {report.unverifiable_count} Unsupported
              </span>
            </div>
          </div>

          <div className="space-y-3">
            {report.verified_claims.map((item, idx) => {
              const isExpanded = expandedClaimId === item.claim_id;
              const isSupported = item.verdict === 'SUPPORTED';
              const isContradicted = item.verdict === 'CONTRADICTED';
              const isUnverifiable = item.verdict === 'UNVERIFIABLE';

              return (
                <div
                  key={item.claim_id}
                  className={`rounded-xl border transition-all ${
                    isSupported
                      ? 'bg-slate-950/70 border-emerald-950/40 hover:border-emerald-500/30'
                      : isContradicted
                      ? 'bg-rose-950/10 border-rose-900/40 hover:border-rose-500/40'
                      : 'bg-amber-950/10 border-amber-900/40 hover:border-amber-500/40'
                  }`}
                >
                  <div
                    onClick={() => setExpandedClaimId(isExpanded ? null : item.claim_id)}
                    className="p-4 flex items-start justify-between gap-4 cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5">
                        {isSupported && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                        {isContradicted && <AlertTriangle className="w-4 h-4 text-rose-400" />}
                        {isUnverifiable && <HelpCircle className="w-4 h-4 text-amber-400" />}
                      </div>
                      <div className="space-y-1">
                        <div className="text-xs font-semibold text-slate-200 leading-snug">
                          {item.claim_text}
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-[10px]">
                          <span className="font-mono text-slate-500">#{item.claim_id}</span>
                          {item.cited_indices.length > 0 ? (
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono">
                              Citations: {item.cited_indices.map((c) => `[${c}]`).join(', ')}
                            </span>
                          ) : (
                            <span className="text-slate-500 italic">No citations attached</span>
                          )}
                          {item.citation_valid && (
                            <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                              Citation Grounded
                            </span>
                          )}
                          <span className="text-slate-400">
                            Confidence: <strong className="text-slate-200">{(item.confidence * 100).toFixed(0)}%</strong>
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span
                        className={`px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide uppercase ${
                          isSupported
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : isContradicted
                            ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                            : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        {item.verdict}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Evidence Passage Drawer */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pt-1 border-t border-slate-800/60 bg-slate-950/40 space-y-2.5 text-xs">
                      {item.matched_doc_title && (
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                            <BookmarkCheck className="w-3.5 h-3.5 text-indigo-400" />
                            Source: {item.matched_doc_title}
                          </span>
                          {item.matched_chunk_id && (
                            <span className="font-mono text-slate-500 text-[10px]">
                              Chunk: {item.matched_chunk_id.slice(0, 8)}...
                            </span>
                          )}
                        </div>
                      )}

                      {item.evidence_snippet ? (
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                            Retrieved Corroborating Evidence Snippet
                          </span>
                          <p className="text-xs text-slate-300 italic leading-relaxed">
                            "{item.evidence_snippet}"
                          </p>
                        </div>
                      ) : (
                        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 text-[11px] text-amber-400/90 italic">
                          No direct passage in the retrieved context grounds or substantiates this assertion.
                        </div>
                      )}

                      {item.explanation && (
                        <div className="text-[11px] text-slate-400">
                          <strong className="text-slate-300 font-medium">NLI Judge Assessment: </strong>
                          {item.explanation}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Human Gold-Standard Benchmark Modal */}
      {showBenchModal && benchReport && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0b0f19] border border-slate-800 max-w-2xl w-full rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white">
                  Human-Labeled Gold Benchmark Evaluation
                </h3>
              </div>
              <button
                onClick={() => setShowBenchModal(false)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg bg-slate-800"
              >
                Close
              </button>
            </div>

            <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 flex items-center justify-between">
              <div>
                <span className="text-xs text-indigo-300 font-semibold block">Detector Agreement with Human Judges</span>
                <span className="text-[11px] text-slate-400">
                  {benchReport.correct_matches} of {benchReport.total_benchmark_cases} gold-standard human-verified claims correctly classified
                </span>
              </div>
              <div className="text-3xl font-extrabold font-mono text-emerald-400">
                {benchReport.benchmark_accuracy}%
              </div>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {benchReport.test_cases.map((tc) => (
                <div
                  key={tc.id}
                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200 max-w-md truncate">
                      {tc.claim}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        tc.is_match ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                      }`}
                    >
                      {tc.is_match ? 'Matched Gold' : 'Mismatch'}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-slate-400 font-mono">
                    <span>Gold Label: <strong className="text-amber-300">{tc.gold_verdict}</strong></span>
                    <span>Detector Verdict: <strong className="text-cyan-300">{tc.predicted_verdict}</strong></span>
                    <span>Confidence: {(tc.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowBenchModal(false)}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
              >
                Done Inspecting
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
