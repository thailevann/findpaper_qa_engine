"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, ExternalLink, User, Calendar, FileText } from "lucide-react"

interface Paper {
  paper_id: string
  title: string
  evidence: string
  final_score: number
  authors?: string[]
  update_date?: string
  arxiv_url?: string
}

interface ResultsSidebarProps {
  isOpen: boolean
  papers: Paper[]
  onClose: () => void
}

export function ResultsSidebar({ isOpen, papers, onClose }: ResultsSidebarProps) {
  if (!isOpen) return null

  const formatScore = (score: number) => {
    return Math.round(score * 100)
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return "Unknown"
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-sidebar border-l border-sidebar-border shadow-lg z-20">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-sidebar-foreground" />
            <h2 className="font-semibold text-sidebar-foreground">Search Results ({papers.length})</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0 hover:bg-sidebar-accent">
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Results */}
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-4">
            {papers.map((paper, index) => (
              <Card key={paper.paper_id} className="bg-sidebar-primary border-sidebar-border">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-sm font-medium text-sidebar-primary-foreground leading-tight">
                      {paper.title}
                    </CardTitle>
                    <Badge variant="secondary" className="bg-sidebar-accent/10 text-sidebar-accent text-xs shrink-0">
                      {formatScore(paper.final_score)}%
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="pt-0 space-y-3">
                  {/* Authors */}
                  {paper.authors && (
                    <div className="flex items-center gap-2">
                      <User className="w-3 h-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">
                        {paper.authors.slice(0, 2).join(", ")}
                        {paper.authors.length > 2 && ` +${paper.authors.length - 2} more`}
                      </span>
                    </div>
                  )}

                  {/* Update Date */}
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3 h-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">{formatDate(paper.update_date)}</span>
                  </div>

                  {/* Evidence */}
                  <div className="bg-muted/30 rounded-lg p-3">
                    <p className="text-xs text-sidebar-primary-foreground leading-relaxed">{paper.evidence}</p>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    {paper.arxiv_url && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 h-8 text-xs bg-transparent"
                        onClick={() => window.open(paper.arxiv_url, "_blank")}
                      >
                        <ExternalLink className="w-3 h-3 mr-1" />
                        arXiv PDF
                      </Button>
                    )}
                    <Button size="sm" variant="outline" className="flex-1 h-8 text-xs bg-transparent">
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  )
}
