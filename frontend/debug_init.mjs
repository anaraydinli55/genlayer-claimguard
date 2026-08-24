import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

async function main() {
  const initTx = "0xdc4a8751c2316533990e12d2934d572ab0cfcff48ee3f617ab27c18a9579907e";
  console.log("🔍 init() tx receipt sorgulaniyor...");
  const receipt = await client.waitForTransactionReceipt({
    hash: initTx,
    status: "ACCEPTED",
    retries: 50,
    interval: 5000,
  });
  console.log("📦 Receipt:");
  console.log(JSON.stringify(receipt, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
}

main().catch(console.error);
