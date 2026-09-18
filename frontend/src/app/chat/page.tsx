'use client';

import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Plus,
  Trash2,
  Bookmark,
  Activity,
  Layers,
  FileText,
  Copy,
  Check,
  RotateCw,
  SlidersHorizontal,
  ChevronRight,
  Target
} from 'lucide-react';
import { api } from '@/lib/api';
import { Message, Conversation, Collection, Document, Citation } from '@/types';
import { SourceInspectorDrawer } from '@/components/chat/SourceInspectorDrawer';

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('');
  const [inputQuery, setInputQuery] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadInitialData = async () => {
    try {
      const [convs, cols, docs] = await Promise.all([
        api.getConversations(),
        api.getCollections(),
        api.getDocuments()
      ]);
      setConversations(convs);
      setCollections(cols);
      setDocuments(docs);
      if (convs.length > 0 && !activeConversationId) {
        setActiveConversationId(convs[0].id);
        setMessages(convs[0].messages || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleSelectConversation = async (id: string) => {
    setActiveConversationId(id);
    try {
      const conv = await api.getConversation(id);
      setMessages(conv.messages || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversationId === id) {
        handleNewChat();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isSending) return;

    const userText = inputQuery.trim();
    setInputQuery('');
    setIsSending(true);

    // Optimistic user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConversationId || '',
      role: 'user',
      content: userText,
      latency_ms: 0,
      tokens_used: 0,
      citations: [],
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await api.sendChatMessage({
        message: userText,
        conversation_id: activeConversationId || undefined,
        collection_id: selectedCollectionId || undefined
      });

      setMessages((prev) => [...prev, response]);
      if (!activeConversationId) {
        setActiveConversationId(response.conversation_id);
        const updatedConvs = await api.getConversations();
        setConversations(updatedConvs);
      }
    } catch (err: any) {
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        conversation_id: activeConversationId || '',
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to generate response.'}`,
        latency_ms: 0,
        tokens_used: 0,
        citations: [],
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  };

  const handleCopy = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedMessageId(id);
    setTimeout(() => setCopiedMessageId(null), 1500);
  };

  return (
    <div className="flex h-[calc(100vh-6.5rem)] gap-6 max-w-7xl mx-auto">
      {/* Left Sidebar: Conversations & Scope */}
      <div className="w-72 flex-shrink-0 flex flex-col rounded-2xl bg-[#0b0f19] border border-slate-800 overflow-hidden shadow-xl hidden md:flex">
        {/* New Chat Button */}
        <div className="p-3 border-b border-slate-800">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Research Chat</span>
          </button>
        </div>

        {/* Collection Filter */}
        <div className="p-3 border-b border-slate-800 space-y-1.5">
          <label className="block text-[10px] uppercase font-bold tracking-wider text-slate-400">
            Query Scope / Collection
          </label>
          <select
            value={selectedCollectionId}
            onChange={(e) => setSelectedCollectionId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">Entire Corpus (All Papers)</option>
            {collections.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.document_count})
              </option>
            ))}
          </select>
        </div>

        {/* Conversations History */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
            Past Conversations
          </div>
          {conversations.map((c) => (
            <div
              key={c.id}
              onClick={() => handleSelectConversation(c.id)}
              className={`group flex items-center justify-between p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                activeConversationId === c.id
                  ? 'bg-slate-800 text-indigo-300 font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <span className="truncate max-w-[170px]">{c.title}</span>
              <button
                onClick={(e) => handleDeleteConversation(c.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition-opacity"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Center Chat Area */}
      <div className="flex-1 flex flex-col rounded-2xl bg-[#0e1424] border border-slate-800 overflow-hidden shadow-2xl relative">
        {/* Top Chat Info Bar */}
        <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-900/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-semibold text-slate-200">
              {selectedCollectionId
                ? `Scoped to: ${collections.find((c) => c.id === selectedCollectionId)?.name}`
                : 'Searching entire research corpus (Cross-encoder reranked)'}
            </span>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Grounded Grounding Active
          </span>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-md mx-auto py-16">
              <div className="w-14 h-14 rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shadow-lg shadow-indigo-600/10">
                <Sparkles className="w-7 h-7" />
              </div>
              <h2 className="text-base font-bold text-white">Ask ResearchVault AI</h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ask questions across research papers. Answers are strictly grounded in retrieved evidence with verifiable clickable citations [1].
              </p>
              <div className="flex flex-wrap gap-2 justify-center pt-2">
                {[
                  'How does RAG combine parametric and non-parametric memory?',
                  'Why divide by sqrt(d_k) in scaled dot-product attention?',
                  'How does Self-RAG use reflection tokens to reduce hallucination?'
                ].map((sample, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInputQuery(sample)}
                    className="text-[11px] px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-indigo-300 transition-colors text-left"
                  >
                    &ldquo;{sample}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isAssistant = msg.role === 'assistant';
              const citationMap = new Map<number, Citation>();
              if (msg.citations) {
                msg.citations.forEach((c) => citationMap.set(c.citation_number, c));
              }

              return (
                <div
                  key={msg.id}
                  className={`flex gap-4 ${isAssistant ? 'items-start' : 'items-start flex-row-reverse'}`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-md ${
                      isAssistant
                        ? 'bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white'
                        : 'bg-slate-700 text-slate-200'
                    }`}
                  >
                    {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                  </div>

                  {/* Content Bubble */}
                  <div
                    className={`max-w-[85%] rounded-2xl p-5 text-xs leading-relaxed space-y-3 ${
                      isAssistant
                        ? 'bg-slate-900/90 border border-slate-800 text-slate-200 shadow-sm'
                        : 'bg-indigo-600 text-white shadow-md'
                    }`}
                  >
                    {/* Assistant Message Query Transformation Badge (if rewritten) */}
                    {isAssistant && msg.rewritten_query && msg.rewritten_query !== messages[messages.indexOf(msg) - 1]?.content && (
                      <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 font-mono">
                        <span className="text-cyan-400 font-bold">Query Rewritten:</span> &ldquo;{msg.rewritten_query}&rdquo;
                      </div>
                    )}

                    {/* Markdown Body */}
                    <div className="prose prose-invert prose-indigo max-w-none text-xs leading-relaxed">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => {
                            const content = React.Children.toArray(children);
                            return (
                              <p className="mb-2 leading-relaxed">
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
                                            onClick={() => cite && setSelectedCitation(cite)}
                                            className="citation-badge"
                                            title={cite ? `${cite.document_title} • Page ${cite.page_number}` : `Source [${num}]`}
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
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {/* Citations Footer Drawer Links */}
                    {isAssistant && msg.citations && msg.citations.length > 0 && (
                      <div className="pt-3 border-t border-slate-800/80 space-y-2">
                        <span className="text-[10px] uppercase tracking-wider font-bold text-slate-400 block">
                          Supporting Citations & Evidence:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.citations.map((c) => (
                            <button
                              key={c.citation_number}
                              onClick={() => setSelectedCitation(c)}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 hover:border-indigo-500/40 text-[11px] text-slate-300 transition-colors"
                            >
                              <span className="font-bold text-indigo-400">[{c.citation_number}]</span>
                              <span className="truncate max-w-[180px]">{c.document_title}</span>
                              <span className="text-slate-500 font-mono text-[10px]">p.{c.page_number}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Footer Controls & Latency */}
                    {isAssistant && (
                      <div className="pt-2 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                        <div className="flex items-center gap-3">
                          <span>Latency: {msg.latency_ms ? msg.latency_ms.toFixed(0) : 0}ms</span>
                          <span>Tokens: {msg.tokens_used}</span>
                        </div>

                        <button
                          onClick={() => handleCopy(msg.id, msg.content)}
                          className="flex items-center gap-1 text-slate-400 hover:text-slate-200 transition-colors"
                        >
                          {copiedMessageId === msg.id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/60">
          <form onSubmit={handleSendMessage} className="flex gap-3">
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask a technical or research question across your indexed papers..."
              disabled={isSending}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
            <button
              type="submit"
              disabled={isSending || !inputQuery.trim()}
              className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 flex items-center gap-2 transition-all cursor-pointer"
            >
              {isSending ? (
                <RotateCw className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Ask RAG</span>
            </button>
          </form>
        </div>
      </div>

      {/* Right Drawer: Source Inspector */}
      <SourceInspectorDrawer
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
