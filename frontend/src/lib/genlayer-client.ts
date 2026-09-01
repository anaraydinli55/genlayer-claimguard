import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

export const genlayerClient = createClient({
  chain: testnetBradbury,
  endpoint: "https://rpc-bradbury.genlayer.com",
});

// ClaimGuard v14 - deployed 2026-09-01
export const CLAIMGUARD_ADDRESS = "0x9E8CA759Fd17aA6b0af88c90734FE5dB636c82c6" as `0x${string}`;
export const BOUNTYMANAGER_ADDRESS = "0xfB52BD1874BbD3113886cd948C3cE8116eA9fC75" as `0x${string}`;
