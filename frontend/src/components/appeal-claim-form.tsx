"use client"

import { useState } from "react"
import { RotateCcw, Link, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useClaimGuard } from "@/hooks/use-claimguard"

export function AppealClaimForm({ claimId, onAppealed }: { claimId: string; onAppealed?: () => void }) {
  const [newUrl, setNewUrl] = useState("")
  const [result, setResult] = useState<string | null>(null)
  
  const { appealClaim, loading, error, isConnected } = useClaimGuard()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    if (!isConnected) { setResult("Please connect your wallet first!"); return }
    try {
      const txResult = await appealClaim(claimId, newUrl)
      setResult(`Appeal submitted successfully! Transaction: ${txResult}`)
      setNewUrl("")
      onAppealed?.()
    } catch (err: any) { setResult(`Error: ${err.message}`) }
  }

  return (
    <Card className="glass max-w-xl mx-auto">
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2"><RotateCcw className="w-5 h-5" /> Appeal Claim #{claimId}</CardTitle>
        <CardDescription>Submit new evidence URL to re-evaluate this claim. Max 3 appeals.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2"><Link className="w-4 h-4" /> New Evidence URL</label>
            <Input placeholder="https://new-evidence.com" value={newUrl} onChange={(e) => setNewUrl(e.target.value)} required />
          </div>
          <Button type="submit" variant="outline" className="w-full gap-2" disabled={loading || !isConnected}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} {loading ? "Submitting..." : "Submit Appeal"}
          </Button>
          {error && <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-400 text-sm">{error}</div>}
          {result && !error && <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-sm">{result}</div>}
        </form>
      </CardContent>
    </Card>
  )
}
