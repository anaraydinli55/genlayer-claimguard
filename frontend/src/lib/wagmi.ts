import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { http, createConfig } from "wagmi";
import { metaMask, walletConnect, injected } from "wagmi/connectors";
import { defineChain } from "viem";

export const genlayer = defineChain({
  id: 137,
  name: "GenLayer",
  nativeCurrency: { name: "GEN", symbol: "GEN", decimals: 18 },
  rpcUrls: {
    default: { http: ["http://127.0.0.1:4000/api"] },
  },
});

export const config = createConfig({
  chains: [genlayer],
  connectors: [injected(), metaMask(), walletConnect({ projectId: "demo" })],
  transports: {
    [genlayer.id]: http("http://127.0.0.1:4000/api"),
  },
});
