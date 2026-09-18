'use client';

import React from 'react';
import { Columns, FileText, CheckCircle2, Bookmark } from 'lucide-react';
import { CompareResponse, Citation } from '@/types';

interface ComparisonMatrixProps {
  comparison: CompareResponse;
  onCitationClick: (citation: Citation) => void;
}

export function ComparisonMatrix({ comparison, onCitationClick }: ComparisonMatrixProps) {
  const citationMap = new Map<number, Citation>();
  comparison.citations.forEach((c) => citationMap.set(c.citation_number, c));

  return (
    <div className="space-y-6">
      {/* Overview Card */}
      <div className="p-6 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Columns className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-sm text-white">
              Comparative Analysis: {comparison.documents_compared_count} Documents
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Latency: {(comparison.latency_ms / 1000).toFixed(2)}s
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed pt-2">
          {comparison.summary_analysis.split('\n\n')[0]}
        </p>
      </div>

      {/* Structured Comparison Table */}
      <div className="rounded-2xl bg-[#0b0f19] border border-slate-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-300 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4 min-w-[200px]">Document</th>
                <th className="p-4 min-w-[220px]">Methodology</th>
                <th className="p-4 min-w-[200px]">Model / Approach</th>
                <th className="p-4 min-w-[180px]">Datasets</th>
                <th className="p-4 min-w-[220px]">Key Results</th>
                <th className="p-4 min-w-[200px]">Limitations</th>
                <th className="p-4 min-w-[100px] text-center">Citations</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {comparison.matrix_rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-4 font-semibold text-white align-top">
                    <div className="flex items-start gap-2">
                      <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <span>{row.document_title}</span>
                    </div>
                  </td>
                  <td className="p-4 align-top leading-relaxed">{row.methodology}</td>
                  <td className="p-4 align-top leading-relaxed text-indigo-300 font-mono text-[11px]">{row.architecture_or_approach}</td>
                  <td className="p-4 align-top leading-relaxed text-slate-400">{row.datasets_used}</td>
                  <td className="p-4 align-top leading-relaxed text-emerald-300 font-medium">{row.key_results}</td>
                  <td className="p-4 align-top leading-relaxed text-amber-300/90 text-[11px]">{row.limitations}</td>
                  <td className="p-4 align-top text-center">
                    <div className="flex flex-wrap justify-center gap-1">
                      {row.citation_numbers.map((num) => {
                        const cite = citationMap.get(num);
                        return (
                          <button
                            key={num}
                            onClick={() => cite && onCitationClick(cite)}
                            className="citation-badge"
                            title={cite ? `${cite.document_title} - Page ${cite.page_number}` : `Source [${num}]`}
                          >
                            [{num}]
                          </button>
                        );
                      })}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
