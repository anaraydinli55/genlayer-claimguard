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
    return createClient({
      chain: testnetBradbury,
      endpoint: "https://rpc-bradbury.genlayer.com",
      account: walletClient.account as any,
    })
  }, [walletClient])

  const createClaim = useCallback(async (url: string, expectedContent: string, description: string, category: string = "custom") => {
    if (!isConnected) throw new Error("Wallet not connected")
    setLoading(true)
    setError(null)
    try {
      const client = getWriteClient()
      return await client.writeContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "createClaim",
        args: [url, expectedContent, description, category],
        value: BigInt(0),
      })
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [isConnected, getWriteClient])

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

  return { createClaim, getAllClaims, getStats, loading, error, isConnected, address }
}
