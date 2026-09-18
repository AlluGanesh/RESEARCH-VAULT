'use client';

import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  Award,
  Play,
  Plus,
  Loader2,
  Activity,
  Layers,
  Database,
  HelpCircle,
  FileQuestion
} from 'lucide-react';
import { api } from '@/lib/api';
import { EvaluationDataset, EvaluationRun } from '@/types';
import { EvaluationDashboard } from '@/components/evaluation/EvaluationDashboard';

export default function EvaluationPage() {
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
      setError(err.message || 'Evaluation failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const currentDataset = datasets.find((d) => d.id === selectedDatasetId);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-2">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Automated RAG Benchmarking Suite</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          RAG Evaluation Studio
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
          Benchmark and compute actual mathematical evaluation metrics: Precision@K, Recall@K, Mean Reciprocal Rank (MRR), Normalized Discounted Cumulative Gain (NDCG), Faithfulness, and Citation Accuracy against gold-standard evaluation datasets.
        </p>
      </div>

      {/* Benchmark Control Bar */}
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
              className="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 flex items-center gap-2 transition-all cursor-pointer"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Benchmarking RAG Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Execute Benchmark Run</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Dataset Test Cases Preview */}
        {currentDataset && (
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="font-semibold text-slate-300">
                Active Benchmark: {currentDataset.name}
              </span>
              <span className="font-mono text-indigo-400">
                {currentDataset.test_cases ? currentDataset.test_cases.length : currentDataset.test_case_count} Gold Questions
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

      {/* Historical Runs Selector Pills */}
      {runs.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
            Select Evaluation Run to Inspect:
          </span>
          <div className="flex flex-wrap gap-2">
            {runs.map((r) => (
              <button
                key={r.id}
                onClick={() => setSelectedRun(r)}
                className={`px-3.5 py-2 rounded-xl text-xs font-medium border transition-all ${
                  selectedRun?.id === r.id
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300 font-semibold'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {r.run_name} (MRR: {(r.mean_mrr * 100).toFixed(0)}% • Faith: {(r.mean_faithfulness * 100).toFixed(0)}%)
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Evaluation Dashboard */}
      {selectedRun ? (
        <EvaluationDashboard run={selectedRun} />
      ) : (
        <div className="py-20 text-center rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-3">
          <Award className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-white">No Evaluation Runs Recorded Yet</h3>
          <p className="text-xs text-slate-400">
            Click &ldquo;Execute Benchmark Run&rdquo; to benchmark the RAG pipeline.
          </p>
        </div>
      )}
    </div>
  );
}
