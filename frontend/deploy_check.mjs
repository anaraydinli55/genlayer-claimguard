import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";
import { readFileSync, writeFileSync } from "fs";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function deployWithRetry(code, maxRetries = 10) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      console.log(`🚀 Deneme ${i + 1}/${maxRetries}...`);
      const txHash = await client.deployContract({ code, args: [], leaderOnly: false });
      return txHash;
    } catch (err) {
      if (err.code === -32005 || err.message?.includes("rate limit")) {
        const wait = err.cause?.data?.retryAfterMs || 1500;
        console.log(`⏳ Rate limit, ${wait}ms bekleniyor...`);
        await sleep(wait + 200);
      } else {
        throw err;
      }
    }
  }
  throw new Error("Max retry asildi");
}

async function main() {
  const contractCode = readFileSync("../contracts/ClaimGuard.py", "utf-8");
  
  const txHash = await deployWithRetry(contractCode);
  console.log("✅ Tx gonderildi:", txHash);
  
  console.log("⏳ Onay bekleniyor...");
  const receipt = await client.waitForTransactionReceipt({
    hash: txHash,
    status: "ACCEPTED",
    retries: 50,
    interval: 5000,
  });
  
  const addr = receipt.data?.contract_address;
  if (!addr) throw new Error("Adres bulunamadi");
  console.log("✅ Yeni kontrat:", addr);
  
  console.log("\n🔍 Kontrol ediliyor...");
  const owner = await client.readContract({ address: addr, functionName: "getOwner", args: [] });
  console.log("✅ Owner:", owner);
  
  const stats = await client.readContract({ address: addr, functionName: "getStats", args: [] });
  console.log("✅ Stats:", JSON.stringify(stats, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
  
  const resolvers = await client.readContract({ address: addr, functionName: "getResolvers", args: [] });
  console.log("✅ Resolvers:", JSON.stringify(resolvers, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
  
  let mjs = readFileSync("check_new.mjs", "utf-8");
  mjs = mjs.replace(/const CLAIMGUARD_ADDRESS = "0x[a-fA-F0-9]+";/, `const CLAIMGUARD_ADDRESS = "${addr}";`);
  writeFileSync("check_new.mjs", mjs);
  console.log("\n✅ check_new.mjs guncellendi");
}

main().catch(err => {
  console.error("❌ Hata:", err.message);
  process.exit(1);
});
