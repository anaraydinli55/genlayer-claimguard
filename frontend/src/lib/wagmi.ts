import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { http, createConfig } from "wagmi";
import { metaMask, walletConnect, injected } from "wagmi/connectors";
import { defineChain } from "viem";

export const genlayer = defineChain({
  id: 493,
  name: "GenLayer Bradbury",
  nativeCurrency: { name: "GEN", symbol: "GEN", decimals: 18 },
  rpcUrls: {
    default: { http: ["https://rpc-bradbury.genlayer.com"] },
  },
});

export const config = createConfig({
  chains: [genlayer],
  connectors: [injected(), metaMask(), walletConnect({ projectId: "demo" })],
  transports: {
    [genlayer.id]: http("https://rpc-bradbury.genlayer.com"),
  },
});
