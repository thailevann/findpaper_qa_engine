"use client"

import { useState } from "react"
import { Button } from "@/components/qa/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/qa/ui/card"
import { Badge } from "@/components/qa/ui/badge"
import {
  Search,
  MessageSquare,
  BookOpen,
  Zap,
  ArrowRight,
  Users,
  FileText,
  Brain,
  Sparkles,
  TrendingUp,
  Award,
} from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null)

  const features = [
    {
      icon: Search,
      title: "Intelligent Paper Discovery",
      description:
        "Advanced semantic search powered by AI to find the most relevant research papers for your specific queries and research needs.",
      href: "/search",
      color: "primary",
      stats: "1M+ papers indexed",
    },
    {
      icon: MessageSquare,
      title: "ScholarQA Intelligence",
      description:
        "Get comprehensive research insights with structured analysis, evidence-based quotes, and comparative tables across multiple papers.",
      href: "/qa",
      color: "secondary",
      stats: "AI-powered analysis",
    },
  ]

  const stats = [
    { label: "Research Papers", value: "1.2M+", icon: BookOpen, trend: "+15%" },
    { label: "AI Models", value: "8", icon: Brain, trend: "Latest" },
    { label: "Search Accuracy", value: "94%", icon: Award, trend: "+5%" },
    { label: "Active Researchers", value: "12K+", icon: Users, trend: "+28%" },
  ]

  const workflows = [
    {
      step: "01",
      title: "Intelligent Query Processing",
      description:
        "Our AI understands your research intent and transforms natural language queries into optimized search parameters.",
      icon: Brain,
    },
    {
      step: "02",
      title: "Multi-Modal Search",
      description:
        "Combines semantic understanding, keyword matching, and citation analysis to find the most relevant papers.",
      icon: Search,
    },
    {
      step: "03",
      title: "Evidence Synthesis",
      description:
        "Automatically extracts key insights, generates summaries, and creates comparison tables from multiple sources.",
      icon: Sparkles,
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-lg">
                  <FileText className="w-6 h-6 text-primary-foreground" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-secondary rounded-full flex items-center justify-center">
                  <Sparkles className="w-2.5 h-2.5 text-secondary-foreground" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">FindPaper</h1>
                <p className="text-sm text-muted-foreground font-medium">AI Research Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/search">
                <Button variant="outline" size="sm" className="font-medium bg-transparent">
                  <Search className="w-4 h-4 mr-2" />
                  Search Papers
                </Button>
              </Link>
              <Link href="/qa">
                <Button size="sm" className="font-medium shadow-lg">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  ScholarQA
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/5" />
        <div className="relative max-w-7xl mx-auto px-6 py-24">
          <div className="text-center max-w-4xl mx-auto">
            <Badge className="mb-6 bg-primary/10 text-primary border-primary/20 font-medium px-4 py-2">
              <Zap className="w-4 h-4 mr-2" />
              Next-Generation Research Platform
            </Badge>

            <h1 className="text-6xl font-bold text-foreground mb-8 text-balance leading-tight">
              Accelerate Your Research with
              <span className="text-primary block mt-2">AI-Powered Discovery</span>
            </h1>

            <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-12 text-pretty leading-relaxed">
              Transform how you discover, analyze, and synthesize academic research. Our advanced AI platform helps
              researchers find relevant papers faster and extract deeper insights from scientific literature.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link href="/search">
                <Button size="lg" variant="outline" className="px-8 py-6 text-lg font-medium min-w-48 bg-transparent">
                  <Search className="w-5 h-5 mr-3" />
                  Start Searching
                </Button>
              </Link>
              <Link href="/qa">
                <Button size="lg" className="px-8 py-6 text-lg font-medium shadow-xl min-w-48">
                  <MessageSquare className="w-5 h-5 mr-3" />
                  Try ScholarQA
                  <ArrowRight className="w-5 h-5 ml-3" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-card/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <Card
                key={index}
                className="text-center border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-background"
              >
                <CardContent className="p-8">
                  <div className="flex items-center justify-center mb-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                      <stat.icon className="w-6 h-6 text-primary" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-foreground mb-2">{stat.value}</div>
                  <div className="text-sm text-muted-foreground mb-2">{stat.label}</div>
                  <Badge variant="secondary" className="text-xs font-medium">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    {stat.trend}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-secondary/10 text-secondary border-secondary/20 font-medium">Core Features</Badge>
            <h2 className="text-4xl font-bold text-foreground mb-6">Powerful Research Tools</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
              Everything you need to conduct comprehensive literature reviews and stay ahead in your field
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <Card
                key={index}
                className={`group relative overflow-hidden border-0 shadow-lg hover:shadow-2xl transition-all duration-500 cursor-pointer ${
                  hoveredCard === feature.title ? "scale-[1.02]" : ""
                }`}
                onMouseEnter={() => setHoveredCard(feature.title)}
                onMouseLeave={() => setHoveredCard(null)}
              >
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${
                    feature.color === "primary" ? "from-primary/5 to-primary/10" : "from-secondary/5 to-secondary/10"
                  } opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
                />

                <CardHeader className="relative">
                  <div className="flex items-start gap-6">
                    <div
                      className={`w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg ${
                        feature.color === "primary" ? "bg-primary" : "bg-secondary"
                      }`}
                    >
                      <feature.icon className="w-8 h-8 text-white" />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-2xl text-foreground mb-2">{feature.title}</CardTitle>
                      <Badge variant="outline" className="text-xs font-medium">
                        {feature.stats}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="relative">
                  <p className="text-muted-foreground mb-8 leading-relaxed text-lg">{feature.description}</p>
                  <Link href={feature.href}>
                    <Button className="w-full font-medium shadow-lg group-hover:shadow-xl transition-shadow">
                      Get Started
                      <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-card/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-primary/10 text-primary border-primary/20 font-medium">How It Works</Badge>
            <h2 className="text-4xl font-bold text-foreground mb-6">Research Made Simple</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
              Our AI-powered platform streamlines the entire research discovery process
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {workflows.map((workflow, index) => (
              <div key={index} className="text-center group">
                <div className="relative mb-8">
                  <div className="w-20 h-20 bg-primary rounded-2xl flex items-center justify-center mx-auto shadow-xl group-hover:shadow-2xl transition-shadow">
                    <workflow.icon className="w-10 h-10 text-primary-foreground" />
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-secondary rounded-full flex items-center justify-center text-secondary-foreground font-bold text-sm shadow-lg">
                    {workflow.step}
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-foreground mb-4">{workflow.title}</h3>
                <p className="text-muted-foreground leading-relaxed text-lg">{workflow.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-background">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-lg">
                <FileText className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <span className="text-xl font-bold text-foreground">FindPaper</span>
                <p className="text-sm text-muted-foreground">AI Research Intelligence</p>
              </div>
            </div>
            <div className="text-center md:text-right">
              <p className="text-muted-foreground">© 2024 FindPaper. Empowering researchers worldwide.</p>
              <p className="text-sm text-muted-foreground mt-1">Built with AI • Designed for Discovery</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
