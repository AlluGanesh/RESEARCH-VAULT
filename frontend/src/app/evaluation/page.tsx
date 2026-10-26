'use client';

import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Sliders,
  TrendingUp,
  Award,
  Play,
  Loader2,
  CheckCircle2,
  HelpCircle,
  Sparkles,
  Layers,
  Database,
  BarChart2,
  Cpu
} from 'lucide-react';
import { api } from '@/lib/api';
import { EvaluationDataset, EvaluationRun } from '@/types';
import { EvaluationDashboard } from '@/components/evaluation/EvaluationDashboard';
import { HallucinationInspector } from '@/components/evaluation/HallucinationInspector';
import { HybridRatioSimulator } from '@/components/evaluation/HybridRatioSimulator';
import { HybridBenchmarkDashboard } from '@/components/evaluation/HybridBenchmarkDashboard';

type TabKey = 'hallucination' | 'hybrid_simulator' | 'hybrid_benchmark' | 'runs';

export default function EvaluationPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('hallucination');
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null);

  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [dsList, runList] = await Promise.all([
        api.getEvaluationDatasets(),
        api.getEvaluationRuns()
      ]);
      setDatasets(dsList);
      setRuns(runList);
      if (dsList.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(dsList[0].id);
      }
      if (runList.length > 0 && !selectedRun) {
        setSelectedRun(runList[0]);
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

  const handleRunEvaluation = async () => {
    if (!selectedDatasetId || isRunning) return;
    setIsRunning(true);
    setError(null);
    try {
      const runRes = await api.runEvaluation({
        dataset_id: selectedDatasetId,
        top_k: 5
      });
      setSelectedRun(runRes);
      loadData();
    } catch (err: any) {
      setError(err.message || 'Evaluation run failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const currentDataset = datasets.find((d) => d.id === selectedDatasetId);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Research Intelligence & RAG Quality Lab</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          RAG Reliability & Evaluation Lab
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
          Comprehensive experimental suite for measuring claim-level hallucination rates, tuning hybrid dense/sparse fusion ratios with weighted RRF, and optimizing retrieval quality metrics against benchmark datasets.
        </p>
      </div>

      {/* Primary Tab Navigation */}
      <div className="flex border-b border-slate-800 gap-2 overflow-x-auto pb-1 text-xs">
        <button
          onClick={() => setActiveTab('hallucination')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl font-semibold transition-all border-b-2 cursor-pointer ${
            activeTab === 'hallucination'
              ? 'bg-[#0f172a] text-indigo-400 border-indigo-500 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 border-transparent hover:bg-slate-900/40'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Hallucination Detection</span>
          <span className="px-1.5 py-0.2 rounded bg-indigo-500/20 text-[10px] text-indigo-300 font-bold">
            Claims
          </span>
        </button>

        <button
          onClick={() => setActiveTab('hybrid_simulator')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl font-semibold transition-all border-b-2 cursor-pointer ${
            activeTab === 'hybrid_simulator'
              ? 'bg-[#0f172a] text-cyan-400 border-cyan-500 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 border-transparent hover:bg-slate-900/40'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>Hybrid Ratio Simulator</span>
          <span className="px-1.5 py-0.2 rounded bg-cyan-500/20 text-[10px] text-cyan-300 font-bold">
            RRF S(d)
          </span>
        </button>

        <button
          onClick={() => setActiveTab('hybrid_benchmark')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl font-semibold transition-all border-b-2 cursor-pointer ${
            activeTab === 'hybrid_benchmark'
              ? 'bg-[#0f172a] text-emerald-400 border-emerald-500 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 border-transparent hover:bg-slate-900/40'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>Retrieval Benchmark & Optimizer</span>
          <span className="px-1.5 py-0.2 rounded bg-emerald-500/20 text-[10px] text-emerald-300 font-bold">
            Curves
          </span>
        </button>

        <button
          onClick={() => setActiveTab('runs')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl font-semibold transition-all border-b-2 cursor-pointer ${
            activeTab === 'runs'
              ? 'bg-[#0f172a] text-purple-400 border-purple-500 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 border-transparent hover:bg-slate-900/40'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>End-to-End Evaluation Runs</span>
          <span className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] text-slate-300 font-mono">
            {runs.length}
          </span>
        </button>
      </div>

      {/* Tab 1: Hallucination Detection & Claim Lab */}
      {activeTab === 'hallucination' && <HallucinationInspector />}

      {/* Tab 2: Hybrid Ratio Simulator */}
      {activeTab === 'hybrid_simulator' && <HybridRatioSimulator />}

      {/* Tab 3: Retrieval Benchmark & Optimizer */}
      {activeTab === 'hybrid_benchmark' && (
        <HybridBenchmarkDashboard
          datasets={datasets}
          selectedDatasetId={selectedDatasetId}
          onSelectDatasetId={setSelectedDatasetId}
        />
      )}

      {/* Tab 4: Standard Evaluation Runs */}
      {activeTab === 'runs' && (
        <div className="space-y-6">
          <div className="p-6 rounded-3xl bg-[#0f172a] border border-slate-800 space-y-4 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Select Gold-Standard Dataset
                </h3>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 min-w-[280px]"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.test_case_count} Test Cases)
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleRunEvaluation}
                  disabled={isRunning || !selectedDatasetId}
                  className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-purple-600/20 flex items-center gap-2 transition-all cursor-pointer"
                >
                  {isRunning ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Benchmarking Full RAG Pipeline...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-white" />
                      <span>Execute Full Evaluation Run</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {currentDataset && (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="font-semibold text-slate-300">
                    Active Benchmark: {currentDataset.name}
                  </span>
                  <span className="font-mono text-indigo-400">
                    {currentDataset.test_cases ? currentDataset.test_cases.length : currentDataset.test_case_count} Questions
                  </span>
                </div>
                {currentDataset.description && (
                  <p className="text-[11px] text-slate-400 italic">
                    {currentDataset.description}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Historical Runs Selector */}
          {runs.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                Select Historical Evaluation Run to Inspect:
              </span>
              <div className="flex flex-wrap gap-2">
                {runs.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => setSelectedRun(r)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                      selectedRun?.id === r.id
                        ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                        : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {r.run_name || 'Evaluation Run'}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Run Dashboard */}
          {selectedRun && <EvaluationDashboard run={selectedRun} />}
        </div>
      )}
    </div>
  );
}
