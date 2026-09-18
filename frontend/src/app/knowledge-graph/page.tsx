'use client';

import React, { useState, useEffect } from 'react';
import { Network, Sparkles, User, FileText, Cpu, ArrowRight, Layers } from 'lucide-react';
import { api } from '@/lib/api';
import { KnowledgeGraphData, KnowledgeNode, KnowledgeEdge } from '@/types';

export default function KnowledgeGraphPage() {
  const [graphData, setGraphData] = useState<KnowledgeGraphData>({ nodes: [], edges: [] });
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getKnowledgeGraph().then((data) => {
      setGraphData(data);
      if (data.nodes.length > 0) {
        setSelectedNode(data.nodes[0]);
      }
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'Author':
        return <User className="w-4 h-4 text-purple-400" />;
      case 'Concept':
        return <Cpu className="w-4 h-4 text-cyan-400" />;
      default:
        return <FileText className="w-4 h-4 text-indigo-400" />;
    }
  };

  const filteredNodes = selectedType === 'ALL'
    ? graphData.nodes
    : graphData.nodes.filter((n) => n.entity_type === selectedType);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold mb-2">
          <Network className="w-3.5 h-3.5" />
          <span>Entity-Relationship Knowledge Network</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Research Knowledge Graph
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
          Explores relationships extracted across the research corpus linking authors, publications, model architectures, and core concepts. Designed for future Neo4j graph expansions.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2">
        {['ALL', 'Paper', 'Author', 'Concept'].map((t) => (
          <button
            key={t}
            onClick={() => setSelectedType(t)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              selectedType === t
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'ALL' ? 'All Entities' : `${t}s`}
          </button>
        ))}
      </div>

      {/* Graph Visual Explorer Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Node Grid */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {filteredNodes.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            return (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className={`p-4 rounded-2xl border cursor-pointer transition-all space-y-2 ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500 shadow-lg shadow-indigo-500/10'
                    : 'bg-[#0f172a]/90 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                    {node.entity_type}
                  </span>
                  {getNodeIcon(node.entity_type)}
                </div>
                <h3 className="font-bold text-xs text-white line-clamp-2">{node.name}</h3>
                {node.description && (
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {node.description}
                  </p>
                )}
              </div>
            );
          })}
        </div>

        {/* Selected Entity Details & Relationships */}
        <div className="p-6 rounded-2xl bg-[#0b0f19] border border-slate-800 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800">
            Entity Inspector
          </h3>

          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase">
                  {selectedNode.entity_type}
                </span>
                <h4 className="text-sm font-bold text-white mt-0.5">{selectedNode.name}</h4>
                {selectedNode.description && (
                  <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                    {selectedNode.description}
                  </p>
                )}
              </div>

              {/* Connected Relationships */}
              <div className="space-y-2 pt-3 border-t border-slate-800">
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                  Connected Graph Edges
                </span>
                <div className="space-y-1.5">
                  {graphData.edges
                    .filter((e) => e.source_id === selectedNode.id || e.target_id === selectedNode.id)
                    .map((edge) => {
                      const target = graphData.nodes.find((n) => n.id === (edge.source_id === selectedNode.id ? edge.target_id : edge.source_id));
                      return (
                        <div key={edge.id} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-[11px] flex items-center justify-between">
                          <span className="font-mono text-cyan-400 font-semibold">{edge.relation_type}</span>
                          <span className="text-slate-300 truncate max-w-[150px]">{target?.name || 'Entity'}</span>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic py-6 text-center">Select an entity node to inspect connections.</p>
          )}
        </div>
      </div>
    </div>
  );
}
