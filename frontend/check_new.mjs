import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

const CLAIMGUARD_ADDRESS = "0x1FDd7CA3dF62932D86291aE5A040440626672338";

async function check() {
  console.log("🔍 Checking new contract...");

  try {
    const owner = await client.readContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "getOwner",
      args: [],
    });
    console.log("✅ Owner:", owner);
  } catch (err) {
    console.error("❌ getOwner failed:", err.message);
  }

  try {
    const stats = await client.readContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "getStats",
      args: [],
    });
    console.log("✅ Stats:", JSON.stringify(stats, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
  } catch (err) {
    console.error("❌ getStats failed:", err.message);
  }

  try {
    const resolvers = await client.readContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "getResolvers",
      args: [],
    });
    console.log("✅ Resolvers:", JSON.stringify(resolvers, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
  } catch (err) {
    console.error("❌ getResolvers failed:", err.message);
  }
}

check();
