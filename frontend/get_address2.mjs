import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.GENLAYER_PRIVATE_KEY.replace(/^0x/, '');
const account = privateKeyToAccount(`0x${privateKey}`);
const client = createClient({
  chain: testnetBradbury,
  account,
});

const txHash = "0xc096a26abd312e422daa5958be8df1425a178c6dd1bb974843e4d9dcd6c9bd5f";

async function getAddress() {
  const tx = await client.getTransaction({ hash: txHash });
  const bigIntReplacer = (key, value) => {
    if (typeof value === 'bigint') return value.toString();
    return value;
  };
  console.log("Transaction:", JSON.stringify(tx, bigIntReplacer, 2));
  if (tx.contractAddress) {
    console.log("✅ Contract Address:", tx.contractAddress);
  }
}

getAddress().catch(console.error);
