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
      throw new Error("No wallet connected. Please connect MetaMask.")
    }
    return createClient({
      chain: testnetBradbury,
      endpoint: "https://rpc-bradbury.genlayer.com",
      account: { address: walletClient.account.address },
    })
  }, [walletClient])

  const createClaim = useCallback(async (url, expectedContent, description, category = "custom") => {
    if (!isConnected) throw new Error("Wallet not connected")
    setLoading(true)
    setError(null)
    try {
      const client = getWriteClient()
      return await client.writeContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "createClaim",
        args: [url, expectedContent, description, category],
      })
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [isConnected, getWriteClient])

  const getClaim = useCallback(async (claimId) => {
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

  return { createClaim, getClaim, getAllClaims, getStats, loading, error, isConnected, address }
}
