import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const pk = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const acc = privateKeyToAccount('0x' + pk);
const client = createClient({ chain: testnetBradbury, account: acc });

const ADDR = "0x324044aB4604761Fa70D1C9CaB9E80f478a934F0";

async function main() {
  console.log("🔧 init()...");
  const initTx = await client.writeContract({ address: ADDR, functionName: "init", args: [], leaderOnly: false });
  await client.waitForTransactionReceipt({ hash: initTx, status: "ACCEPTED", retries: 50, interval: 5000 });
  console.log("✅ init tamam");

  console.log("🔧 registerAsset ETH...");
  const regTx = await client.writeContract({
    address: ADDR,
    functionName: "registerAsset",
    args: ["ETH", "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"],
    leaderOnly: false
  });
  await client.waitForTransactionReceipt({ hash: regTx, status: "ACCEPTED", retries: 50, interval: 5000 });
  console.log("✅ ETH registered");

  console.log("🔧 updatePrice ETH...");
  const updTx = await client.writeContract({ address: ADDR, functionName: "updatePrice", args: ["ETH"], leaderOnly: false });
  await client.waitForTransactionReceipt({ hash: updTx, status: "ACCEPTED", retries: 50, interval: 5000 });
  console.log("✅ ETH price updated");

  console.log("🔍 getPrice ETH...");
  const price = await client.readContract({ address: ADDR, functionName: "getPrice", args: ["ETH"] });
  console.log("✅ Price:", JSON.stringify(price, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
}
main().catch(e => console.error("❌", e.message));
