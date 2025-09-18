"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
  "Following citations that were mentioned in relevant passages",
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

    const stepDelays = searchSteps.map((_, index) => {
      if (index === 2 || index === 3 || index === 5 || index === 8 ) return 1500 // tăng thời gian cho step 3 và 4
      return 500 // bước còn lại giữ nguyên
    })

    let stepIndex = 0

    const nextStep = () => {
      setCompletedSteps((completed) => [...completed, stepIndex])
      stepIndex += 1
      if (stepIndex < searchSteps.length) {
        setCurrentStep(stepIndex)
        setTimeout(nextStep, stepDelays[stepIndex])
      } else {
        setAllStepsCompleted(true)
      }
    }

    setCurrentStep(0)
    setTimeout(nextStep, stepDelays[0])

    return () => {}
  }, [isSearching])


  // When isSearching becomes false, complete the process
  useEffect(() => {
    if (!isSearching && allStepsCompleted) {
      setTimeout(onComplete, 500)
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
                <div className="w-4 h-4 flex items-center justify-center">
                  {completedSteps.includes(index) ? (
                    <CheckCircle className="w-3 h-3 text-accent" />
                  ) : index === currentStep ? (
                    <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                  ) : (
                    <div className="w-2 h-2 bg-muted rounded-full" />
                  )}
                </div>
                <span className="text-sm">{step}</span>
                {index === currentStep && isSearching && (
                  <Badge variant="secondary" className="ml-auto text-xs">
                    {allStepsCompleted && index === searchSteps.length - 1 ? "Waiting for results..." : "Processing..."}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}