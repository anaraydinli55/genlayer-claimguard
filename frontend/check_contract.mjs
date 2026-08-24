import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

const CLAIMGUARD_ADDRESS = "0xC10aA2FF75EDe1bbCb7E2A4F90Fe603fb3c9b299";

async function check() {
  console.log("🔍 Checking contract state...");
  
  try {
    // 1. Get stats
    const stats = await client.readContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "getStats",
      args: [],
    });
    console.log("Stats:", JSON.stringify(stats, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
    
    // 2. Get claim count
    console.log("Claim count:", stats.total_claims);
    
    // 3. Try to get owner
    // Note: getOwner function doesn't exist, skip
    
  } catch (err) {
    console.error("Error:", err.message);
  }
}

check();
