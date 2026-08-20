"use client"

import { useState, useCallback } from "react"
import { genlayerClient, CLAIMGUARD_ADDRESS } from "@/lib/genlayer-client"

export function useClaimGuard() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createClaim = useCallback(async (
    url: string,
    expectedContent: string,
    description: string,
    category: string = "custom"
  ) => {
    setLoading(true)
    setError(null)
    try {
      const result = await genlayerClient.writeContract({
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
  }, [])

  const getClaim = useCallback(async (claimId: number) => {
    try {
      const result = await genlayerClient.readContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "getClaim",
        args: [claimId],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const getAllClaims = useCallback(async () => {
    try {
      const result = await genlayerClient.readContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "getAllClaims",
        args: [],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  const getStats = useCallback(async () => {
    try {
      const result = await genlayerClient.readContract({
        address: CLAIMGUARD_ADDRESS,
        functionName: "getStats",
        args: [],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  return { createClaim, getClaim, getAllClaims, getStats, loading, error }
}
