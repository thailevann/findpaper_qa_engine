"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/search/ui/card"
import { Badge } from "@/components/search/ui/badge"
import { Button } from "@/components/search/ui/button"
import { CheckCircle, Clock, ChevronDown, ChevronUp } from "lucide-react"

interface SearchStepsProps {
  isSearching: boolean
  query: string
  onComplete: () => void
}

const searchSteps = [
  "Analyzing your request",
  "Attempting to fetch query",
  "Searching for papers",
  "Running keyword and semantic searches",
  "Reranking candidate documents",
  "Assessing relevance of retrieved papers",
  "Found relevant papers",
  "Sorting and ranking papers",
  "Finalizing results",
]

export function SearchSteps({ isSearching, query, onComplete }: SearchStepsProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<number[]>([])
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [allStepsCompleted, setAllStepsCompleted] = useState(false)

  useEffect(() => {
    if (!isSearching) return

    // reset state mỗi lần search mới
    setCurrentStep(0)
    setCompletedSteps([])
    setAllStepsCompleted(false)

    const stepDelays = searchSteps.map((_, index) => (index === 4 ? 500 : 300))
    let stepIndex = 0
    let timeoutId: ReturnType<typeof setTimeout>

    const nextStep = () => {
      // đánh dấu step trước completed
      if (stepIndex > 0) {
        setCompletedSteps((completed) => [...completed, stepIndex - 1])
      }

      // nếu còn step thì chuyển currentStep
      if (stepIndex < searchSteps.length) {
        setCurrentStep(stepIndex)
        timeoutId = setTimeout(() => {
          stepIndex += 1
          nextStep()
        }, stepDelays[stepIndex])
      } else {
        // hoàn tất toàn bộ steps
        setCompletedSteps((completed) => [...completed, searchSteps.length - 1])
        setAllStepsCompleted(true)
      }
    }

    // bắt đầu chạy
    nextStep()

    return () => clearTimeout(timeoutId)
  }, [isSearching])

  // Khi isSearching trở về false, gọi onComplete
  useEffect(() => {
    if (!isSearching && allStepsCompleted) {
      const timer = setTimeout(onComplete, 100)
      return () => clearTimeout(timer)
    }
  }, [isSearching, allStepsCompleted, onComplete])

  return (
    <Card className="border-accent/20">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-accent rounded-full flex items-center justify-center">
              {isSearching ? (
                <Clock className="w-3 h-3 text-accent-foreground animate-spin" />
              ) : (
                <CheckCircle className="w-3 h-3 text-accent-foreground" />
              )}
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{isSearching ? "Searching..." : "Search Complete"}</h3>
              <p className="text-sm text-muted-foreground">Query: "{query}"</p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="flex items-center gap-1"
          >
            {isCollapsed ? (
              <>
                <ChevronDown className="w-4 h-4" />
                Show steps
              </>
            ) : (
              <>
                <ChevronUp className="w-4 h-4" />
                Collapse steps
              </>
            )}
          </Button>
        </div>

      {!isCollapsed && (
        <div className="space-y-2">
          {searchSteps.map((step, index) => (
            <div
              key={index}
              className={`flex items-center gap-3 p-2 rounded-lg transition-all duration-200 ${
                completedSteps.includes(index)
                  ? "bg-accent/10 text-foreground"
                  : index === currentStep
                  ? "bg-accent/5 text-foreground"
                  : "text-muted-foreground"
              }`}
            >
              {/* Icon bên trái */}
              <div className="w-4 h-4 flex items-center justify-center">
                {completedSteps.includes(index) ? (
                  <CheckCircle className="w-3 h-3 text-accent" />
                ) : index === currentStep ? (
                  <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                ) : (
                  <div className="w-2 h-2 bg-muted rounded-full" />
                )}
              </div>

              {/* Nội dung step */}
              <span className="text-sm">{step}</span>

              {/* Slot cố định cho badge */}
              <div className="ml-auto min-w-[7rem] flex justify-end">
                {index === currentStep && isSearching && (
                  <Badge variant="secondary" className="text-xs">
                    {allStepsCompleted && index === searchSteps.length - 1
                      ? "Waiting for results..."
                      : "Processing..."}
                  </Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      </CardContent>
    </Card>
  )
}
