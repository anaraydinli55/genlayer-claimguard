import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { genlayer } from "@genlayer/js/chains";
import { http } from "wagmi";

export const config = getDefaultConfig({
  appName: "ClaimGuard",
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "YOUR_PROJECT_ID",
  chains: [genlayer],
  transports: {
    [genlayer.id]: http(process.env.NEXT_PUBLIC_GENLAYER_RPC_URL),
  },
  ssr: true,
});
