import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";
import { readFileSync } from "fs";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({ chain: testnetBradbury, account });

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const code = readFileSync("../contracts/SimpleGuard.py", "utf-8");
  const tx = await client.deployContract({ code, args: [], leaderOnly: false });
  const receipt = await client.waitForTransactionReceipt({ hash: tx, status: "ACCEPTED", retries: 50, interval: 5000 });
  const addr = receipt.txDataDecoded?.contractAddress;
  console.log("✅ Adres:", addr);
  await sleep(30000);
  
  console.log("🔍 getMessage (__init__ sonrasi):");
  const msg = await client.readContract({ address: addr, functionName: "getMessage", args: [] });
  console.log("   Result:", msg);
  
  console.log("🔧 setMessage('test'):");
  const setTx = await client.writeContract({ address: addr, functionName: "setMessage", args: ["test"], leaderOnly: false });
  await client.waitForTransactionReceipt({ hash: setTx, status: "ACCEPTED", retries: 50, interval: 5000 });
  console.log("   Tx:", setTx);
  await sleep(30000);
  
  console.log("🔍 getMessage (setMessage sonrasi):");
  const msg2 = await client.readContract({ address: addr, functionName: "getMessage", args: [] });
  console.log("   Result:", msg2);
  
  console.log("🔧 init():");
  const initTx = await client.writeContract({ address: addr, functionName: "init", args: [], leaderOnly: false });
  await client.waitForTransactionReceipt({ hash: initTx, status: "ACCEPTED", retries: 50, interval: 5000 });
  console.log("   Tx:", initTx);
  await sleep(30000);
  
  console.log("🔍 getOwner (init sonrasi):");
  const owner = await client.readContract({ address: addr, functionName: "getOwner", args: [] });
  console.log("   Result:", owner);
}
main().catch(e => console.error("❌", e.message));
