#!/usr/bin/env python3
"""ClaimGuard Interaction Script"""
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--action", required=True, choices=["create-claim", "resolve", "appeal", "stats"])
    parser.add_argument("--url"); parser.add_argument("--expected"); parser.add_argument("--description")
    parser.add_argument("--category", default="custom"); parser.add_argument("--claim-id", type=int)
    args = parser.parse_args()
    print(f"Action: {args.action} | Contract: {args.contract}")

if __name__ == "__main__":
    main()
