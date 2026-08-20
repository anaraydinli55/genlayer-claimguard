"use client"

import { useState } from "react"
import { Send, Link, FileText, Tag, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

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
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    await new Promise((r) => setTimeout(r, 1500))
    setResult(`Claim submitted! ID: #${Math.floor(Math.random() * 1000) + 1}`)
    setSubmitting(false)
    setUrl(""); setExpected(""); setDescription("")
  }

  return (
    <Card className="glass max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">Submit a New Claim</CardTitle>
        <CardDescription>Provide a URL and expected content. Validators will fetch evidence and run AI consensus.</CardDescription>
      </CardHeader>
      <CardContent>
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
          <Button type="submit" variant="gradient" className="w-full gap-2" disabled={submitting}>
            <Send className="w-4 h-4" /> {submitting ? "Submitting..." : "Submit Claim"}
          </Button>
          {result && (
            <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-sm">{result}</div>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
