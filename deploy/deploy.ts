#!/usr/bin/env ts-node
/**
 * ClaimGuard Deployment Script
 * 
 * Usage:
 *   npx ts-node deploy.ts              # Deploy to localnet
 *   npx ts-node deploy.ts --testnet    # Deploy to testnet
 * 
 * Requires: @genlayer/cli (install when available)
 */

async function deploy() {
  const isTestnet = process.argv.includes("--testnet");
  const network = isTestnet ? "testnet_bradbury" : "localnet";

  console.log(`🚀 Deploying ClaimGuard to ${network}...`);

  // TODO: Replace with actual GenLayer SDK when available
  // const { getProvider, getAccountFromEnvOrDefault } = require("@genlayer/cli");
  // const provider = getProvider();
  // const account = getAccountFromEnvOrDefault();
  // 
  // const deployResult = await provider.deployContract(account, "contracts/ClaimGuard.py", []);
  // console.log(`✅ Deployed at: ${deployResult.contractAddress}`);

  console.log("⚠️  GenLayer CLI not yet installed.");
  console.log("   Install with: npm install -g @genlayer/cli");
  console.log("   Then run this script again.");
  console.log("\n📋 Manual deploy steps:");
  console.log("   1. Go to studio.genlayer.com");
  console.log("   2. Create new project");
  console.log("   3. Paste contracts/ClaimGuard.py");
  console.log("   4. Click Deploy");
  console.log("   5. Run init()");
}

deploy().catch(console.error);
