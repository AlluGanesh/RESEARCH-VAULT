export type DocumentStatus = 
  | 'UPLOADED' 
  | 'EXTRACTING' 
  | 'CHUNKING' 
  | 'EMBEDDING' 
  | 'INDEXING' 
  | 'COMPLETED' 
  | 'FAILED';

export interface Chunk {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number: number;
  section: string;
  subsection?: string;
  content: string;
  context_header?: string;
  token_count: number;
  similarity_score?: number;
  rerank_score?: number;
}

export interface Document {
  id: string;
  user_id: string;
  collection_id?: string;
  title: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  author?: string;
  abstract?: string;
  publication_date?: string;
  doi_or_url?: string;
  topics: string[];
  page_count: number;
  chunk_count: number;
  token_count: number;
  status: DocumentStatus;
  error_message?: string;
  created_at: string;
  updated_at: string;
  chunks?: Chunk[];
}

export interface Collection {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  color: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  id?: string;
  citation_number: number;
  document_id: string;
  chunk_id?: string;
  document_title: string;
  page_number: number;
  section: string;
  passage_text: string;
  similarity_score: number;
  rerank_score: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  rewritten_query?: string;
  expansion_queries?: string[];
  latency_ms: number;
  tokens_used: number;
  structured_data?: Record<string, any>;
  citations: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  collection_id?: string;
  title: string;
  mode: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ResearchPlanStep {
  step_number: number;
  sub_question: string;
  rationale: string;
  retrieved_chunks_count: number;
  status: string;
}

export interface ContradictionItem {
  topic: string;
  perspective_a: string;
  perspective_a_source: string;
  perspective_b: string;
  perspective_b_source: string;
  analysis: string;
}

export interface ResearchResponse {
  query: string;
  plan_steps: ResearchPlanStep[];
  executive_summary: string;
  key_findings: string[];
  cross_document_synthesis: string;
  contradictions: ContradictionItem[];
  research_gaps: string[];
  markdown_report: string;
  citations: Citation[];
  latency_ms: number;
  total_tokens: number;
}

export interface ComparisonRow {
  document_id: string;
  document_title: string;
  methodology: string;
  architecture_or_approach: string;
  datasets_used: string;
  key_results: string;
  limitations: string;
  citation_numbers: number[];
}

export interface CompareResponse {
  question: string;
  documents_compared_count: number;
  summary_analysis: string;
  matrix_rows: ComparisonRow[];
  markdown_table: string;
  citations: Citation[];
  latency_ms: number;
}

export interface EvaluationTestCase {
  id: string;
  dataset_id: string;
  question: string;
  ground_truth_answer: string;
  relevant_doc_titles: string[];
  relevant_passages: string[];
  created_at: string;
}

export interface EvaluationDataset {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  test_case_count: number;
  created_at: string;
  test_cases: EvaluationTestCase[];
}

export interface EvaluationResult {
  id: string;
  test_case_id?: string;
  question: string;
  ground_truth: string;
  generated_answer: string;
  precision_at_k: number;
  recall_at_k: number;
  reciprocal_rank: number;
  ndcg_score: number;
  faithfulness_score: number;
  answer_relevance_score: number;
  context_relevance_score: number;
  citation_accuracy: number;
  latency_ms: number;
}

export interface EvaluationRun {
  id: string;
  dataset_id: string;
  run_name: string;
  llm_provider: string;
  embedding_provider: string;
  reranker_used: string;
  mean_precision_at_k: number;
  mean_recall_at_k: number;
  mean_mrr: number;
  mean_ndcg: number;
  mean_faithfulness: number;
  mean_answer_relevance: number;
  mean_context_relevance: number;
  mean_citation_accuracy: number;
  total_test_cases: number;
  status: string;
  created_at: string;
  results: EvaluationResult[];
}

export interface QueryTrace {
  id: string;
  user_id: string;
  conversation_id?: string;
  raw_query: string;
  rewritten_query?: string;
  expansion_queries: string[];
  extracted_keywords: string[];
  applied_filters: Record<string, any>;
  vector_candidates_count: number;
  lexical_candidates_count: number;
  rrf_candidates: any[];
  reranked_candidates: any[];
  compressed_context?: string;
  llm_prompt?: string;
  llm_response?: string;
  citations_count: number;
  query_transform_ms: number;
  retrieval_ms: number;
  rerank_ms: number;
  compression_ms: number;
  generation_ms: number;
  total_latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  status: string;
  error_message?: string;
  created_at: string;
}

export interface ObservabilityStats {
  total_documents: number;
  total_chunks: number;
  total_embeddings: number;
  total_queries: number;
  avg_retrieval_latency_ms: number;
  avg_generation_latency_ms: number;
  avg_total_latency_ms: number;
  total_tokens_consumed: number;
  failed_queries_count: number;
  latest_traces: QueryTrace[];
}

export interface KnowledgeNode {
  id: string;
  name: string;
  entity_type: string;
  description?: string;
  properties: Record<string, any>;
}

export interface KnowledgeEdge {
  id: string;
  source_id: string;
  target_id: string;
  relation_type: string;
  weight: number;
  evidence_text?: string;
  document_id?: string;
}

export interface KnowledgeGraphData {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

export interface ClaimVerificationItem {
  claim_id: string;
  claim_text: string;
  original_sentence: string;
  cited_indices: number[];
  verdict: 'SUPPORTED' | 'CONTRADICTED' | 'UNVERIFIABLE';
  confidence: number;
  evidence_snippet?: string;
  matched_doc_title?: string;
  matched_chunk_id?: string;
  citation_valid: boolean;
  explanation?: string;
}

export interface HallucinationReport {
  total_claims: number;
  supported_count: number;
  contradicted_count: number;
  unverifiable_count: number;
  hallucination_rate: number;
  claim_support_rate: number;
  contradiction_rate: number;
  unverifiable_rate: number;
  citation_valid_count: number;
  total_citations_checked: number;
  citation_accuracy: number;
  verified_claims: ClaimVerificationItem[];
  execution_time_ms: number;
}

export interface HumanBenchmarkCaseItem {
  id: string;
  claim: string;
  gold_verdict: string;
  predicted_verdict: string;
  confidence: number;
  is_match: boolean;
}

export interface HumanBenchmarkReport {
  total_benchmark_cases: number;
  correct_matches: number;
  benchmark_accuracy: number;
  test_cases: HumanBenchmarkCaseItem[];
}

export interface HybridCandidateItem {
  chunk_id?: string;
  document_title?: string;
  retrieval_source: 'dense_only' | 'sparse_only' | 'hybrid_overlap';
  rrf_score: number;
  vector_score?: number;
  lexical_score?: number;
  passage_preview: string;
}

export interface HybridSimulateResponse {
  query: string;
  dense_weight: number;
  sparse_weight: number;
  k: number;
  total_retrieved: number;
  overlap_count: number;
  overlap_ratio: number;
  dense_only_count: number;
  sparse_only_count: number;
  latency_ms: number;
  candidates: HybridCandidateItem[];
}

export interface BenchmarkCurvePoint {
  dense_weight: number;
  sparse_weight: number;
  dense_pct: number;
  sparse_pct: number;
  mean_ndcg: number;
  mean_recall: number;
  mean_precision: number;
  mean_mrr: number;
  mean_overlap: number;
  mean_dense_only: number;
  mean_sparse_only: number;
  avg_latency_ms: number;
  estimated_hallucination_rate: number;
  composite_score: number;
}

export interface OptimalRecommendation {
  dense_weight: number;
  sparse_weight: number;
  dense_pct: number;
  sparse_pct: number;
  peak_ndcg: number;
  peak_recall: number;
  composite_score: number;
  estimated_hallucination_rate: number;
  ndcg_lift_over_dense_pct: number;
  ndcg_lift_over_bm25_pct: number;
  rationale: string;
}

export interface HybridBenchmarkResponse {
  dataset_id: string;
  dataset_name: string;
  k: number;
  total_test_cases: number;
  benchmark_curves: BenchmarkCurvePoint[];
  optimal_recommendation: OptimalRecommendation;
  execution_time_ms: number;
}

