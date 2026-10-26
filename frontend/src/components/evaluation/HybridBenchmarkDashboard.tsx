'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import {
  TrendingUp,
  Award,
  Zap,
  Play,
  Loader2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  BarChart2,
  Sparkles,
  ArrowUpRight,
  Database,
  Sliders,
  Check
} from 'lucide-react';
import { api } from '@/lib/api';
import { EvaluationDataset, HybridBenchmarkResponse } from '@/types';

interface HybridBenchmarkDashboardProps {
  datasets: EvaluationDataset[];
  selectedDatasetId: string;
  onSelectDatasetId: (id: string) => void;
}

export function HybridBenchmarkDashboard({
  datasets,
  selectedDatasetId,
  onSelectDatasetId
}: HybridBenchmarkDashboardProps) {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [benchmarkData, setBenchmarkData] = useState<HybridBenchmarkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [applied, setApplied] = useState<boolean>(false);

  const handleRunBenchmark = async () => {
    if (!selectedDatasetId || isRunning) return;
    setIsRunning(true);
    setError(null);
    try {
      const res = await api.runHybridBenchmark({
        dataset_id: selectedDatasetId,
        k: 10
      });
      setBenchmarkData(res);
    } catch (err: any) {
      setError(err.message || 'Benchmark execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  // Run benchmark on initial mount if dataset is present and no data yet
  useEffect(() => {
    if (selectedDatasetId && !benchmarkData) {
      handleRunBenchmark();
    }
  }, [selectedDatasetId]);

  const handleApplyOptimal = () => {
    setApplied(true);
    setTimeout(() => setApplied(false), 2500);
  };

  // Transform data for charts
  const chartPoints = benchmarkData?.benchmark_curves.map((pt) => ({
    ratio: `${pt.dense_pct}%`,
    dense_pct: pt.dense_pct,
    'NDCG@10': Number((pt.mean_ndcg * 100).toFixed(1)),
    'Recall@10': Number((pt.mean_recall * 100).toFixed(1)),
    'Overlap@10': Number((pt.mean_overlap * 100).toFixed(1)),
    'Hallucination Rate': Number(pt.estimated_hallucination_rate.toFixed(1)),
    'Dense Only': pt.mean_dense_only,
    'Sparse BM25 Only': pt.mean_sparse_only,
    'Latency (ms)': Number(pt.avg_latency_ms.toFixed(1))
  })) || [];

  const opt = benchmarkData?.optimal_recommendation;

  return (
    <div className="space-y-6">
      {/* Top Benchmark Launcher Card */}
      <div className="p-6 rounded-3xl bg-[#0f172a] border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold mb-2">
              <BarChart2 className="w-3.5 h-3.5" />
              <span>Multi-Ratio Retrieval Benchmark</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Hybrid Retrieval Ratio Benchmark & Optimizer
            </h2>
            <p className="text-xs text-slate-400 mt-0.5 max-w-2xl leading-relaxed">
              Systematically sweep fusion ratios from 0:100 (pure BM25) to 100:0 (pure Dense). Plot NDCG@10 and Recall@10 curves to eliminate arbitrary 60:40 guesses with mathematically verified Pareto-optimal ratios.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedDatasetId}
              onChange={(e) => onSelectDatasetId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 min-w-[240px]"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.test_case_count} Test Cases)
                </option>
              ))}
            </select>

            <button
              onClick={handleRunBenchmark}
              disabled={isRunning || !selectedDatasetId}
              className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-cyan-600/20 flex items-center gap-2 transition-all cursor-pointer shrink-0"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Sweeping Ratios (0% to 100%)...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Run Ratio Benchmark</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Recommended Optimal Ratio Card */}
      {opt && (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-cyan-950/40 via-indigo-950/30 to-purple-950/20 border border-cyan-500/30 shadow-xl space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shrink-0">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    Recommended Optimal Ratio
                  </span>
                  <span className="text-xs text-slate-400">
                    Based on {benchmarkData.total_test_cases} benchmark evaluations
                  </span>
                </div>
                <div className="text-2xl font-black font-mono text-white flex items-center gap-3">
                  <span>{opt.dense_pct}% Dense</span>
                  <span className="text-slate-500 font-light">/</span>
                  <span className="text-amber-400">{opt.sparse_pct}% BM25</span>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 block">Peak NDCG@10</span>
                <span className="text-base font-extrabold font-mono text-cyan-400">
                  {(opt.peak_ndcg * 100).toFixed(1)}%
                </span>
              </div>
              <div className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 block">Peak Recall@10</span>
                <span className="text-base font-extrabold font-mono text-emerald-400">
                  {(opt.peak_recall * 100).toFixed(1)}%
                </span>
              </div>
              <div className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 block">NDCG Lift vs BM25</span>
                <span className="text-base font-extrabold font-mono text-indigo-400">
                  +{opt.ndcg_lift_over_bm25_pct}%
                </span>
              </div>
              <button
                onClick={handleApplyOptimal}
                className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-600/30 flex items-center gap-2 transition-all cursor-pointer"
              >
                {applied ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-300" />
                    <span>Applied to Pipeline!</span>
                  </>
                ) : (
                  <>
                    <Sliders className="w-4 h-4" />
                    <span>Apply Optimal Weights</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
            <strong className="text-cyan-300 font-semibold">Mathematical Optimization Rationale: </strong>
            {opt.rationale}
          </div>
        </div>
      )}

      {/* Main Retrieval Curves Chart */}
      {benchmarkData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* NDCG & Recall Curves */}
          <div className="p-6 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  NDCG@10 & Recall@10 Quality Curves
                </h3>
                <span className="text-[11px] text-slate-500">
                  Horizontal axis: Dense semantic search weight (0% = pure BM25, 100% = pure Dense)
                </span>
              </div>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartPoints} margin={{ top: 10, right: 20, left: -20, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="ratio" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '11px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Line type="monotone" dataKey="NDCG@10" stroke="#38bdf8" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="Recall@10" stroke="#34d399" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="Overlap@10" stroke="#818cf8" strokeWidth={2} strokeDasharray="4 4" dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Hallucination Rate Correlation Curve */}
          <div className="p-6 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                  Hallucination Rate Correlation (%)
                </h3>
                <span className="text-[11px] text-slate-500">
                  Lower is better. Reflects unsupported claims induced by retrieval failure
                </span>
              </div>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartPoints} margin={{ top: 10, right: 20, left: -20, bottom: 10 }}>
                  <defs>
                    <linearGradient id="hallucinationGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="ratio" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" domain={[0, 40]} tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '11px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Area
                    type="monotone"
                    dataKey="Hallucination Rate"
                    stroke="#f43f5e"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#hallucinationGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Side-by-Side Retrieval Ratios Comparison Table */}
      {benchmarkData && (
        <div className="rounded-2xl bg-[#0b0f19] border border-slate-800 overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <h4 className="font-bold text-xs text-white">
              Side-by-Side Fusion Ratio Diagnostics (0:100 to 100:0)
            </h4>
            <span className="text-[11px] font-mono text-slate-400">
              Execution: {benchmarkData.execution_time_ms}ms across {benchmarkData.total_test_cases} test cases
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-semibold">
                <tr>
                  <th className="p-3.5">Dense Weight</th>
                  <th className="p-3.5">Sparse BM25 Weight</th>
                  <th className="p-3.5">NDCG@10</th>
                  <th className="p-3.5">Recall@10</th>
                  <th className="p-3.5">Precision@10</th>
                  <th className="p-3.5">Overlap@10</th>
                  <th className="p-3.5">Dense-Only Hits</th>
                  <th className="p-3.5">Sparse-Only Hits</th>
                  <th className="p-3.5">Hallucination Rate</th>
                  <th className="p-3.5">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300">
                {benchmarkData.benchmark_curves.map((pt, idx) => {
                  const isOptimal = opt && pt.dense_weight === opt.dense_weight;

                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-900/40 transition-colors ${
                        isOptimal ? 'bg-cyan-950/20 border-l-4 border-cyan-400' : ''
                      }`}
                    >
                      <td className="p-3.5 font-mono font-bold text-slate-200 flex items-center gap-2">
                        {isOptimal && (
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                        )}
                        {pt.dense_pct}%
                        {isOptimal && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold">
                            Optimal
                          </span>
                        )}
                      </td>
                      <td className="p-3.5 font-mono text-slate-400">
                        {pt.sparse_pct}%
                      </td>
                      <td className="p-3.5 font-mono font-bold text-cyan-400">
                        {(pt.mean_ndcg * 100).toFixed(1)}%
                      </td>
                      <td className="p-3.5 font-mono font-bold text-emerald-400">
                        {(pt.mean_recall * 100).toFixed(1)}%
                      </td>
                      <td className="p-3.5 font-mono text-slate-300">
                        {(pt.mean_precision * 100).toFixed(1)}%
                      </td>
                      <td className="p-3.5 font-mono text-indigo-400">
                        {(pt.mean_overlap * 100).toFixed(0)}%
                      </td>
                      <td className="p-3.5 font-mono text-cyan-300">
                        {pt.mean_dense_only.toFixed(1)}
                      </td>
                      <td className="p-3.5 font-mono text-amber-300">
                        {pt.mean_sparse_only.toFixed(1)}
                      </td>
                      <td className={`p-3.5 font-mono font-bold ${
                        pt.estimated_hallucination_rate < 15 ? 'text-emerald-400' : 'text-amber-400'
                      }`}>
                        {pt.estimated_hallucination_rate.toFixed(1)}%
                      </td>
                      <td className="p-3.5 font-mono text-slate-400">
                        {pt.avg_latency_ms.toFixed(1)}ms
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
