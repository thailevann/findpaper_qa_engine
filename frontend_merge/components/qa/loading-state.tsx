import { Loader2, Search, FileText, Lightbulb } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/qa/ui/card"
import { Skeleton } from "@/components/qa/ui/skeleton"

export function LoadingState() {
  return (
    <div className="space-y-6">
      {/* Processing indicator */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-4">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <div className="text-center">
              <p className="font-medium">Processing your research query...</p>
              <p className="text-sm text-muted-foreground">This may take a few moments</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Processing stages */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Search className="h-8 w-8 mx-auto mb-2 text-primary animate-pulse" />
            <p className="text-sm font-medium">Searching Papers</p>
            <p className="text-xs text-muted-foreground">Finding relevant research</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <FileText className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm font-medium text-muted-foreground">Analyzing Content</p>
            <p className="text-xs text-muted-foreground">Processing passages</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Lightbulb className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm font-medium text-muted-foreground">Generating Answer</p>
            <p className="text-xs text-muted-foreground">Synthesizing insights</p>
          </CardContent>
        </Card>
      </div>

      {/* Skeleton for results */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4 text-center">
                <Skeleton className="h-8 w-16 mx-auto mb-2" />
                <Skeleton className="h-4 w-20 mx-auto" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
