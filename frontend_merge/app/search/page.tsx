"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/search/ui/button"
import { Input } from "@/components/search/ui/input"
import { Card, CardContent } from "@/components/search/ui/card"
import { Badge } from "@/components/search/ui/badge"

import { SearchSteps } from "@/components/search/search-steps"
import { Search, Send, ChevronRight, ChevronLeft, ArrowLeft, MessageSquare } from "lucide-react"
import Link from "next/link"


interface Paper {
  paper_id: string
  title: string
  evidence: string
  final_score: number
  authors?: string[]
  update_date?: string
}

interface SearchResult {
  original_query: string
  rewritten_query: string
  keyword_query: string
  matched_count: number
  matched_papers: Paper[]
  perfect_matches: number
  relevant_matches: number
  other_matches: number
}

export default function PaperSearchChatbot() {
  const [query, setQuery] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)
  const [showSteps, setShowSteps] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setShowSteps(true);
    setSearchResult(null);

    try {
      const response = await fetch("http://localhost:8000/top_papers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query, limit: 50 }),
      });
      if (!response.ok) {
        throw new Error("Failed to fetch papers");
      }
      const data = await response.json();
      // Map API response to SearchResult type
      const apiResult: SearchResult = {
        original_query: data.original_query,
        rewritten_query: data.rewritten_query,
        keyword_query: data.keyword_query,
        matched_count: data.matched_count,
        matched_papers: data.matched_papers,
        perfect_matches: data.matched_papers?.length ?? 0, // You may want to update this logic if API returns more info
        relevant_matches: 0,
        other_matches: 0,
      };
      setSearchResult(apiResult);
      setSidebarOpen(true);
    } catch (error) {
      // Optionally handle error UI
      setSearchResult(null);
      alert("Error fetching papers: " + (error as Error).message);
    } finally {
      setIsSearching(false);
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Main Content */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? "mr-96" : ""}`}>
        {/* Header */}
        <header className="border-b bg-background/80 backdrop-blur-xl sticky top-0 z-10">
          <div className="max-w-4xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                  <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-lg">
                    <Search className="w-4 h-4 text-primary-foreground" />
                  </div>
                  <h1 className="text-xl font-semibold text-foreground">Paper Search</h1>
                </Link>
              </div>
              <div className="flex gap-2">
                <Link href="/">
                  <Button variant="outline" size="sm" className="font-medium bg-transparent">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Home
                  </Button>
                </Link>
                <Link href="/qa">
                  <Button size="sm" className="font-medium shadow-lg">
                    <MessageSquare className="h-4 w-4 mr-2" />
                    ScholarQA
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </header>

        {/* Chat Area */}
        <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-8">
          <div className="space-y-6">
            {/* Welcome Message */}
            {!showSteps && !searchResult && (
              <Card className="border-0 shadow-lg bg-card/30">
                <CardContent className="p-8">
                  <h2 className="text-3xl font-bold text-foreground mb-4">Welcome to Paper Search</h2>
                  <p className="text-muted-foreground text-lg text-pretty leading-relaxed">
                    Describe the papers you're looking for and I'll help you find the most relevant research papers with
                    detailed analysis and evidence using our advanced AI-powered search engine.
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Search Steps */}
            {showSteps && (
              <SearchSteps isSearching={isSearching} query={query} onComplete={() => setShowSteps(false)} />
            )}

            {/* Search Results */}
            {searchResult && (
              <Card>
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20 font-medium">
                      Search Complete
                    </Badge>
                  </div>
                  <div className="text-foreground">
                    <span className="font-medium">Asta</span> found {searchResult.matched_papers.length} papers
                  </div>
                  <div className="bg-muted/50 rounded-lg p-4 space-y-2">
                    <p className="text-sm font-medium text-foreground mb-1">This is what I searched for:</p>
                    <div className="text-sm text-muted-foreground">Keyword: {searchResult.keyword_query}</div>
                    <div className="text-sm text-muted-foreground">Rewritten query: {searchResult.rewritten_query}</div>
                  </div>
                  <div className="space-y-4 pt-2">
                    {searchResult.matched_papers.map((paper) => (
                      <div key={paper.paper_id} className="border rounded-xl p-6 bg-card/50 shadow-sm hover:shadow-md transition-shadow">
                        <div className="font-semibold text-foreground mb-3 text-lg">{paper.title}</div>
                        <div className="text-muted-foreground mb-4 leading-relaxed">Evidence: {paper.evidence}</div>
                        <a 
                          href={`https://arxiv.org/pdf/${paper.paper_id}`} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-sm text-primary hover:text-primary/80 underline hover:no-underline transition-colors font-medium"
                        >
                          View PDF: https://arxiv.org/pdf/{paper.paper_id}
                        </a>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </main>

        {/* Search Input */}
        <div className="border-t border-border bg-card/50 backdrop-blur-sm sticky bottom-0">
          <div className="max-w-4xl mx-auto px-6 py-4">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Describe the papers you're looking for..."
                  className="pr-12 bg-background"
                  disabled={isSearching}
                />
                <Button
                  size="sm"
                  onClick={handleSearch}
                  disabled={!query.trim() || isSearching}
                  className="absolute right-1 top-1 h-8 w-8 p-0"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}