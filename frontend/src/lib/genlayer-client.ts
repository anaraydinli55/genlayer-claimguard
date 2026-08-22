import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

export const genlayerClient = createClient({
  chain: testnetBradbury,
  endpoint: "https://rpc-bradbury.genlayer.com",
});

export const CLAIMGUARD_ADDRESS = "0x7D7cF1Ea80740deBFF330C5384747904dC02B468" as `0x${string}`;
export const BOUNTYMANAGER_ADDRESS = "0xfB52BD1874BbD3113886cd948C3cE8116eA9fC75" as `0x${string}`;
