import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

export const genlayerClient = createClient({
  chain: testnetBradbury,
  endpoint: process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || "http://localhost:4000/api",
});

export const CLAIMGUARD_ADDRESS = (process.env.NEXT_PUBLIC_CLAIMGUARD_ADDRESS || "") as `0x${string}`;
export const BOUNTYMANAGER_ADDRESS = (process.env.NEXT_PUBLIC_BOUNTYMANAGER_ADDRESS || "") as `0x${string}`;
