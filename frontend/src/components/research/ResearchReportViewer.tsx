'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Sparkles,
  Layers,
  CheckCircle2,
  AlertOctagon,
  HelpCircle,
  Clock,
  Zap,
  Download,
  Copy
} from 'lucide-react';
import { ResearchResponse, Citation } from '@/types';

interface ResearchReportViewerProps {
  report: ResearchResponse;
  onCitationClick: (citation: Citation) => void;
}

export function ResearchReportViewer({ report, onCitationClick }: ResearchReportViewerProps) {
  const copyMarkdown = () => {
    navigator.clipboard.writeText(report.markdown_report);
    alert('Research Report Markdown copied to clipboard!');
  };

  const citationMap = new Map<number, Citation>();
  report.citations.forEach((c) => citationMap.set(c.citation_number, c));

  return (
    <div className="space-y-6">
      {/* Top Banner Stats */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-slate-900 to-[#0a0f1d] border border-indigo-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl shadow-indigo-500/5">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs uppercase tracking-wider font-bold text-indigo-400">
              Multi-Hop Deep Research Synthesis
            </span>
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">
            {report.query}
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-right">
            <span className="block text-[10px] text-slate-400 uppercase font-medium">Latency</span>
            <span className="text-xs font-mono font-bold text-emerald-400">
              {(report.latency_ms / 1000).toFixed(2)}s
            </span>
          </div>

          <div className="px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-right">
            <span className="block text-[10px] text-slate-400 uppercase font-medium">Evidence Passages</span>
            <span className="text-xs font-mono font-bold text-indigo-400">
              {report.citations.length} Citations
            </span>
          </div>

          <button
            onClick={copyMarkdown}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>Copy Markdown</span>
          </button>
        </div>
      </div>

      {/* Multi-Step Inquiry Decomposition Accordion */}
      <div className="space-y-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          Research Planner & Sub-Question Inquiries
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {report.plan_steps.map((step) => (
            <div
              key={step.step_number}
              className="p-4 rounded-xl bg-[#0f172a]/70 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                    Step 0{step.step_number}
                  </span>
                  <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> {step.retrieved_chunks_count} Chunks
                  </span>
                </div>
                <h4 className="text-xs font-semibold text-slate-200 leading-snug mb-1">
                  {step.sub_question}
                </h4>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {step.rationale}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Findings Pills */}
      {report.key_findings && report.key_findings.length > 0 && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            Core Empirical Takeaways
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {report.key_findings.map((f, i) => (
              <div
                key={i}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 leading-relaxed flex items-start gap-2.5"
              >
                <span className="w-5 h-5 rounded-full bg-indigo-600/20 text-indigo-400 text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span>{f}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contradiction & Divergence Box (if present) */}
      {report.contradictions && report.contradictions.length > 0 && (
        <div className="p-5 rounded-2xl bg-amber-950/15 border border-amber-500/30 space-y-3">
          <div className="flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400">
              Cross-Document Contradiction / Diverging Findings
            </h3>
          </div>
          {report.contradictions.map((c, i) => (
            <div key={i} className="space-y-2 p-3.5 rounded-xl bg-slate-950/40 border border-amber-500/20 text-xs">
              <h4 className="font-semibold text-amber-200">{c.topic}</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] font-bold text-indigo-400 block mb-1">Perspective A ({c.perspective_a_source})</span>
                  <p className="text-slate-300">{c.perspective_a}</p>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] font-bold text-cyan-400 block mb-1">Perspective B ({c.perspective_b_source})</span>
                  <p className="text-slate-300">{c.perspective_b}</p>
                </div>
              </div>
              <p className="text-[11px] text-slate-400 italic pt-1">
                Analysis: {c.analysis}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Full Synthesis Report Body */}
      <div className="p-6 rounded-2xl bg-[#0d1322] border border-slate-800 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800">
          Synthesized Scientific Report
        </h3>
        <div className="prose prose-invert prose-indigo max-w-none text-xs leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ node, ...props }) => <a className="text-indigo-400 underline" {...props} />,
              p: ({ children }) => {
                // Parse inline citation numbers [1]
                const content = React.Children.toArray(children);
                return (
                  <p className="text-slate-200 text-xs leading-relaxed mb-3">
                    {content.map((item, idx) => {
                      if (typeof item === 'string') {
                        const parts = item.split(/(\[\d+\])/g);
                        return parts.map((part, pIdx) => {
                          const match = part.match(/^\[(\d+)\]$/);
                          if (match) {
                            const num = parseInt(match[1], 10);
                            const cite = citationMap.get(num);
                            return (
                              <button
                                key={pIdx}
                                onClick={() => cite && onCitationClick(cite)}
                                className="citation-badge"
                                title={cite ? `${cite.document_title} - Page ${cite.page_number}` : `Source [${num}]`}
                              >
                                [{num}]
                              </button>
                            );
                          }
                          return part;
                        });
                      }
                      return item;
                    })}
                  </p>
                );
              }
            }}
          >
            {report.markdown_report}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
