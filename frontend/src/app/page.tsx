"use client"

import { useState } from "react"
import { Shield, Zap, Globe, Brain, ArrowRight, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { CreateClaimForm } from "@/components/create-claim-form"
import { ClaimList } from "@/components/claim-list"
import { StatsOverview } from "@/components/stats-overview"

export default function Home() {
  const [activeTab, setActiveTab] = useState<"overview" | "create" | "claims">("overview")

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-center py-16 lg:py-24">
        <div className="inline-flex items-center gap-2 rounded-full bg-violet-500/10 border border-violet-500/20 px-4 py-1.5 text-sm font-medium text-violet-600 dark:text-violet-400 mb-6">
          <Zap className="w-4 h-4" /> GenLayer Intelligent Contract
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight mb-6">
          Verify Claims with <span className="gradient-text">AI Consensus</span>
        </h1>
        <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
          ClaimGuard is a reusable GenLayer primitive that verifies real-world claims
          by fetching web evidence and using LLM consensus to evaluate truthfulness.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" variant="gradient" className="gap-2" onClick={() => setActiveTab("create")}>
            Submit a Claim <ArrowRight className="w-4 h-4" />
          </Button>
          <Button size="lg" variant="outline" className="gap-2" onClick={() => setActiveTab("claims")}>
            <Activity className="w-4 h-4" /> View Claims
          </Button>
        </div>
      </div>

      <div className="flex justify-center mb-8">
        <div className="inline-flex bg-muted rounded-xl p-1 gap-1">
          {(["overview", "create", "claims"] as const).map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === tab ? "bg-white dark:bg-slate-800 shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
              {tab === "overview" && "Overview"}{tab === "create" && "Submit Claim"}{tab === "claims" && "All Claims"}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "overview" && (
        <>
          <StatsOverview />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <FeatureCard icon={<Globe className="w-6 h-6" />} title="Web Evidence"
              description="Fetches real-time web content as evidence using GenLayer's non-deterministic web rendering." />
            <FeatureCard icon={<Brain className="w-6 h-6" />} title="LLM Consensus"
              description="Uses json_eq equivalence principle to ensure all validators agree on structured AI evaluations." />
            <FeatureCard icon={<Shield className="w-6 h-6" />} title="Appeal System"
              description="Built-in appeal mechanism allows claims to be re-evaluated with new evidence up to 3 times." />
          </div>
        </>
      )}
      {activeTab === "create" && <CreateClaimForm />}
      {activeTab === "claims" && <ClaimList />}
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <Card className="glass hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 flex items-center justify-center text-violet-600 dark:text-violet-400 mb-4">{icon}</div>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
    </Card>
  )
}
