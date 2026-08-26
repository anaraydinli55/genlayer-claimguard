"use client"

import { useEffect, useState } from "react"
import { Search, ExternalLink, MessageSquare, ShieldCheck, Gavel, RotateCcw } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { getStatusColor, getCategoryLabel, formatAddress, formatDate } from "@/lib/utils"
import { genlayerClient, CLAIMGUARD_ADDRESS } from "@/lib/genlayer-client"
import { useClaimGuard } from "@/hooks/use-claimguard"

interface Claim {
  id: number
  creator: string
  evidence_url: string
  description: string
  category: string
  status: string
  created_at: number
  appeal_count: number
  confidence: number
  reasoning: string
  expected_content: string
}

export function ClaimList() {
  const [claims, setClaims] = useState<Claim[]>([])
  const [filter, setFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [appealUrl, setAppealUrl] = useState<string>("")

  const { resolveClaim, appealClaim } = useClaimGuard()

  useEffect(() => {
    async function loadClaims() {
      try {
        setLoading(true)
        setError("")

        const result = await genlayerClient.readContract({
          address: CLAIMGUARD_ADDRESS,
          functionName: "getAllClaims",
          args: [],
        }) as any[]

        const parsed: Claim[] = (result || []).map((raw: any) => ({
          id: Number(raw?.id ?? 0),
          creator: String(raw?.creator ?? ""),
          evidence_url: String(raw?.evidence_url ?? ""),
          description: String(raw?.description ?? ""),
          category: String(raw?.category ?? ""),
          status: String(raw?.status ?? "pending"),
          created_at: Number(raw?.created_at ?? 0),
          appeal_count: Number(raw?.appeal_count ?? 0),
          confidence: Number(raw?.confidence ?? 0),
          reasoning: String(raw?.reasoning ?? ""),
          expected_content: String(raw?.expected_content ?? ""),
        }))

        setClaims(parsed.reverse())
      } catch (err) {
        console.error(err)
        setError("Claims could not be loaded.")
        setClaims([])
      } finally {
        setLoading(false)
      }
    }

    loadClaims()
  }, [])

  const handleResolve = async (claimId: number) => {
    setActionLoading(claimId)
    try {
      await resolveClaim(String(claimId))
      window.location.reload()
    } catch (err: any) {
      alert(`Resolve failed: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleAppeal = async (claimId: number) => {
    setActionLoading(claimId)
    try {
      await appealClaim(String(claimId), appealUrl)
      setAppealUrl("")
      window.location.reload()
    } catch (err: any) {
      alert(`Appeal failed: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const filtered = claims.filter((claim) => {
    const query = filter.toLowerCase()
    const matchesSearch =
      claim.description.toLowerCase().includes(query) ||
      claim.evidence_url.toLowerCase().includes(query) ||
      claim.expected_content.toLowerCase().includes(query)
    const matchesStatus = statusFilter === "all" || claim.status === statusFilter
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
          {statuses.map((status) => (
            <button key={status} onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-all ${statusFilter === status ? "bg-violet-600 text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}>
              {status}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="text-center py-12 text-muted-foreground">Loading claims...</div>}
      {!loading && error && <div className="text-center py-12 text-red-400">{error}</div>}
      {!loading && !error && filtered.length === 0 && <div className="text-center py-12 text-muted-foreground">No claims found.</div>}

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
                      <Badge variant="outline" className="text-xs gap-1"><MessageSquare className="w-3 h-3" />{claim.appeal_count} appeals</Badge>
                    )}
                  </div>

                  <p className="text-sm font-medium">{claim.description}</p>
                  <p className="text-xs text-muted-foreground">Expected: {claim.expected_content}</p>

                  {claim.reasoning && claim.status !== "pending" && (
                    <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded">
                      <span className="font-semibold">Reasoning:</span> {claim.reasoning}
                    </div>
                  )}

                  <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                    <span>By {formatAddress(claim.creator)}</span>
                    <span>•</span>
                    <span>{formatDate(claim.created_at)}</span>
                    {claim.confidence > 0 && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-1"><ShieldCheck className="w-3 h-3" />Confidence: {(claim.confidence * 100).toFixed(0)}%</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  {claim.status === "pending" && (
                    <Button variant="outline" size="sm" className="gap-1" onClick={() => handleResolve(claim.id)} disabled={actionLoading === claim.id}>
                      <Gavel className="w-4 h-4" />{actionLoading === claim.id ? "Resolving..." : "Resolve"}
                    </Button>
                  )}

                  {claim.status !== "pending" && claim.appeal_count < 3 && (
                    <div className="flex flex-col gap-2">
                      <Input placeholder="New evidence URL (optional)" value={appealUrl} onChange={(e) => setAppealUrl(e.target.value)} className="text-xs h-8" />
                      <Button variant="ghost" size="sm" className="gap-1" onClick={() => handleAppeal(claim.id)} disabled={actionLoading === claim.id}>
                        <RotateCcw className="w-4 h-4" />{actionLoading === claim.id ? "Appealing..." : "Appeal"}
                      </Button>
                    </div>
                  )}

                  {claim.evidence_url && (
                    <a href={claim.evidence_url} target="_blank" rel="noopener noreferrer">
                      <Button variant="ghost" size="sm" className="gap-1"><ExternalLink className="w-4 h-4" />Evidence</Button>
                    </a>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
