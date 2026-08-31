import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

export const genlayerClient = createClient({
  chain: testnetBradbury,
  endpoint: "https://rpc-bradbury.genlayer.com",
});

export const CLAIMGUARD_ADDRESS = "0x42f58D65B39F05d3cD95B9Fb8a021d7EC6998985" as `0x${string}`;
export const BOUNTYMANAGER_ADDRESS = "0xfB52BD1874BbD3113886cd948C3cE8116eA9fC75" as `0x${string}`;
