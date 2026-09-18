'use client';

import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { Award, Target, CheckCircle2, ShieldCheck, Activity, Cpu } from 'lucide-react';
import { EvaluationRun } from '@/types';

interface EvaluationDashboardProps {
  run: EvaluationRun;
}

export function EvaluationDashboard({ run }: EvaluationDashboardProps) {
  const chartData = [
    { name: 'Precision@K', value: Number((run.mean_precision_at_k * 100).toFixed(1)), fullMark: 100 },
    { name: 'Recall@K', value: Number((run.mean_recall_at_k * 100).toFixed(1)), fullMark: 100 },
    { name: 'MRR', value: Number((run.mean_mrr * 100).toFixed(1)), fullMark: 100 },
    { name: 'NDCG', value: Number((run.mean_ndcg * 100).toFixed(1)), fullMark: 100 },
    { name: 'Faithfulness', value: Number((run.mean_faithfulness * 100).toFixed(1)), fullMark: 100 },
    { name: 'Answer Rel.', value: Number((run.mean_answer_relevance * 100).toFixed(1)), fullMark: 100 },
    { name: 'Citation Acc.', value: Number((run.mean_citation_accuracy * 100).toFixed(1)), fullMark: 100 },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner Metric Scorecards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Precision@5</span>
            <Target className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {(run.mean_precision_at_k * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] text-slate-500 block">Retrieval Hit Density</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Recall@5</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {(run.mean_recall_at_k * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] text-slate-500 block">Ground-Truth Coverage</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Mean NDCG</span>
            <Award className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-400">
            {(run.mean_ndcg * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] text-slate-500 block">Discounted Ranking Gain</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Faithfulness</span>
            <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-purple-400">
            {(run.mean_faithfulness * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] text-slate-500 block">Hallucination Resistance</span>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="p-6 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-400" />
            Quantitative Metric Breakdown (%)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} interval={0} angle={-25} textAnchor="end" />
                <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Radar Quality Polygon */}
        <div className="p-6 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            RAG Holistic Quality Polygon
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData}>
                <PolarGrid stroke="#1e293b" />
                <PolarAngleAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 9 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" tick={{ fontSize: 8 }} />
                <Radar name="Performance" dataKey="value" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Per-Question Results Table */}
      <div className="rounded-2xl bg-[#0b0f19] border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <h4 className="font-bold text-xs text-white">
            Per-Question Grounded Benchmark Results ({run.results.length} Test Cases)
          </h4>
          <span className="text-[11px] font-mono text-slate-400">
            Engine: {run.embedding_provider} + {run.reranker_used}
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-semibold">
              <tr>
                <th className="p-3.5">Question</th>
                <th className="p-3.5">Precision@K</th>
                <th className="p-3.5">Recall@K</th>
                <th className="p-3.5">Faithfulness</th>
                <th className="p-3.5">Citation Acc.</th>
                <th className="p-3.5">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {run.results.map((res, idx) => (
                <tr key={idx} className="hover:bg-slate-900/40">
                  <td className="p-3.5 max-w-xs truncate font-medium text-slate-200" title={res.question}>
                    {res.question}
                  </td>
                  <td className="p-3.5 font-mono text-indigo-400 font-bold">
                    {(res.precision_at_k * 100).toFixed(0)}%
                  </td>
                  <td className="p-3.5 font-mono text-emerald-400 font-bold">
                    {(res.recall_at_k * 100).toFixed(0)}%
                  </td>
                  <td className="p-3.5 font-mono text-purple-400 font-bold">
                    {(res.faithfulness_score * 100).toFixed(0)}%
                  </td>
                  <td className="p-3.5 font-mono text-cyan-400 font-bold">
                    {(res.citation_accuracy * 100).toFixed(0)}%
                  </td>
                  <td className="p-3.5 font-mono text-slate-400">
                    {res.latency_ms.toFixed(0)}ms
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
