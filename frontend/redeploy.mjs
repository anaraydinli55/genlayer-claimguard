import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";
import fs from "node:fs";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

async function deploy() {
  const code = fs.readFileSync("../contracts/ClaimGuard.py", "utf-8");
  console.log("🚀 Redeploying ClaimGuard...");
  const contractAddress = await client.deployContract({ code, args: [] });
  console.log("✅ New address:", contractAddress);
}

deploy().catch(console.error);
