"use client"

import { History, X, Clock } from "lucide-react"
import { Button } from "@/components/qa/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/qa/ui/card"

interface QueryHistoryProps {
  history: string[]
  onSelect: (query: string) => void
  onClear: () => void
}

export function QueryHistory({ history, onSelect, onClear }: QueryHistoryProps) {
  if (history.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Recent Searches
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClear}>
            <X className="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {history.map((query, index) => (
            <Button
              key={index}
              variant="ghost"
              className="w-full justify-start h-auto p-3 text-left"
              onClick={() => onSelect(query)}
            >
              <Clock className="h-4 w-4 mr-3 text-muted-foreground flex-shrink-0" />
              <span className="truncate">{query}</span>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
