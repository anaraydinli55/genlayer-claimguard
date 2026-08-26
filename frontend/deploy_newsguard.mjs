import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";
import { readFileSync } from "fs";

const pk = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const acc = privateKeyToAccount('0x' + pk);
const client = createClient({ chain: testnetBradbury, account: acc });

async function main() {
  const code = readFileSync("../../genlayer-newsguard/NewsGuard.py", "utf-8");
  console.log("🚀 Deploying NewsGuard...");
  const tx = await client.deployContract({ code, args: [], leaderOnly: false });
  console.log("✅ Tx:", tx);
  const receipt = await client.waitForTransactionReceipt({ hash: tx, status: "ACCEPTED", retries: 50, interval: 5000 });
  const addr = receipt.txDataDecoded?.contractAddress;
  console.log("✅ Address:", addr);
  console.log("🔗 Explorer: https://explorer.genlayer.com/address/" + addr);
}
main().catch(e => console.error("❌", e.message));
