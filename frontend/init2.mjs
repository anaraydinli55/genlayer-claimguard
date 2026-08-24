import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

const CLAIMGUARD_ADDRESS = "0x35426b0535860491b35aBFA2bbCA757bC742Ee0f";

async function init() {
  console.log("🚀 Calling init() on new contract...");
  try {
    const result = await client.writeContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "init",
      value: BigInt(0),
      args: [],
    });
    console.log("✅ Init successful:", result);
  } catch (err) {
    console.log("Note:", err.message);
  }
}

init();
