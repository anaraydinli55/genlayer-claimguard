import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

export const genlayerClient = createClient({
  chain: testnetBradbury,
  endpoint: "https://rpc-bradbury.genlayer.com",
});

export const CLAIMGUARD_ADDRESS = "0xC10aA2FF75EDe1bbCb7E2A4F90Fe603fb3c9b299" as `0x${string}`;
export const BOUNTYMANAGER_ADDRESS = "0xfB52BD1874BbD3113886cd948C3cE8116eA9fC75" as `0x${string}`;
