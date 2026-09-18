'use client';

import React, { useState, useRef } from 'react';
import { X, UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2, Settings2 } from 'lucide-react';
import { api } from '@/lib/api';
import { Collection } from '@/types';

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  collections: Collection[];
  onUploadSuccess: () => void;
}

export function DocumentUploadModal({
  isOpen,
  onClose,
  collections,
  onUploadSuccess,
}: DocumentUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [collectionId, setCollectionId] = useState<string>('');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [chunkSize, setChunkSize] = useState(500);
  const [chunkOverlap, setChunkOverlap] = useState(100);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      setFile(selected);
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '));
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    if (collectionId) formData.append('collection_id', collectionId);
    if (title) formData.append('title', title);
    if (author) formData.append('author', author);

    try {
      await api.uploadDocument(formData);
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        setUploading(false);
        setFile(null);
        setTitle('');
        setAuthor('');
        onUploadSuccess();
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Upload failed.');
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl bg-[#0e1424] border border-slate-800 shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center">
              <UploadCloud className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Ingest Research Document</h3>
              <p className="text-[11px] text-slate-400">PDF, DOCX, TXT, or Markdown papers</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isSuccess ? (
            <div className="py-10 text-center space-y-3">
              <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto animate-bounce" />
              <h4 className="text-sm font-semibold text-white">Document Ingested & Processing!</h4>
              <p className="text-xs text-slate-400">Extracting sections, structure-aware chunking & embedding...</p>
            </div>
          ) : (
            <>
              {/* Drag & Drop Area */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                  file
                    ? 'border-indigo-500/60 bg-indigo-950/20'
                    : 'border-slate-800 hover:border-indigo-500/40 bg-slate-900/30'
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.doc,.txt,.md"
                  className="hidden"
                />
                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="w-8 h-8 text-indigo-400" />
                    <div className="text-left">
                      <p className="text-xs font-semibold text-white">{file.name}</p>
                      <p className="text-[11px] text-slate-400 font-mono">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <UploadCloud className="w-8 h-8 text-indigo-400 mx-auto" />
                    <p className="text-xs text-slate-300 font-medium">
                      Drag & drop your research paper, or <span className="text-indigo-400 underline">browse</span>
                    </p>
                    <p className="text-[11px] text-slate-500">Supports PDF, DOCX, TXT, Markdown (up to 50MB)</p>
                  </div>
                )}
              </div>

              {/* Title & Collection Inputs */}
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Document Title
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Attention Is All You Need"
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Lead Author(s)
                    </label>
                    <input
                      type="text"
                      value={author}
                      onChange={(e) => setAuthor(e.target.value)}
                      placeholder="e.g. Vaswani et al."
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Assign to Collection
                    </label>
                    <select
                      value={collectionId}
                      onChange={(e) => setCollectionId(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                    >
                      <option value="">No Collection (General)</option>
                      {collections.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Advanced Chunking Toggle */}
              <div>
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-400 font-medium"
                >
                  <Settings2 className="w-3.5 h-3.5" />
                  <span>{showAdvanced ? 'Hide' : 'Show'} Advanced Ingestion Config</span>
                </button>

                {showAdvanced && (
                  <div className="grid grid-cols-2 gap-3 p-3 mt-2 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">
                        Chunk Target Size (Tokens)
                      </label>
                      <input
                        type="number"
                        value={chunkSize}
                        onChange={(e) => setChunkSize(Number(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-200 font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">
                        Sliding Window Overlap
                      </label>
                      <input
                        type="number"
                        value={chunkOverlap}
                        onChange={(e) => setChunkOverlap(Number(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-200 font-mono"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <div className="pt-2 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !file}
                  className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 flex items-center gap-2 transition-all cursor-pointer"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Ingesting & Indexing...</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-4 h-4" />
                      <span>Start Pipeline</span>
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
