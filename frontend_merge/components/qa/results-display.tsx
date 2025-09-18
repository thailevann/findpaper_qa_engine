"use client"

import type React from "react"

import { useState } from "react"
import { Copy, Download, ChevronDown, ChevronRight, FileText, Clock, Hash, Lightbulb } from "lucide-react"
import { Button } from "@/components/qa/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/qa/ui/card"
import { Badge } from "@/components/qa/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/qa/ui/collapsible"
import { Separator } from "@/components/qa/ui/separator"
import { useToast } from "@/hooks/qa/use-toast"
import type { QAResult } from "@/app/qa/page"

interface ResultsDisplayProps {
  result: QAResult
}

export function ResultsDisplay({ result }: ResultsDisplayProps) {
  const [expandedThemes, setExpandedThemes] = useState<Set<number>>(new Set())
  const [showQuotes, setShowQuotes] = useState(false)
  const [showProcessing, setShowProcessing] = useState(false)
  const { toast } = useToast()

  const toggleTheme = (index: number) => {
    const newExpanded = new Set(expandedThemes)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedThemes(newExpanded)
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast({
        title: "Copied to clipboard",
        description: "The content has been copied to your clipboard.",
      })
    } catch (err) {
      toast({
        title: "Failed to copy",
        description: "Could not copy to clipboard.",
        variant: "destructive",
      })
    }
  }

  const downloadAsPDF = () => {
    // Simple text download for now - could be enhanced with proper PDF generation
    const content = `FindPaper ScholarQA Engine Results\n\nQuery: ${result.original_query}\n\nSummary:\n${result.scholarqa_result.summary}\n\nSections:\n${result.scholarqa_result.sections.map((section) => `- ${section.name}: ${section.narrative}`).join("\n")}`
    const blob = new Blob([content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `research-scholarqa-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Query Processing Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Query Processing
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label className="text-sm font-medium">Original Query:</Label>
            <p className="text-sm text-muted-foreground mt-1">{result.original_query}</p>
          </div>
          {result.rewritten_query && (
            <div>
              <Label className="text-sm font-medium">Rewritten Query:</Label>
              <p className="text-sm text-muted-foreground mt-1">{result.rewritten_query}</p>
            </div>
          )}
          {result.keyword_query && (
            <div>
              <Label className="text-sm font-medium">Keyword Query:</Label>
              <p className="text-sm text-muted-foreground mt-1">{result.keyword_query}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-primary">{result.finding_info.total_passages_found}</div>
            <div className="text-sm text-muted-foreground">Papers Found</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-primary">{result.scholarqa_result.metadata.total_quotes}</div>
            <div className="text-sm text-muted-foreground">Quotes Extracted</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-primary">{result.scholarqa_result.metadata.total_sections}</div>
            <div className="text-sm text-muted-foreground">Sections Created</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-primary">{result.scholarqa_result.metadata.total_papers}</div>
            <div className="text-sm text-muted-foreground">Papers Referenced</div>
          </CardContent>
        </Card>
      </div>

      {/* Main Answer Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              Research Summary
            </CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => copyToClipboard(result.scholarqa_result.summary)}>
                <Copy className="h-4 w-4 mr-2" />
                Copy
              </Button>
              <Button variant="outline" size="sm" onClick={downloadAsPDF}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none text-pretty leading-relaxed">
            {result.scholarqa_result.summary.split("\n").map((paragraph, index) => (
              <p key={index} className="mb-4 last:mb-0">
                {paragraph}
              </p>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sections Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Hash className="h-5 w-5" />
            Research Sections ({result.scholarqa_result.sections.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {result.scholarqa_result.sections.map((section, index) => (
            <div key={index} className="border rounded-lg">
              <Collapsible open={expandedThemes.has(index)} onOpenChange={() => toggleTheme(index)}>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" className="w-full justify-between p-4 h-auto">
                    <div className="flex items-center gap-3">
                      {expandedThemes.has(index) ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                      <span className="font-medium">{section.name}</span>
                      <Badge variant="secondary">{section.quote_count} quotes</Badge>
                    </div>
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="px-4 pb-4 space-y-3">
                    <div className="text-sm text-muted-foreground mb-2">{section.description}</div>
                    <div className="prose prose-sm max-w-none text-pretty leading-relaxed mb-4">
                      {section.narrative.split("\n").map((paragraph, pIndex) => (
                        <p key={pIndex} className="mb-2 last:mb-0">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                    {section.quotes.map((quote, quoteIndex) => (
                      <div key={quoteIndex} className="bg-muted/50 p-3 rounded-md">
                        <div className="text-xs text-muted-foreground mb-1">
                          From: {quote.title} (Score: {quote.score.toFixed(2)})
                        </div>
                        <p className="text-sm">{quote.quote_text}</p>
                      </div>
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Supporting Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Comparison Tables */}
        {result.scholarqa_result.comparison_tables.length > 0 && (
          <Card>
            <CardHeader>
              <Collapsible open={showQuotes} onOpenChange={setShowQuotes}>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" className="w-full justify-between p-0 h-auto">
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Comparison Tables ({result.scholarqa_result.comparison_tables.length})
                    </CardTitle>
                    {showQuotes ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </Button>
                </CollapsibleTrigger>
              </Collapsible>
            </CardHeader>
            <Collapsible open={showQuotes} onOpenChange={setShowQuotes}>
              <CollapsibleContent>
                <CardContent className="space-y-3 max-h-96 overflow-y-auto">
                  {result.scholarqa_result.comparison_tables.map((table, index) => (
                    <div key={index} className="bg-muted/50 p-3 rounded-md">
                      <div className="text-sm font-medium mb-2">{table.section}</div>
                      <div className="text-xs text-muted-foreground">
                        {table.paper_count} papers compared
                      </div>
                    </div>
                  ))}
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>
        )}

        {/* Processing Details */}
        <Card>
          <CardHeader>
            <Collapsible open={showProcessing} onOpenChange={setShowProcessing}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="w-full justify-between p-0 h-auto">
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Processing Details
                  </CardTitle>
                  {showProcessing ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </Button>
              </CollapsibleTrigger>
            </Collapsible>
          </CardHeader>
          <Collapsible open={showProcessing} onOpenChange={setShowProcessing}>
            <CollapsibleContent>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Total Passages Found:</span>
                    <div className="text-muted-foreground">{result.finding_info.total_passages_found}</div>
                  </div>
                  <div>
                    <span className="font-medium">Passages Used for QA:</span>
                    <div className="text-muted-foreground">{result.finding_info.passages_used_for_qa}</div>
                  </div>
                  <div>
                    <span className="font-medium">Sections Created:</span>
                    <div className="text-muted-foreground">{result.scholarqa_result.metadata.total_sections}</div>
                  </div>
                  <div>
                    <span className="font-medium">Quotes Extracted:</span>
                    <div className="text-muted-foreground">{result.scholarqa_result.metadata.total_quotes}</div>
                  </div>
                </div>
                {Object.keys(result.gemini_filters).length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <span className="font-medium text-sm">Applied Filters:</span>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {JSON.stringify(result.gemini_filters, null, 2)}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>
      </div>
    </div>
  )
}

function Label({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <label className={`text-sm font-medium ${className}`}>{children}</label>
}
