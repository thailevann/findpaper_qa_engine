"use client"

import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface ErrorDisplayProps {
  error: string
  onRetry: () => void
}

export function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  const isNetworkError = error.includes("fetch") || error.includes("network") || error.includes("connection")
  const isServerError = error.includes("500") || error.includes("502") || error.includes("503")

  return (
    <Card className="border-destructive/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-5 w-5" />
          Error Processing Request
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>

        <div className="space-y-3">
          <h4 className="font-medium">Troubleshooting Tips:</h4>
          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            {isNetworkError && (
              <>
                <li>Check your internet connection</li>
                <li>Ensure the API server is running on http://localhost:8000</li>
              </>
            )}
            {isServerError && (
              <>
                <li>The server may be temporarily unavailable</li>
                <li>Try again in a few moments</li>
              </>
            )}
            <li>Try rephrasing your research question</li>
            <li>Check if your query is too broad or too specific</li>
            <li>Ensure the backend API is properly configured</li>
          </ul>
        </div>

        <div className="flex gap-2">
          <Button onClick={onRetry} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
