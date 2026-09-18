'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Layers,
  FileText,
  FolderOpen,
  MessageSquare,
  Sparkles,
  Columns,
  CheckCircle2,
  Activity,
  Network,
  Settings,
  ShieldCheck
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Layers },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Collections', href: '/collections', icon: FolderOpen },
  { name: 'Research Chat', href: '/chat', icon: MessageSquare },
  { name: 'Research Mode', href: '/research', icon: Sparkles, badge: 'Pro' },
  { name: 'Document Compare', href: '/compare', icon: Columns },
  { name: 'RAG Evaluation', href: '/evaluation', icon: CheckCircle2 },
  { name: 'AI Observability', href: '/observability', icon: Activity },
  { name: 'Knowledge Graph', href: '/knowledge-graph', icon: Network },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-slate-800 bg-[#0a0f1d] min-h-screen">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <div>
          <span className="font-bold text-base tracking-tight text-white block">ResearchVault</span>
          <span className="text-[10px] uppercase font-semibold tracking-wider text-indigo-400 block -mt-1">Intelligence AI</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Workspace
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-all ${
                isActive
                  ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* RAG Engine Status Badge */}
      <div className="p-4 border-t border-slate-800/80 m-3 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Hybrid Engine Active
          </span>
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        </div>
        <div className="space-y-1 text-[11px] text-slate-400">
          <div className="flex justify-between">
            <span>Retrieval:</span>
            <span className="font-mono text-slate-300">Qdrant + BM25</span>
          </div>
          <div className="flex justify-between">
            <span>Reranker:</span>
            <span className="font-mono text-indigo-300">Cross-Encoder</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
