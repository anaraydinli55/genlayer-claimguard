"use client"

import * as React from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { WagmiProvider } from "wagmi"
import { RainbowKitProvider, darkTheme, lightTheme } from "@rainbow-me/rainbowkit"
import { config } from "@/lib/wagmi"
import { useTheme } from "next-themes"

const queryClient = new QueryClient()

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const { resolvedTheme } = useTheme()
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider theme={resolvedTheme === "dark" ? darkTheme() : lightTheme()}>
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  )
}
