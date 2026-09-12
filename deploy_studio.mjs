import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";
import fs from "fs";

const rawKey = process.env.GENLAYER_PRIVATE_KEY || process.env.PRIVATE_KEY;
if (!rawKey) {
  console.error("❌ PRIVATE_KEY bulunamadı!");
  process.exit(1);
}

const privateKey = rawKey.startsWith("0x") ? rawKey : "0x" + rawKey;
const account = privateKeyToAccount(privateKey);

const client = createClient({
  chain: studionet,
  account,
});

console.log("🔑 Deployer:", account.address);
console.log("⛓️  Ağ:     ", studionet.name);

async function main() {
  const contractCode = fs.readFileSync("contracts/ClaimGuard.py", "utf8");

  console.log("\n🚀 ClaimGuard kontratı deploy ediliyor...");
  const txHash = await client.deployContract({
    code: contractCode,
    args: [],
    leaderOnly: false,
  });

  console.log("⏳ Deploy tx gönderildi:", txHash);
  console.log("⏳ Onay (finalized) bekleniyor...");

  const receipt = await client.waitForTransactionReceipt({
    hash: txHash,
    status: "FINALIZED"
  });

  const contractAddress = receipt.contract_address || receipt.to_address || receipt.recipient;
  console.log("\n✅ KONTRAT BAŞARIYLA DAĞITILDI!");
  console.log("📍 Kontrat Adresi:", contractAddress);

  console.log("\n🔧 init() çağrılıyor...");
  const initTx = await client.writeContract({
    address: contractAddress,
    functionName: "init",
    args: [],
  });

  console.log("⏳ init tx:", initTx);
  await client.waitForTransactionReceipt({ hash: initTx, status: "FINALIZED" });
  console.log("✅ init() tamamlandı!");

  console.log("\n🔍 getStats() test ediliyor...");
  const stats = await client.readContract({
    address: contractAddress,
    functionName: "getStats",
    args: []
  });
  console.log("✅ getStats() sonucu:", stats);

  console.log("\n=======================================================");
  console.log("🔗 RESMİ EXPLORER KANIT LİNKİNİZ:");
  console.log(`https://explorer-studio.genlayer.com/address/${contractAddress}`);
  console.log("=======================================================\n");
}

main().catch(err => {
  console.error("❌ Hata:", err);
  process.exit(1);
});
