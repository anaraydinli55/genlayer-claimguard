import { createClient } from "@genlayer/js";
import { genlayer } from "@genlayer/js/chains";

export const genlayerClient = createClient({
  chain: genlayer,
  endpoint: process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || "http://localhost:4000/api",
});

export const CLAIMGUARD_ADDRESS = process.env.NEXT_PUBLIC_CLAIMGUARD_ADDRESS || "";
export const BOUNTYMANAGER_ADDRESS = process.env.NEXT_PUBLIC_BOUNTYMANAGER_ADDRESS || "";
