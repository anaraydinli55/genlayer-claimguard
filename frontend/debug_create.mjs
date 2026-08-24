import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({ chain: testnetBradbury, account });

const CLAIMGUARD_ADDRESS = "0xFcBc0BA201f64965c40b8B0965FdaE3C9e67344C";

async function main() {
  const owner = await client.readContract({ address: CLAIMGUARD_ADDRESS, functionName: "getOwner", args: [] });
  console.log("Owner (before createClaim):", JSON.stringify(owner));

  const txHash = await client.writeContract({
    address: CLAIMGUARD_ADDRESS,
    functionName: "createClaim",
    args: ["https://example.com", "test content", "test desc", "custom"],
    leaderOnly: false,
  });
  console.log("tx:", txHash);

  const receipt = await client.waitForTransactionReceipt({
    hash: txHash,
    status: "ACCEPTED",
    retries: 50,
    interval: 5000,
  });

  console.log("FULL RECEIPT:", JSON.stringify(receipt, (k, v) => typeof v === 'bigint' ? v.toString() : v, 2));
}

main().catch(err => console.error("CATCH ERROR:", err));
