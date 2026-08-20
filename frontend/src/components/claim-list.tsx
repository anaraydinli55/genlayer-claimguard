"use client"

import { useEffect, useState } from "react"
import { Search, ExternalLink, MessageSquare, ShieldCheck } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  getStatusColor,
  getCategoryLabel,
  formatAddress,
  formatDate,
} from "@/lib/utils"
import { genlayerClient, CLAIMGUARD_ADDRESS } from "@/lib/genlayer-client"

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

export function ClaimList() {
  const [claims, setClaims] = useState<Claim[]>([])
  const [filter, setFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    async function loadClaims() {
      try {
        setLoading(true)
        setError("")

        const stats = await genlayerClient.readContract({
          address: CLAIMGUARD_ADDRESS,
          functionName: "getStats",
          args: [],
        }) as any

        const total = Number(stats?.total_claims ?? 0)

        if (total === 0) {
          setClaims([])
          return
        }

        const results = await Promise.all(
          Array.from({ length: total }, (_, i) =>
            genlayerClient.readContract({
              address: CLAIMGUARD_ADDRESS,
              functionName: "getClaim",
              args: [i + 1],
            })
          )
        )

        const parsed: Claim[] = results.map((raw: any, index) => {
          let confidence: number | undefined

          try {
            if (raw?.resolution) {
              const resolution =
                typeof raw.resolution === "string"
                  ? JSON.parse(raw.resolution)
                  : raw.resolution

              if (typeof resolution?.confidence === "number") {
                confidence = resolution.confidence
              }
            }
          } catch {
            confidence = undefined
          }

          return {
            id: index + 1,
            creator: String(raw?.creator ?? ""),
            url: String(raw?.url ?? ""),
            description: String(raw?.description ?? ""),
            category: String(raw?.category ?? ""),
            status: String(raw?.status ?? "pending"),
            created_at: Number(raw?.created_at ?? 0),
            appeal_count: Number(raw?.appeal_count ?? 0),
            confidence,
          }
        })

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

  const filtered = claims.filter((claim) => {
    const query = filter.toLowerCase()

    const matchesSearch =
      claim.description.toLowerCase().includes(query) ||
      claim.url.toLowerCase().includes(query)

    const matchesStatus =
      statusFilter === "all" || claim.status === statusFilter

    return matchesSearch && matchesStatus
  })

  const statuses = [
    "all",
    "pending",
    "verified",
    "rejected",
    "inconclusive",
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />

          <Input
            placeholder="Search claims..."
            className="pl-10"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>

        <div className="flex gap-2 flex-wrap">
          {statuses.map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-all ${
                statusFilter === status
                  ? "bg-violet-600 text-white"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="text-center py-12 text-muted-foreground">
          Loading claims...
        </div>
      )}

      {!loading && error && (
        <div className="text-center py-12 text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No claims found.
        </div>
      )}

      <div className="grid gap-4">
        {filtered.map((claim) => (
          <Card
            key={claim.id}
            className="glass hover:shadow-md transition-all"
          >
            <CardContent className="p-6">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                <div className="flex-1 space-y-3">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-sm font-mono text-muted-foreground">
                      #{claim.id}
                    </span>

                    <Badge
                      variant="outline"
                      className={getStatusColor(claim.status)}
                    >
                      {claim.status}
                    </Badge>

                    <Badge variant="secondary" className="text-xs">
                      {getCategoryLabel(claim.category)}
                    </Badge>

                    {claim.appeal_count > 0 && (
                      <Badge
                        variant="outline"
                        className="text-xs gap-1"
                      >
                        <MessageSquare className="w-3 h-3" />
                        {claim.appeal_count} appeals
                      </Badge>
                    )}
                  </div>

                  <p className="text-sm font-medium">
                    {claim.description}
                  </p>

                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>By {formatAddress(claim.creator)}</span>
                    <span>•</span>
                    <span>{formatDate(claim.created_at)}</span>

                    {claim.confidence !== undefined && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3" />
                          Confidence:{" "}
                          {(claim.confidence * 100).toFixed(0)}%
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {claim.url && (
                  <a
                    href={claim.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button
                      variant="ghost"
                      size="sm"
                      className="gap-1"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Evidence
                    </Button>
                  </a>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
