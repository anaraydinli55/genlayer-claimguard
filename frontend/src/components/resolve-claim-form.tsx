"use client"

import { useState } from "react"
import { Gavel, CheckCircle, XCircle, HelpCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { useClaimGuard } from "@/hooks/use-claimguard"

const VERDICTS = [
  { value: "VERIFIED", label: "Verified", icon: <CheckCircle className="w-4 h-4" />, color: "bg-emerald-600" },
  { value: "REJECTED", label: "Rejected", icon: <XCircle className="w-4 h-4" />, color: "bg-red-600" },
  { value: "INCONCLUSIVE", label: "Inconclusive", icon: <HelpCircle className="w-4 h-4" />, color: "bg-amber-600" },
]

export function ResolveClaimForm({ claimId, onResolved }: { claimId: string; onResolved?: () => void }) {
  const [verdict, setVerdict] = useState("VERIFIED")
  const [confidence, setConfidence] = useState(95)
  const [reasoning, setReasoning] = useState("")
  const [evidenceSummary, setEvidenceSummary] = useState("")
  const [result, setResult] = useState<string | null>(null)
  
  const { resolveClaim, loading, error, isConnected } = useClaimGuard()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    if (!isConnected) { setResult("Please connect your wallet first!"); return }
    try {
      const txResult = await resolveClaim(claimId, verdict, confidence, reasoning, evidenceSummary)
      setResult(`Claim resolved successfully! Transaction: ${txResult}`)
      onResolved?.()
    } catch (err: any) { setResult(`Error: ${err.message}`) }
  }

  return (
    <Card className="glass max-w-xl mx-auto">
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2"><Gavel className="w-5 h-5" /> Resolve Claim #{claimId}</CardTitle>
        <CardDescription>As the contract owner, submit the resolution verdict with confidence and reasoning.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium">Verdict</label>
            <div className="flex gap-2">
              {VERDICTS.map((v) => (
                <button key={v.value} type="button" onClick={() => setVerdict(v.value)}
                  className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${verdict === v.value ? v.color + " text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}>
                  {v.icon} {v.label}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Confidence: {confidence}%</label>
            <input type="range" min="0" max="100" value={confidence} onChange={(e) => setConfidence(Number(e.target.value))}
              className="w-full accent-violet-600" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Reasoning</label>
            <Textarea placeholder="Why this verdict?" value={reasoning} onChange={(e) => setReasoning(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Evidence Summary</label>
            <Textarea placeholder="Summary of evidence found..." value={evidenceSummary} onChange={(e) => setEvidenceSummary(e.target.value)} required />
          </div>
          <Button type="submit" variant="gradient" className="w-full gap-2" disabled={loading || !isConnected}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Gavel className="w-4 h-4" />} {loading ? "Resolving..." : "Submit Resolution"}
          </Button>
          {error && <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-400 text-sm">{error}</div>}
          {result && !error && <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-sm">{result}</div>}
        </form>
      </CardContent>
    </Card>
  )
}
