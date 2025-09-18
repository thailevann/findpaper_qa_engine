"use client"

import { useState } from "react"
import { Button } from "@/components/qa/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/qa/ui/card"
import { Badge } from "@/components/qa/ui/badge"
import { Search, MessageSquare, BookOpen, Zap, ArrowRight, Users, FileText, Brain } from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null)

  const features = [
    {
      icon: Search,
      title: "Smart Paper Search",
      description: "Find relevant research papers using advanced semantic and keyword search with AI-powered query processing.",
      href: "/search",
      color: "from-green-500 to-emerald-600"
    },
    {
      icon: MessageSquare,
      title: "ScholarQA Analysis",
      description: "Get comprehensive research answers with structured sections, quotes, and comparison tables.",
      href: "/qa",
      color: "from-emerald-500 to-teal-600"
    }
  ]

  const stats = [
    { label: "Papers Indexed", value: "1M+", icon: BookOpen },
    { label: "AI Models", value: "5+", icon: Brain },
    { label: "Search Types", value: "3", icon: Zap },
    { label: "Active Users", value: "500+", icon: Users }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50">
      {/* Header */}
      <header className="border-b border-green-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-green-800">FindPaper</h1>
                <p className="text-sm text-green-600">Research Intelligence Platform</p>
              </div>
            </div>
            <div className="flex gap-3">
              <Link href="/search">
                <Button variant="outline" className="border-green-200 text-green-700 hover:bg-green-50">
                  <Search className="w-4 h-4 mr-2" />
                  Search
                </Button>
              </Link>
              <Link href="/qa">
                <Button className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  ScholarQA
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <Badge className="mb-4 bg-green-100 text-green-800 border-green-200">
            <Zap className="w-3 h-3 mr-1" />
            AI-Powered Research Platform
          </Badge>
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Discover & Analyze Research Papers with
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-500 to-emerald-600"> AI Intelligence</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            FindPaper combines advanced search capabilities with intelligent analysis to help researchers discover, 
            understand, and synthesize academic papers more effectively than ever before.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/search">
              <Button size="lg" variant="outline" className="border-green-200 text-green-700 hover:bg-green-50 px-8">
                <Search className="w-5 h-5 mr-2" />
                Start Searching
              </Button>
            </Link>
            <Link href="/qa">
              <Button size="lg" className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-8">
                <MessageSquare className="w-5 h-5 mr-2" />
                Try ScholarQA
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-20">
          {stats.map((stat, index) => (
            <Card key={index} className="text-center border-green-200 hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <stat.icon className="w-8 h-8 text-green-600 mx-auto mb-3" />
                <div className="text-3xl font-bold text-green-700 mb-1">{stat.value}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-2 gap-8 mb-20">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className={`relative overflow-hidden border-green-200 hover:shadow-xl transition-all duration-300 cursor-pointer group ${
                hoveredCard === feature.title ? 'scale-105' : ''
              }`}
              onMouseEnter={() => setHoveredCard(feature.title)}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-5 group-hover:opacity-10 transition-opacity`} />
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center`}>
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900">{feature.title}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-6 leading-relaxed">{feature.description}</p>
                <Link href={feature.href}>
                  <Button className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white">
                    Get Started
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* How It Works */}
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">How FindPaper Works</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Our platform combines cutting-edge AI with academic research to deliver unparalleled insights
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">1. Smart Search</h3>
            <p className="text-gray-600">
              Use natural language to find relevant papers with AI-powered query processing and semantic search
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">2. AI Analysis</h3>
            <p className="text-gray-600">
              Get structured answers with sections, quotes, and comparison tables from multiple papers
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">3. Export Results</h3>
            <p className="text-gray-600">
              Download your research findings in various formats for further analysis and citation
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-green-200 bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <span className="text-green-800 font-semibold">FindPaper</span>
            </div>
            <div className="text-sm text-gray-600">
              © 2024 FindPaper. Powered by AI Research Intelligence.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
