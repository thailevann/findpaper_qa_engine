// API service for FindPaper QA Engine
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:9000'

// Legacy QA Types (backward compatibility)
export interface QARequest {
  query: string
  limit?: number
  max_themes?: number
  model?: string
}

export interface QAResponse {
  original_query: string
  rewritten_query: string
  keyword_query: string
  gemini_filters: Record<string, any>
  raw_gemini_output: string
  qa_result: {
    query: string
    filtered_passages: string[]
    themes: Array<{
      name: string
      quotes: string[]
    }>
    final_report: string
    processing_info: {
      total_passages: number
      selected_quotes: number
      themes_generated: number
      papers_used: number
    }
  }
  finding_info: {
    total_passages_found: number
    passages_used_for_qa: number
  }
}

// New ScholarQA Types (enhanced structured output)
export interface ScholarQARequest {
  query: string
  limit?: number
  model?: string
  retrieval_top_k?: number
  rerank_top_k?: number
}

export interface QuoteWithMetadata {
  quote_text: string
  paper_id: string
  title: string
  score: number
  similarity_score: number
  passage_index: number
  metadata: {
    cross_score: number
    final_score: number
  }
}

export interface SectionInfo {
  name: string
  description: string
  narrative: string
  quotes: QuoteWithMetadata[]
  quote_count: number
  papers_referenced: string[]
}

export interface ComparisonTable {
  section: string
  headers: string[]
  rows: Array<{
    paper_title: string
    attributes: string[]
  }>
  paper_count: number
  metadata: {
    papers: string[]
    generated_at: string
  }
}

export interface ProcessingTrace {
  pipeline_start: boolean
  query: string
  input_passages: number
  retrieved_passages?: number
  embeddings_generated?: number
  reranked_passages?: number
  extracted_quotes?: number
  outline_generated?: boolean
  sections_created?: number
  comparison_tables?: number
  pipeline_completed?: boolean
  final_sections?: number
  final_quotes?: number
  final_papers?: number
  error?: string
  pipeline_failed?: boolean
}

export interface ReportMetadata {
  total_sections: number
  total_quotes: number
  total_papers: number
  comparison_tables_count: number
}

export interface StructuredReport {
  query: string
  summary: string
  sections: SectionInfo[]
  comparison_tables: ComparisonTable[]
  processing_trace: ProcessingTrace
  metadata: ReportMetadata
}

export interface ScholarQAResponse {
  original_query: string
  rewritten_query: string
  keyword_query: string
  gemini_filters: Record<string, any>
  raw_gemini_output: string
  scholarqa_result: StructuredReport
  finding_info: {
    total_passages_found: number
    passages_used_for_qa: number
  }
}

export class FindPaperAPI {
  // Legacy QA endpoint (backward compatibility)
  static async searchQA(request: QARequest): Promise<QAResponse> {
    const response = await fetch(`${API_BASE_URL}/qa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error: ${response.status} - ${errorText}`)
    }

    return response.json()
  }

  // New ScholarQA endpoint (enhanced structured output)
  static async searchScholarQA(request: ScholarQARequest): Promise<ScholarQAResponse> {
    const response = await fetch(`${API_BASE_URL}/scholarqa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error: ${response.status} - ${errorText}`)
    }

    return response.json()
  }

  static async healthCheck(): Promise<{ status: string; message: string; version?: string; features?: string[] }> {
    const response = await fetch(`${API_BASE_URL}/health`)
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`)
    }

    return response.json()
  }

  static async searchPassages(query: string, limit: number = 5) {
    const response = await fetch(`${API_BASE_URL}/search_passsages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, limit }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error: ${response.status} - ${errorText}`)
    }

    return response.json()
  }

  static async getTopPapers(query: string, limit: number = 5) {
    const response = await fetch(`${API_BASE_URL}/top_papers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, limit }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error: ${response.status} - ${errorText}`)
    }

    return response.json()
  }
}

// Available OpenAI models
export const AVAILABLE_MODELS = [
  { value: 'gpt-4o', label: 'GPT-4o (Best Quality)' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Recommended)' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (Fast & Cost-Effective)' },
] as const

export type ModelType = typeof AVAILABLE_MODELS[number]['value']
