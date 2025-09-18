import { BookOpen, Search, Lightbulb, TrendingUp } from "lucide-react"
import { Card, CardContent } from "@/components/qa/ui/card"

export function EmptyState() {
  return (
    <div className="text-center py-12">
      <div className="mx-auto w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mb-6">
        <BookOpen className="h-12 w-12 text-primary" />
      </div>

      <h2 className="text-2xl font-bold mb-4">Welcome to FindPaper QA Engine</h2>
      <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
        Ask research questions and get comprehensive answers synthesized from academic papers. Our AI-powered system
        searches through thousands of research papers to provide you with accurate, well-sourced information.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-6 text-center">
            <Search className="h-8 w-8 mx-auto mb-4 text-primary" />
            <h3 className="font-semibold mb-2">Smart Search</h3>
            <p className="text-sm text-muted-foreground">
              Advanced query processing finds the most relevant research papers for your question
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Lightbulb className="h-8 w-8 mx-auto mb-4 text-primary" />
            <h3 className="font-semibold mb-2">AI Analysis</h3>
            <p className="text-sm text-muted-foreground">
              Intelligent synthesis of information from multiple sources into coherent answers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <TrendingUp className="h-8 w-8 mx-auto mb-4 text-primary" />
            <h3 className="font-semibold mb-2">Research Insights</h3>
            <p className="text-sm text-muted-foreground">
              Organized themes and citations help you understand complex research topics
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
