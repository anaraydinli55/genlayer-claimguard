"use client"

import { useState } from "react"
import { Gavel, Loader2, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useClaimGuard } from "@/hooks/use-claimguard"

export function ResolveClaimForm({ claimId, onResolved }: { claimId: string; onResolved?: () => void }) {
  const [result, setResult] = useState<string | null>(null)
  const { resolveClaim, loading, error, isConnected } = useClaimGuard()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    if (!isConnected) { 
      setResult("Please connect your wallet first!")
      return 
    }
    try {
      const txResult = await resolveClaim(claimId)
      setResult(`Claim resolution triggered on-chain! Transaction: ${txResult}`)
      onResolved?.()
    } catch (err: any) { 
      setResult(`Error: ${err.message}`) 
    }
  }

  return (
    <Card className="glass max-w-xl mx-auto">
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2">
          <Gavel className="w-5 h-5 text-violet-500" /> Resolve Claim #{claimId}
        </CardTitle>
        <CardDescription>
          Trigger GenLayer validator LLM consensus to fetch real-time web evidence and resolve this claim autonomously on-chain.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20 text-sm text-violet-300 flex items-start gap-3">
            <Sparkles className="w-5 h-5 shrink-0 text-violet-400 mt-0.5" />
            <div>
              <p className="font-semibold text-violet-200">Decentralized Evidence-Based Consensus</p>
              <p className="mt-1 text-xs text-violet-300/80">
                No manual verdict required. GenLayer validators will fetch the source URL, evaluate the claim against extracted content, and establish the on-chain verdict automatically.
              </p>
            </div>
          </div>

          <Button type="submit" variant="gradient" className="w-full gap-2 py-6 text-base font-medium" disabled={loading || !isConnected}>
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Gavel className="w-5 h-5" />} 
            {loading ? "Resolving via Validator Consensus..." : "Trigger Consensus Resolution"}
          </Button>
          
          {error && <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}
          {result && !error && <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">{result}</div>}
        </form>
      </CardContent>
    </Card>
  )
}
