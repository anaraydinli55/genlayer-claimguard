"use client"

import { useState } from "react"
import { Search, ExternalLink, MessageSquare, ShieldCheck } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { getStatusColor, getCategoryLabel, formatAddress, formatDate } from "@/lib/utils"

interface Claim {
  id: number
  creator: string
  url: string
  description: string
  category: string
  status: string
  created_at: number
  appeal_count: number
  confidence?: number
}

const DEMO_CLAIMS: Claim[] = [
  { id: 1, creator: "0x1234...abcd", url: "https://news.example.com/article-123", description: "Verify if the partnership announcement is real", category: "fact_check", status: "verified", created_at: 1690000000, appeal_count: 0, confidence: 0.92 },
  { id: 2, creator: "0x5678...efgh", url: "https://github.com/user/repo", description: "Verify if the bounty task was completed", category: "bounty_verification", status: "pending", created_at: 1690200000, appeal_count: 0 },
  { id: 3, creator: "0x9abc...ijkl", url: "https://twitter.com/elonmusk/status/...", description: "Check if this tweet exists and matches", category: "identity_verification", status: "rejected", created_at: 1689900000, appeal_count: 1, confidence: 0.45 },
  { id: 4, creator: "0xdef0...mnop", url: "https://weather.com/forecast", description: "Prediction market resolution", category: "prediction_market", status: "verified", created_at: 1689800000, appeal_count: 0, confidence: 0.88 },
  { id: 5, creator: "0x1234...abcd", url: "https://forum.example.com/post-456", description: "Moderation request for harmful content", category: "content_moderation", status: "inconclusive", created_at: 1690300000, appeal_count: 2, confidence: 0.55 },
]

export function ClaimList() {
  const [filter, setFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")

  const filtered = DEMO_CLAIMS.filter((c) => {
    const matchesSearch = c.description.toLowerCase().includes(filter.toLowerCase()) || c.url.toLowerCase().includes(filter.toLowerCase())
    const matchesStatus = statusFilter === "all" || c.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const statuses = ["all", "pending", "verified", "rejected", "inconclusive"]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search claims..." className="pl-10" value={filter} onChange={(e) => setFilter(e.target.value)} />
        </div>
        <div className="flex gap-2 flex-wrap">
          {statuses.map((s) => (
            <button key={s} onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-all ${statusFilter === s ? "bg-violet-600 text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}>
              {s}
            </button>
          ))}
        </div>
      </div>
      <div className="grid gap-4">
        {filtered.map((claim) => (
          <Card key={claim.id} className="glass hover:shadow-md transition-all">
            <CardContent className="p-6">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                <div className="flex-1 space-y-3">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-sm font-mono text-muted-foreground">#{claim.id}</span>
                    <Badge variant="outline" className={getStatusColor(claim.status)}>{claim.status}</Badge>
                    <Badge variant="secondary" className="text-xs">{getCategoryLabel(claim.category)}</Badge>
                    {claim.appeal_count > 0 && (
                      <Badge variant="outline" className="text-xs gap-1"><MessageSquare className="w-3 h-3" /> {claim.appeal_count} appeals</Badge>
                    )}
                  </div>
                  <p className="text-sm font-medium">{claim.description}</p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>By {formatAddress(claim.creator)}</span>
                    <span>•</span>
                    <span>{formatDate(claim.created_at)}</span>
                    {claim.confidence && <><span>•</span><span className="flex items-center gap-1"><ShieldCheck className="w-3 h-3" /> Confidence: {(claim.confidence * 100).toFixed(0)}%</span></>}
                  </div>
                </div>
                <a href={claim.url} target="_blank" rel="noopener noreferrer">
                  <Button variant="ghost" size="sm" className="gap-1"><ExternalLink className="w-4 h-4" /> Evidence</Button>
                </a>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
