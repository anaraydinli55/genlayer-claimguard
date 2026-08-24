import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";
import { readFileSync, writeFileSync } from "fs";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({ chain: testnetBradbury, account });

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function deployWithRetry(code, maxRetries = 10) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      console.log(`🚀 Deploy ${i+1}/${maxRetries}...`);
      return await client.deployContract({ code, args: [], leaderOnly: false });
    } catch (err) {
      if (err.code === -32005) { await sleep(err.cause?.data?.retryAfterMs || 1500); }
      else { throw err; }
    }
  }
}

async function callWithRetry(addr, fn, args, maxRetries = 10) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      console.log(`🔧 ${fn} ${i+1}/${maxRetries}...`);
      return await client.writeContract({ address: addr, functionName: fn, args, leaderOnly: false });
    } catch (err) {
      if (err.code === -32005) { await sleep(err.cause?.data?.retryAfterMs || 1500); }
      else { throw err; }
    }
  }
}

async function main() {
  const code = readFileSync("../contracts/ClaimGuard.py", "utf-8");
  const tx = await deployWithRetry(code);
  console.log("✅ Deploy:", tx);
  
  const receipt = await client.waitForTransactionReceipt({ hash: tx, status: "ACCEPTED", retries: 100, interval: 10000 });
  const addr = receipt.txDataDecoded?.contractAddress;
  console.log("✅ Adres:", addr);
  
  await sleep(20000);
  
  console.log("\n🔧 init() cagriliyor...");
  const initTx = await callWithRetry(addr, "init", []);
  console.log("✅ Init tx:", initTx);
  
  await client.waitForTransactionReceipt({ hash: initTx, status: "ACCEPTED", retries: 50, interval: 5000 });
  console.log("✅ Init tamamlandi");
  
  await sleep(20000);
  
  const owner = await client.readContract({ address: addr, functionName: "getOwner", args: [] });
  console.log("✅ Owner:", owner);
  
  let mjs = readFileSync("check_new.mjs", "utf-8");
  mjs = mjs.replace(/const CLAIMGUARD_ADDRESS = "0x[a-fA-F0-9]+";/, `const CLAIMGUARD_ADDRESS = "${addr}";`);
  writeFileSync("check_new.mjs", mjs);
  console.log("✅ check_new.mjs guncellendi");
}
main().catch(e => { console.error("❌", e.message); process.exit(1); });
