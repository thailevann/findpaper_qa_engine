"use client"

import { useState } from "react"
import { Header } from "@/components/header"
import { SearchInterface } from "@/components/search-interface"
import { ResultsDisplay } from "@/components/results-display"
import { LoadingState } from "@/components/loading-state"
import { ErrorDisplay } from "@/components/error-display"
import { EmptyState } from "@/components/empty-state"
import { QueryHistory } from "@/components/query-history"
import { useLocalStorage } from "@/hooks/use-local-storage"
import { generateMockData } from "@/lib/mock-data"

export interface QAResult {
  original_query: string
  rewritten_query: string
  keyword_query: string
  gemini_filters: Record<string, any>
  raw_gemini_output: string
  qa_result: {
    query: string
    filtered_passages: Array<{
      paper_id: string
      title: string
      evidence: string
      cross_score: number
      final_score: number
    }>
    themes: Array<{
      theme_name: string
      quotes: Array<{
        paper_id: string
        title: string
        evidence: string
        cross_score: number
      }>
    }>
    final_report: string
    processing_info: {
      papers_found: number
      quotes_selected: number
      themes_generated: number
      processing_time: number
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
        const response = await fetch("http://localhost:8000/qa", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query,
            limit: options.limit,
            max_themes: options.maxThemes,
            model: options.model,
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data: QAResult = await response.json()
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
