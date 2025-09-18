import { BookOpen, Search, Lightbulb, TrendingUp } from "lucide-react"
import { Card, CardContent } from "@/components/qa/ui/card"

export function EmptyState() {
  return (
    <div className="text-center py-16">
      <div className="mx-auto w-32 h-32 bg-primary/10 rounded-2xl flex items-center justify-center mb-8 shadow-lg">
        <BookOpen className="h-16 w-16 text-primary" />
      </div>

      <h2 className="text-4xl font-bold mb-6 text-foreground">Welcome to ScholarQA Intelligence</h2>
      <p className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto text-pretty leading-relaxed">
        Ask research questions and get comprehensive answers synthesized from academic papers. Our AI-powered system
        searches through thousands of research papers to provide you with accurate, well-sourced information and structured analysis.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow bg-card/30">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-6">
              <Search className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-4 text-foreground">Smart Search</h3>
            <p className="text-muted-foreground leading-relaxed">
              Advanced query processing finds the most relevant research papers for your question using semantic understanding
            </p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow bg-card/30">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-6">
              <Lightbulb className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-4 text-foreground">AI Analysis</h3>
            <p className="text-muted-foreground leading-relaxed">
              Intelligent synthesis of information from multiple sources into coherent answers with structured sections
            </p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow bg-card/30">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-6">
              <TrendingUp className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-4 text-foreground">Research Insights</h3>
            <p className="text-muted-foreground leading-relaxed">
              Organized themes, quotes, and comparison tables help you understand complex research topics
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
