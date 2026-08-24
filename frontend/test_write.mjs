import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({ chain: testnetBradbury, account });

const ADDR = "0x44B90f3A1847936721C665bdD317cedcaaFBa139";

async function main() {
  console.log("🔧 createClaim testi...");
  try {
    const tx = await client.writeContract({
      address: ADDR,
      functionName: "createClaim",
      args: ["https://example.com", "test content", "test desc", "prediction_market"],
      leaderOnly: false,
    });
    console.log("✅ createClaim tx:", tx);
    const receipt = await client.waitForTransactionReceipt({ hash: tx, status: "ACCEPTED", retries: 50, interval: 5000 });
    console.log("✅ Receipt:", receipt.txExecutionResultName);
    const stats = await client.readContract({ address: ADDR, functionName: "getStats", args: [] });
    console.log("📊 Stats:", JSON.stringify(stats, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
  } catch (err) {
    console.error("❌ Hata:", err.message);
  }
}
main();
