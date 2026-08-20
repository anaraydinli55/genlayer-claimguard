"use client"

import { useState, useCallback } from "react"
import { genlayerClient, BOUNTYMANAGER_ADDRESS } from "@/lib/genlayer-client"

export function useBountyManager() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createBounty = useCallback(async (
    title: string,
    description: string,
    rewardAmount: number,
    evidenceUrl: string,
    expectedEvidence: string
  ) => {
    setLoading(true)
    setError(null)
    try {
      const result = await genlayerClient.writeContract({
        address: BOUNTYMANAGER_ADDRESS,
        functionName: "createBounty",
        args: [title, description, rewardAmount, evidenceUrl, expectedEvidence],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const submitWork = useCallback(async (bountyId: number, proofUrl: string) => {
    setLoading(true)
    setError(null)
    try {
      const result = await genlayerClient.writeContract({
        address: BOUNTYMANAGER_ADDRESS,
        functionName: "submitWork",
        args: [bountyId, proofUrl],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const getOpenBounties = useCallback(async () => {
    try {
      const result = await genlayerClient.readContract({
        address: BOUNTYMANAGER_ADDRESS,
        functionName: "getOpenBounties",
        args: [],
      })
      return result
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  return { createBounty, submitWork, getOpenBounties, loading, error }
}
