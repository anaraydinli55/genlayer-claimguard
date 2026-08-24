import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";
import { readFileSync } from "fs";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

async function main() {
  const txHash = "0x7b4b2f9f5f8b3ba8fb75a44ead89b9efb0caef6d9fd034628eea17857f7979ab";
  
  console.log("🔍 Receipt sorgulaniyor...");
  const receipt = await client.waitForTransactionReceipt({
    hash: txHash,
    status: "ACCEPTED",
    retries: 50,
    interval: 5000,
  });
  
  console.log("📦 Receipt tam yapisi:");
  console.log(JSON.stringify(receipt, (k,v) => typeof v === 'bigint' ? v.toString() : v, 2));
  
  console.log("\n🔍 Olası adres alanlari:");
  console.log("receipt.contractAddress:", receipt.contractAddress);
  console.log("receipt.contract_address:", receipt.contract_address);
  console.log("receipt.data?.contract_address:", receipt.data?.contract_address);
  console.log("receipt.data?.contractAddress:", receipt.data?.contractAddress);
  console.log("receipt.to:", receipt.to);
  console.log("receipt.contractAddress:", receipt.contractAddress);
}

main().catch(console.error);
