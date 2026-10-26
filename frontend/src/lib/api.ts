import {
  Document,
  Collection,
  Conversation,
  Message,
  ResearchResponse,
  CompareResponse,
  EvaluationDataset,
  EvaluationRun,
  ObservabilityStats,
  QueryTrace,
  KnowledgeGraphData,
  HallucinationReport,
  HumanBenchmarkReport,
  HybridSimulateResponse,
  HybridBenchmarkResponse,
  OptimalRecommendation
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private getHeaders(isFormData = false): HeadersInit {
    const headers: Record<string, string> = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('researchvault_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const isFormData = options.body instanceof FormData;
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...this.getHeaders(isFormData),
        ...(options.headers || {})
      }
    });

    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to text status
      }
      throw new Error(errorMessage);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string): Promise<{ access_token: string }> {
    const data = await this.request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    if (typeof window !== 'undefined' && data.access_token) {
      localStorage.setItem('researchvault_token', data.access_token);
    }
    return data;
  }

  // Documents
  async getDocuments(collectionId?: string): Promise<Document[]> {
    const query = collectionId ? `?collection_id=${encodeURIComponent(collectionId)}` : '';
    return this.request<Document[]>(`/documents${query}`);
  }

  async getDocument(id: string): Promise<Document> {
    return this.request<Document>(`/documents/${id}`);
  }

  async uploadDocument(formData: FormData): Promise<Document> {
    return this.request<Document>('/documents/upload', {
      method: 'POST',
      body: formData
    });
  }

  async reprocessDocument(id: string): Promise<Document> {
    return this.request<Document>(`/documents/${id}/reprocess`, {
      method: 'POST'
    });
  }

  async deleteDocument(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/documents/${id}`, {
      method: 'DELETE'
    });
  }

  // Collections
  async getCollections(): Promise<Collection[]> {
    return this.request<Collection[]>('/collections');
  }

  async createCollection(name: string, description?: string, color?: string): Promise<Collection> {
    return this.request<Collection>('/collections', {
      method: 'POST',
      body: JSON.stringify({ name, description, color })
    });
  }

  async deleteCollection(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/collections/${id}`, {
      method: 'DELETE'
    });
  }

  // Chat
  async getConversations(): Promise<Conversation[]> {
    return this.request<Conversation[]>('/chat/conversations');
  }

  async getConversation(id: string): Promise<Conversation> {
    return this.request<Conversation>(`/chat/conversations/${id}`);
  }

  async deleteConversation(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/chat/conversations/${id}`, {
      method: 'DELETE'
    });
  }

  async sendChatMessage(payload: {
    message: string;
    conversation_id?: string;
    collection_id?: string;
    document_ids?: string[];
    mode?: string;
  }): Promise<Message> {
    return this.request<Message>('/chat', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // Research Mode
  async runResearch(payload: {
    query: string;
    collection_id?: string;
    document_ids?: string[];
    depth?: string;
  }): Promise<ResearchResponse> {
    return this.request<ResearchResponse>('/research', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // Compare Documents
  async compareDocuments(payload: {
    document_ids: string[];
    question?: string;
  }): Promise<CompareResponse> {
    return this.request<CompareResponse>('/compare', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // Evaluation
  async getEvaluationDatasets(): Promise<EvaluationDataset[]> {
    return this.request<EvaluationDataset[]>('/evaluation/datasets');
  }

  async getEvaluationRuns(): Promise<EvaluationRun[]> {
    return this.request<EvaluationRun[]>('/evaluation/runs');
  }

  async runEvaluation(payload: {
    dataset_id: string;
    run_name?: string;
    llm_provider?: string;
    top_k?: number;
  }): Promise<EvaluationRun> {
    return this.request<EvaluationRun>('/evaluation/run', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // Hallucination Detection & Scoring
  async detectHallucinations(payload: {
    answer_text: string;
    context_passages?: any[];
    query?: string;
    llm_provider?: string;
  }): Promise<HallucinationReport> {
    return this.request<HallucinationReport>('/evaluation/hallucination', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async runHumanBenchmark(): Promise<HumanBenchmarkReport> {
    return this.request<HumanBenchmarkReport>('/evaluation/hallucination/human-benchmark', {
      method: 'POST'
    });
  }

  async getHallucinationHistory(limit = 15): Promise<any[]> {
    return this.request<any[]>(`/evaluation/hallucination/history?limit=${limit}`);
  }

  // Hybrid Retrieval Ratio Simulator & Optimizer
  async simulateHybridRetrieval(payload: {
    query: string;
    dense_weight: number;
    sparse_weight: number;
    k?: number;
  }): Promise<HybridSimulateResponse> {
    return this.request<HybridSimulateResponse>('/evaluation/hybrid-simulate', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async runHybridBenchmark(payload: {
    dataset_id: string;
    k?: number;
    ratios?: number[];
  }): Promise<HybridBenchmarkResponse> {
    return this.request<HybridBenchmarkResponse>('/evaluation/hybrid-benchmark', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async optimizeRatio(payload: {
    dataset_id: string;
    k?: number;
  }): Promise<OptimalRecommendation> {
    return this.request<OptimalRecommendation>('/evaluation/optimize-ratio', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async getBenchmarkResults(limit = 10): Promise<any[]> {
    return this.request<any[]>(`/evaluation/benchmark-results?limit=${limit}`);
  }


  // Observability
  async getObservabilityStats(): Promise<ObservabilityStats> {
    return this.request<ObservabilityStats>('/observability/stats');
  }

  async getQueryTraces(limit: number = 50): Promise<QueryTrace[]> {
    return this.request<QueryTrace[]>(`/observability/traces?limit=${limit}`);
  }

  // Knowledge Graph
  async getKnowledgeGraph(): Promise<KnowledgeGraphData> {
    return this.request<KnowledgeGraphData>('/knowledge-graph');
  }
}

export const api = new ApiClient();
