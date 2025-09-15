"use client"

import type React from "react"

import { useState } from "react"
import { Search, Settings, Sparkles, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Card, CardContent } from "@/components/ui/card"

interface SearchInterfaceProps {
  onSearch: (
    query: string,
    options: {
      limit: number
      maxThemes: number
      model?: string
      useMockData?: boolean
    },
  ) => void
}

const exampleQueries = [
  "What are the latest advances in machine learning?",
  "How does climate change affect biodiversity?",
  "What are the applications of quantum computing?",
  "Recent developments in renewable energy technologies",
]

export function SearchInterface({ onSearch }: SearchInterfaceProps) {
  const [query, setQuery] = useState("")
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [limit, setLimit] = useState(50)
  const [maxThemes, setMaxThemes] = useState(5)
  const [model, setModel] = useState<string>()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query.trim(), { limit, maxThemes, model })
    }
  }

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery)
    onSearch(exampleQuery, { limit, maxThemes, model })
  }

  const handleMockData = () => {
    const mockQuery = "What are the latest advances in machine learning?"
    setQuery(mockQuery)
    onSearch(mockQuery, { limit, maxThemes, model, useMockData: true })
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-5 w-5" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a research question... (e.g., 'What are the latest advances in machine learning?')"
                className="pl-10 pr-4 py-6 text-lg"
              />
            </div>

            <div className="flex items-center gap-4 flex-wrap">
              <Button type="submit" disabled={!query.trim()} className="px-8">
                <Sparkles className="mr-2 h-4 w-4" />
                Search Papers
              </Button>

              <Button type="button" variant="outline" onClick={handleMockData} className="px-6 bg-transparent">
                <Zap className="mr-2 h-4 w-4" />
                Try Mock Data
              </Button>

              <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
                <CollapsibleTrigger asChild>
                  <Button variant="outline" type="button">
                    <Settings className="mr-2 h-4 w-4" />
                    Advanced Options
                  </Button>
                </CollapsibleTrigger>
              </Collapsible>
            </div>

            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
              <CollapsibleContent className="space-y-4 pt-4 border-t">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Max Themes: {maxThemes}</Label>
                    <Slider
                      value={[maxThemes]}
                      onValueChange={(value) => setMaxThemes(value[0])}
                      max={10}
                      min={1}
                      step={1}
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Passage Limit: {limit}</Label>
                    <Slider
                      value={[limit]}
                      onValueChange={(value) => setLimit(value[0])}
                      max={100}
                      min={10}
                      step={10}
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Model Selection</Label>
                    <Select value={model} onValueChange={setModel}>
                      <SelectTrigger>
                        <SelectValue placeholder="Default model" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-4">GPT-4</SelectItem>
                        <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                        <SelectItem value="claude-3">Claude 3</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </form>
        </CardContent>
      </Card>

      {/* Example Queries */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground">Try these example queries:</h3>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((example, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => handleExampleClick(example)}
              className="text-xs"
            >
              {example}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}
