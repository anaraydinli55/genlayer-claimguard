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

  const getClient = useCallback(() => {
    if (!walletClient) throw new Error("No wallet connected. Please connect MetaMask.")
    return createClient({
      chain: testnetBradbury,
      endpoint: "https://rpc-bradbury.genlayer.com",
      account: walletClient.account,
    })
  }, [walletClient])

  const createClaim = useCallback(async (
    url: string,
    expectedContent: string,
    description: string,
    category: string = "custom"
  ) => {
    if (!isConnected) throw new Error("Wallet not connected")
    setLoading(true)
    setError(null)
    try {
      const client = getClient()
      const result = await client.writeContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "createClaim",
        value: BigInt(0),
        args: [url, expectedContent, description, category],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [isConnected, getClient])

  const resolveClaim = useCallback(async (claimId: string) => {
    if (!isConnected) throw new Error("Wallet not connected")
    setLoading(true)
    setError(null)
    try {
      const client = getClient()
      const result = await client.writeContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "resolveClaim",
        value: BigInt(0),
        args: [claimId],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [isConnected, getClient])

  const appealClaim = useCallback(async (claimId: string, newEvidenceUrl: string = "") => {
    if (!isConnected) throw new Error("Wallet not connected")
    setLoading(true)
    setError(null)
    try {
      const client = getClient()
      const result = await client.writeContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "appealClaim",
        value: BigInt(0),
        args: [claimId, newEvidenceUrl],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [isConnected, getClient])

  const getClaim = useCallback(async (claimId: number) => {
    try {
      const client = getClient()
      const result = await client.readContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "getClaim",
        args: [claimId],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [getClient])

  const getAllClaims = useCallback(async () => {
    try {
      const client = getClient()
      const result = await client.readContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "getAllClaims",
        args: [],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [getClient])

  const getStats = useCallback(async () => {
    try {
      const client = getClient()
      const result = await client.readContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "getStats",
        args: [],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [getClient])

  return { createClaim, resolveClaim, appealClaim, getClaim, getAllClaims, getStats, loading, error, isConnected, address }
}
