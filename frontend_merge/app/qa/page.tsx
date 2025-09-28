"use client"

import { useState } from "react"
import { Search, FileText, BarChart3, Settings, User, Download, Copy, ChevronRight, Sparkles, Zap } from "lucide-react"
import { Button } from "@/components/qa/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/qa/ui/card"
import { Input } from "@/components/qa/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/qa/ui/tabs"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/qa/ui/collapsible"
import { Badge } from "@/components/qa/ui/badge"
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

const exampleQueries = [
  "What are the latest advances in machine learning?",
  "How does climate change affect biodiversity?",
  "What are the applications of quantum computing?",
  "Recent developments in renewable energy technologies",
]

export default function ScholarQAPage() {
  const [result, setResult] = useState<QAResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState("Transformer for low-resource languages")
  const [queryHistory, setQueryHistory] = useLocalStorage<string[]>("qa-history", [])

  const handleSearch = async (
    searchQuery: string,
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
        const mockData = generateMockData(searchQuery)
        setResult(mockData)
      } else {
        const data = await FindPaperAPI.searchScholarQA({
          query: searchQuery,
          limit: options.limit,
          model: options.model,
          retrieval_top_k: options.limit,
          rerank_top_k: Math.min(options.limit, 20)
        })
        setResult(data)
      }

      // Add to history
      const newHistory = [searchQuery, ...queryHistory.filter((q) => q !== searchQuery)].slice(0, 10)
      setQueryHistory(newHistory)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery)
    handleSearch(exampleQuery, { limit: 50, maxThemes: 5 })
  }

  const handleMockData = () => {
    const mockQuery = "What are the latest advances in machine learning?"
    setQuery(mockQuery)
    handleSearch(mockQuery, { limit: 50, maxThemes: 5, useMockData: true })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      handleSearch(query.trim(), { limit: 50, maxThemes: 5 })
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">ScholarQA Intelligence</h1>
                <p className="text-sm text-muted-foreground">
                  Get comprehensive research insights with structured analysis, evidence-based quotes, and comparative
                  tables across multiple papers.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm">
                <Settings className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <User className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="max-w-6xl mx-auto space-y-8">
          <Card className="border-primary/20 bg-gradient-to-br from-card to-primary/5">
            <CardContent className="p-6 space-y-6">
              <form onSubmit={handleSubmit}>
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Recent research about transformer in NLP"
                    className="pl-12 h-14 text-lg bg-background/80 backdrop-blur-sm"
                  />
                </div>
              </form>

              <Tabs defaultValue="analyze" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger
                    value="analyze"
                    className="gap-2 bg-primary text-primary-foreground data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                    onClick={() => handleSearch(query, { limit: 50, maxThemes: 5 })}
                  >
                    <BarChart3 className="w-4 h-4" />
                    Analyze Research
                  </TabsTrigger>
                  <TabsTrigger value="mock" className="gap-2" onClick={handleMockData}>
                    <FileText className="w-4 h-4" />
                    Try Mock Data
                  </TabsTrigger>
                  <TabsTrigger value="advanced" className="gap-2">
                    <Settings className="w-4 h-4" />
                    Advanced Options
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="analyze" className="mt-6">
                  <div className="space-y-4">
                    <h3 className="font-medium text-foreground">Try these example queries:</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {exampleQueries.map((example, index) => (
                        <Card 
                          key={index}
                          className="p-4 hover:shadow-md transition-shadow cursor-pointer border-primary/20"
                          onClick={() => handleExampleClick(example)}
                        >
                          <h4 className="font-medium mb-2">{example}</h4>
                        </Card>
                      ))}
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Loading State */}
          {loading && (
            <Card>
              <CardContent className="p-8 text-center">
                <div className="flex items-center justify-center gap-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                  <span className="text-muted-foreground">Analyzing research papers...</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error State */}
          {error && (
            <Card className="border-destructive/20 bg-destructive/5">
              <CardContent className="p-6">
                <div className="text-destructive font-medium mb-2">Error</div>
                <div className="text-muted-foreground">{error}</div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="mt-4"
                  onClick={() => setError(null)}
                >
                  Try Again
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Results */}
          {result && !loading && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="w-5 h-5 text-primary" />
                    Query Processing
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Original Query:</h4>
                    <p className="text-muted-foreground">{result.original_query}</p>
                  </div>
                  {result.rewritten_query && (
                    <div>
                      <h4 className="font-medium mb-2">Rewritten Query:</h4>
                      <p className="text-muted-foreground">{result.rewritten_query}</p>
                    </div>
                  )}
                  {result.keyword_query && (
                    <div>
                      <h4 className="font-medium mb-2">Keyword Query:</h4>
                      <p className="text-muted-foreground">{result.keyword_query}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="text-center p-6 bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
                  <div className="text-3xl font-bold text-primary mb-2">{result.finding_info.total_passages_found}</div>
                  <div className="text-sm text-muted-foreground">Papers Found</div>
                </Card>
                <Card className="text-center p-6 bg-gradient-to-br from-secondary/10 to-secondary/5 border-secondary/20">
                  <div className="text-3xl font-bold text-secondary mb-2">{result.scholarqa_result.metadata.total_quotes}</div>
                  <div className="text-sm text-muted-foreground">Quotes Extracted</div>
                </Card>
                <Card className="text-center p-6 bg-gradient-to-br from-accent/10 to-accent/5 border-accent/20">
                  <div className="text-3xl font-bold text-accent mb-2">{result.scholarqa_result.metadata.total_sections}</div>
                  <div className="text-sm text-muted-foreground">Sections Created</div>
                </Card>
                <Card className="text-center p-6 bg-gradient-to-br from-chart-1/10 to-chart-1/5 border-chart-1/20">
                  <div className="text-3xl font-bold text-chart-1 mb-2">{result.scholarqa_result.metadata.total_papers}</div>
                  <div className="text-sm text-muted-foreground">Papers Referenced</div>
                </Card>
              </div>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-primary" />
                      Research Summary
                    </CardTitle>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="prose prose-sm max-w-none text-muted-foreground leading-relaxed">
                    {result.scholarqa_result.summary.split("\n").map((paragraph, index) => (
                      <p key={index} className="mb-4 last:mb-0">
                        {paragraph}
                      </p>
                    ))}
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Research Sections ({result.scholarqa_result.sections.length})</h3>

                    {result.scholarqa_result.sections.map((section, index) => (
                      <Collapsible key={index} defaultOpen={index === 0}>
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 bg-muted/50 rounded-lg hover:bg-muted/70 transition-colors">
                          <div className="flex items-center gap-3">
                            <ChevronRight className="w-4 h-4 transition-transform data-[state=open]:rotate-90" />
                            <div className="text-left">
                              <h4 className="font-medium">{section.name}</h4>
                              <p className="text-sm text-muted-foreground">{section.quote_count} quotes</p>
                            </div>
                          </div>
                        </CollapsibleTrigger>
                        <CollapsibleContent className="px-4 pb-4">
                          <div className="space-y-4 mt-4">
                            <p className="text-sm text-muted-foreground">
                              {section.description}
                            </p>
                            <div className="space-y-4">
                              <div className="prose prose-sm max-w-none text-muted-foreground leading-relaxed">
                                {section.narrative.split("\n").map((paragraph, pIndex) => (
                                  <p key={pIndex} className="mb-2 last:mb-0">
                                    {paragraph}
                                  </p>
                                ))}
                              </div>
                              {section.quotes.map((quote, quoteIndex) => (
                                <div key={quoteIndex} className="bg-muted/30 p-4 rounded-lg border-l-4 border-primary">
                                  <p className="text-sm italic">
                                    "{quote.quote_text}"
                                  </p>
                                  <p className="text-xs text-muted-foreground mt-2">
                                    From: {quote.title} (Score: {quote.score.toFixed(2)})
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        </CollapsibleContent>
                      </Collapsible>
                    ))}
                  </div>

                  <div className="pt-6 border-t">
                    <h3 className="text-lg font-semibold mb-4">Processing Details</h3>
                    <div className="text-sm text-muted-foreground">
                      <p>
                        Query processed successfully with comprehensive analysis across {result.finding_info.total_passages_found} research papers and
                        structured output generation with {result.scholarqa_result.metadata.total_sections} sections and {result.scholarqa_result.metadata.total_quotes} quotes.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* Empty State */}
          {!result && !loading && !error && (
            <Card>
              <CardContent className="p-12 text-center">
                <div className="mx-auto w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mb-6">
                  <FileText className="h-12 w-12 text-primary" />
                </div>
                <h2 className="text-2xl font-bold mb-4">Welcome to ScholarQA Intelligence</h2>
                <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
                  Ask research questions and get comprehensive answers synthesized from academic papers. Our AI-powered system
                  searches through thousands of research papers to provide you with accurate, well-sourced information.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}