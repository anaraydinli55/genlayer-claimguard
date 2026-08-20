"use client"

import { useState, useEffect } from "react"
import { CheckCircle, XCircle, Clock, BarChart3 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Stats {
  total_claims: number
  verified: number
  rejected: number
  pending: number
  success_rate: number
}

export function StatsOverview() {
  const [stats, setStats] = useState<Stats>({
    total_claims: 0, verified: 0, rejected: 0, pending: 0, success_rate: 0,
  })

  useEffect(() => {
    setStats({ total_claims: 142, verified: 98, rejected: 31, pending: 13, success_rate: 0.69 })
  }, [])

  const items = [
    { label: "Total Claims", value: stats.total_claims, icon: BarChart3, color: "text-violet-600" },
    { label: "Verified", value: stats.verified, icon: CheckCircle, color: "text-emerald-600" },
    { label: "Rejected", value: stats.rejected, icon: XCircle, color: "text-red-600" },
    { label: "Pending", value: stats.pending, icon: Clock, color: "text-yellow-600" },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {items.map((item) => (
        <Card key={item.label} className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{item.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <item.icon className={`w-5 h-5 ${item.color}`} />
              <span className="text-3xl font-bold">{item.value}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
