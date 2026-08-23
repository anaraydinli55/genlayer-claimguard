"use client"

import { useState } from "react"
import { Send, Link, FileText, Tag, AlertCircle, Wallet } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useClaimGuard } from "@/hooks/use-claimguard"
import { ConnectButton } from "@rainbow-me/rainbowkit"

const CATEGORIES = [
  { value: "prediction_market", label: "Prediction Market" },
  { value: "bounty_verification", label: "Bounty Verification" },
  { value: "content_moderation", label: "Content Moderation" },
  { value: "identity_verification", label: "Identity Verification" },
  { value: "fact_check", label: "Fact Check" },
  { value: "custom", label: "Custom" },
]

export function CreateClaimForm() {
  const [url, setUrl] = useState("")
  const [expected, setExpected] = useState("")
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState("custom")
  const [result, setResult] = useState<string | null>(null)
  
  const { createClaim, loading, error, isConnected } = useClaimGuard()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    
    if (!isConnected) {
      setResult("Please connect your wallet first!")
      return
    }
    
    try {
      const txResult = await createClaim(url, expected, description, category)
      setResult(`Claim submitted successfully! Transaction: ${txResult}`)
      setUrl(""); setExpected(""); setDescription("")
    } catch (err: any) {
      setResult(`Error: ${err.message}`)
    }
  }

  return (
    <Card className="glass max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">Submit a New Claim</CardTitle>
        <CardDescription>Provide a URL and expected content. Validators will fetch evidence and run AI consensus.</CardDescription>
      </CardHeader>
      <CardContent>
        {!isConnected && (
          <div className="mb-6 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 text-sm flex items-center justify-between">
            <span className="flex items-center gap-2"><Wallet className="w-4 h-4" /> Connect wallet to submit claims</span>
            <ConnectButton />
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2"><Link className="w-4 h-4" /> Evidence URL</label>
            <Input placeholder="https://example.com/article" value={url} onChange={(e) => setUrl(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2"><FileText className="w-4 h-4" /> Expected Content</label>
            <Textarea placeholder="What should validators look for?" value={expected} onChange={(e) => setExpected(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2"><AlertCircle className="w-4 h-4" /> Description</label>
            <Textarea placeholder="Detailed description..." value={description} onChange={(e) => setDescription(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2"><Tag className="w-4 h-4" /> Category</label>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map((cat) => (
                <button key={cat.value} type="button" onClick={() => setCategory(cat.value)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${category === cat.value ? "bg-violet-600 text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}>
                  {cat.label}
                </button>
              ))}
            </div>
          </div>
          <Button type="submit" variant="gradient" className="w-full gap-2" disabled={loading || !isConnected}>
            <Send className="w-4 h-4" /> {loading ? "Submitting..." : "Submit Claim"}
          </Button>
          {error && (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-400 text-sm">{error}</div>
          )}
          {result && !error && (
            <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-sm">{result}</div>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
