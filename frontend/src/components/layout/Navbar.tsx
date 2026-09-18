'use client';

import React from 'react';
import Link from 'next/link';
import { Plus, Search, Sparkles, User, Terminal } from 'lucide-react';

interface NavbarProps {
  onOpenUpload?: () => void;
}

export function Navbar({ onOpenUpload }: NavbarProps) {
  return (
    <header className="h-16 border-b border-slate-800 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-30 px-6 flex items-center justify-between">
      {/* Search / Context Bar */}
      <div className="flex items-center gap-3 max-w-md w-full">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search papers, concepts, or past queries..."
            className="w-full bg-slate-900/80 border border-slate-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {onOpenUpload && (
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>
        )}

        <Link
          href="/research"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Research Mode</span>
        </Link>

        {/* User Badge */}
        <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center text-xs font-bold text-white shadow-inner">
            AV
          </div>
          <div className="text-left hidden sm:block">
            <span className="block text-xs font-medium text-slate-200 leading-none">Dr. Alex Vance</span>
            <span className="block text-[10px] text-slate-400 leading-none mt-1">Lead AI Researcher</span>
          </div>
        </div>
      </div>
    </header>
  );
}
