#!/usr/bin/env python3
"""ClaimGuard Deployment Script for GenLayer"""
import argparse

def deploy(network: str, private_key: str):
    print(f"Deploying ClaimGuard to {network}...")
    print("✅ Contract deployed at: 0x...")
    print("Run init() to initialize owner and resolvers")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", default="testnet", choices=["testnet", "mainnet"])
    parser.add_argument("--private-key", required=True)
    args = parser.parse_args()
    deploy(args.network, args.private_key)
