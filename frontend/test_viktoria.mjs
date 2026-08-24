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

async function test() {
  console.log("🧪 Testing viktoria-az.store claim...");
  
  // 1. Create claim
  console.log("1. Creating claim...");
  const cid = await client.writeContract({
    address: CLAIMGUARD_ADDRESS,
    functionName: "createClaim",
    value: BigInt(0),
    args: ["https://viktoria-az.store", "Azerbaijani e-commerce website", "Verify legitimacy of viktoria-az.store e-commerce platform", "bounty_verification"],
  });
  console.log("   ✅ Claim created, tx:", cid);
  
  // 2. Get claim
  console.log("2. Getting claim...");
  const claim = await client.readContract({
    address: CLAIMGUARD_ADDRESS,
    functionName: "getClaim",
    args: [1],
  });
  console.log("   Claim:", JSON.stringify(claim, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
  
  // 3. Resolve
  console.log("3. Resolving (AI consensus - may take 30-60s)...");
  const status = await client.writeContract({
    address: CLAIMGUARD_ADDRESS,
    functionName: "resolveClaim",
    value: BigInt(0),
    args: ["1"],
  });
  console.log("   ✅ Status:", status);
  
  // 4. Get resolved
  const resolved = await client.readContract({
    address: CLAIMGUARD_ADDRESS,
    functionName: "getClaim",
    args: [1],
  });
  console.log("   Resolved:", JSON.stringify(resolved, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
}

test().catch(err => {
  console.error("❌ Error:", err.message);
  if (err.message.includes("rate limit")) {
    console.log("   ⏳ Bradbury is at capacity. Try again in a few minutes.");
  }
});
