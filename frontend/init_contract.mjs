import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

const CLAIMGUARD_ADDRESS = "0x8A54cafd8C66911B73e0f90cF1816202b199e9e5";

async function init() {
  console.log("🔧 init() çağrılıyor...");
  try {
    const result = await client.writeContract({
      address: CLAIMGUARD_ADDRESS,
      functionName: "init",
      args: [],
    });
    console.log("✅ init başarılı:", result);
  } catch (err) {
    console.error("❌ init hatası:", err.message);
  }
}

init();
