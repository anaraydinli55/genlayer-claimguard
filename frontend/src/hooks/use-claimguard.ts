"use client"

import { useState, useCallback } from "react"
import { useAccount, useWalletClient } from "wagmi"
import { createClient } from "genlayer-js"
import { testnetBradbury } from "genlayer-js/chains"
import { CLAIMGUARD_ADDRESS } from "@/lib/genlayer-client"

export function useClaimGuard() {
  const { address, isConnected } = useAccount()
  const { data: walletClient } = useWalletClient()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getReadClient = useCallback(() => {
    return createClient({
      chain: testnetBradbury,
      endpoint: "https://rpc-bradbury.genlayer.com",
    })
  }, [])

  const getWriteClient = useCallback(() => {
    if (!walletClient?.account?.address) {
      throw new Error("No wallet connected.")
    }
    const ethProvider = (window as any).ethereum
    if (!ethProvider) {
      throw new Error("No Ethereum provider found.")
    }
    return createClient({
      chain: testnetBradbury,
      endpoint: "https://rpc-bradbury.genlayer.com",
      account: walletClient.account.address,
      provider: ethProvider,
    })
  }, [walletClient])

  const createClaim = useCallback(async (url: string, expectedContent: string, description: string, category: string = "custom") => {
    if (!isConnected) throw new Error("Wallet not connected")
    setLoading(true); setError(null)
    try {
      const client = getWriteClient()
      return await client.writeContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "createClaim",
        args: [url, expectedContent, description, category],
        value: BigInt(0),
      })
    } catch (err: any) { setError(err.message); throw err }
    finally { setLoading(false) }
  }, [isConnected, getWriteClient])

  const resolveClaim = useCallback(async (claimId: string, verdict: string, confidencePct: number, reasoning: string, evidenceSummary: string) => {
    if (!isConnected) throw new Error("Wallet not connected")
    setLoading(true); setError(null)
    try {
      const client = getWriteClient()
      return await client.writeContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "resolveClaim",
        args: [claimId, verdict, String(confidencePct), reasoning, evidenceSummary],
        value: BigInt(0),
      })
    } catch (err: any) { setError(err.message); throw err }
    finally { setLoading(false) }
  }, [isConnected, getWriteClient])

  const appealClaim = useCallback(async (claimId: string, newEvidenceUrl: string) => {
    if (!isConnected) throw new Error("Wallet not connected")
    setLoading(true); setError(null)
    try {
      const client = getWriteClient()
      return await client.writeContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "appealClaim",
        args: [claimId, newEvidenceUrl],
        value: BigInt(0),
      })
    } catch (err: any) { setError(err.message); throw err }
    finally { setLoading(false) }
  }, [isConnected, getWriteClient])

  const getClaim = useCallback(async (claimId: string) => {
    const client = getReadClient()
    return await client.readContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "getClaim",
      args: [claimId],
    })
  }, [getReadClient])

  const getAllClaims = useCallback(async () => {
    const client = getReadClient()
    return await client.readContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "getAllClaims",
      args: [],
    })
  }, [getReadClient])

  const getStats = useCallback(async () => {
    const client = getReadClient()
    return await client.readContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "getStats",
      args: [],
    })
  }, [getReadClient])

  const getOwner = useCallback(async () => {
    const client = getReadClient()
    return await client.readContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "getOwner",
      args: [],
    })
  }, [getReadClient])

  return { createClaim, resolveClaim, appealClaim, getClaim, getAllClaims, getStats, getOwner, loading, error, isConnected, address }
}
