"use client"

import { useState } from "react"

import { Header } from "@/components/qa/header"
import { SearchInterface } from "@/components/qa/search-interface"
import { ResultsDisplay } from "@/components/qa/results-display"
import { LoadingState } from "@/components/qa/loading-state"
import { ErrorDisplay } from "@/components/qa/error-display"
import { EmptyState } from "@/components/qa/empty-state"
import { QueryHistory } from "@/components/qa/query-history"

import { useLocalStorage } from "@/hooks/qa/use-local-storage"
import { generateMockData } from "@/lib/qa/mock-data"
import { FindPaperAPI } from "@/lib/qa/api"

export interface QAResult {
  original_query: string
  rewritten_query: string
  keyword_query: string
  gemini_filters: Record<string, any>
  raw_gemini_output: string
  scholarqa_result: {
    query: string
    summary: string
    sections: Array<{
      name: string
      description: string
      narrative: string
      quotes: Array<{
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
      }>
      quote_count: number
      papers_referenced: string[]
    }>
    comparison_tables: Array<{
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
    }>
    processing_trace: {
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
    metadata: {
      total_sections: number
      total_quotes: number
      total_papers: number
      comparison_tables_count: number
    }
  }
  finding_info: {
    total_passages_found: number
    passages_used_for_qa: number
  }
}

export default function HomePage() {
  const [result, setResult] = useState<QAResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [queryHistory, setQueryHistory] = useLocalStorage<string[]>("qa-history", [])

  const handleSearch = async (
    query: string,
    options: {
      limit: number
      maxThemes: number
      model?: string
      useMockData?: boolean
    },
  ) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      if (options.useMockData) {
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 2000))
        const mockData = generateMockData(query)
        setResult(mockData)
      } else {
        const data = await FindPaperAPI.searchScholarQA({
          query,
          limit: options.limit,
          model: options.model,
          retrieval_top_k: options.limit,
          rerank_top_k: Math.min(options.limit, 20)
        })
        setResult(data)
      }

      // Add to history
      const newHistory = [query, ...queryHistory.filter((q) => q !== query)].slice(0, 10)
      setQueryHistory(newHistory)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleHistorySelect = (query: string) => {
    // Trigger search with default options
    handleSearch(query, { limit: 50, maxThemes: 5 })
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <SearchInterface onSearch={handleSearch} />

        {queryHistory.length > 0 && !result && !loading && (
          <QueryHistory history={queryHistory} onSelect={handleHistorySelect} onClear={() => setQueryHistory([])} />
        )}

        {loading && <LoadingState />}

        {error && <ErrorDisplay error={error} onRetry={() => setError(null)} />}

        {result && !loading && <ResultsDisplay result={result} />}

        {!result && !loading && !error && queryHistory.length === 0 && <EmptyState />}
      </main>
    </div>
  )
}
