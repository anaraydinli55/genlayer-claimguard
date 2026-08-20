import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatAddress(addr: string): string {
  if (!addr || addr.length < 10) return addr
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`
}

export function formatDate(timestamp: number): string {
  if (!timestamp) return "—"
  return new Date(timestamp * 1000).toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  })
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "verified": return "status-verified"
    case "rejected": return "status-rejected"
    case "pending": return "status-pending"
    case "inconclusive": return "status-inconclusive"
    default: return "status-pending"
  }
}

export function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    prediction_market: "Prediction Market",
    bounty_verification: "Bounty Verification",
    content_moderation: "Content Moderation",
    identity_verification: "Identity Verification",
    fact_check: "Fact Check",
    custom: "Custom",
  }
  return labels[category] || category
}
