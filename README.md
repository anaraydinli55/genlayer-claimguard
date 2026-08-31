# ClaimGuard — AI-Powered On-Chain Claim Verification

> A reusable GenLayer **Intelligent Contract** primitive that verifies real-world claims by fetching web evidence and using LLM consensus to evaluate truthfulness.

## What is ClaimGuard?

ClaimGuard is a decentralized claim verification protocol built on GenLayer. It allows anyone to submit a claim about real-world content and have it verified by AI validators that:

1. **Fetch web evidence** using `gl.nondet.web.render/get`
2. **Evaluate with LLM consensus** using `gl.eq_principle.json_eq`
3. **Emit on-chain results** with confidence scores and reasoning

## Architecture

```
User submits claim → ClaimGuard IC → Web Evidence (non-det)
                              ↓
                    LLM Evaluation (json_eq consensus)
                              ↓
                    On-chain Result + Appeal System
```

## Features

- **Web Evidence Fetching** — Renders JS-heavy pages or falls back to plain GET
- **LLM Consensus** — Uses `json_eq` for structured validator agreement
- **6 Claim Categories** — Prediction markets, bounties, moderation, identity, fact check, custom
- **Appeal System** — Up to 3 appeals per claim with new evidence URLs
- **Role-Based Access** — Owner-managed resolver whitelist
- **Full Event Emission** — `ClaimCreated`, `ClaimResolved`, `ClaimAppealed`
- **BountyManager** — Decentralized bounty platform integrated with ClaimGuard

## Contract API

### ClaimGuard Write Methods
| Method | Description |
|--------|-------------|
| `init()` | Initialize contract, sets deployer as owner |
| `createClaim(url, expected_content, description, category)` | Submit a new claim |
| `resolveClaim(claim_id)` | Resolve pending claim (resolver only) |
| `appealClaim(claim_id, new_evidence_url)` | Appeal a resolved claim |
| `addResolver(address)` | Add approved resolver (owner only) |
| `removeResolver(address)` | Remove resolver (owner only) |

### ClaimGuard View Methods
| Method | Description |
|--------|-------------|
| `getClaim(claim_id)` | Get full claim details |
| `getClaimsByStatus(status)` | Filter by status |
| `getClaimsByCategory(category)` | Filter by category |
| `getAllClaims()` | List all claims |
| `getStats()` | Protocol statistics |

### BountyManager Methods
| Method | Description |
|--------|-------------|
| `createBounty(title, desc, reward, evidence_url, expected_evidence)` | Create bounty with ClaimGuard claim |
| `submitWork(bounty_id, proof_url)` | Worker submits proof |
| `verifyAndRelease(bounty_id)` | Verify via ClaimGuard and release reward |
| `cancelBounty(bounty_id)` | Creator cancels bounty |

## Tech Stack

- **Contract**: Python (GenLayer Intelligent Contract)
- **Frontend**: Next.js 15 + React 19 + TypeScript + Tailwind CSS + RainbowKit
- **Testing**: pytest with mocked GenLayer environment (no external SDK needed)

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/anaraydinli/genlayer-claimguard.git
cd genlayer-claimguard
```

### 2. Install Python dependencies

```bash
pip install pytest
```

### 3. Run tests (mock-based, no GenLayer SDK needed)

```bash
pytest tests/test_claimguard.py -v
```

### 4. Check contract syntax

```bash
python scripts/check.py
```

### 5. Setup frontend

```bash
cd frontend
npm install
```

### 6. Configure environment

```bash
cp ../.env.example .env.local
# Edit .env.local with your values
```

### 7. Run frontend

```bash
npm run dev
# Open http://localhost:3000
```

## Deploy to GenLayer

### Option A: GenLayer Studio (Recommended for testing)

1. Go to [studio.genlayer.com](https://studio.genlayer.com)
2. Create new project
3. Paste `contracts/ClaimGuard.py` content
4. Click **Deploy**
5. Run `init()` to set owner

### Option B: GenLayer CLI (When available)

```bash
# Install GenLayer CLI (when published)
npm install -g @genlayer/cli

# Deploy
genlayer deploy contracts/ClaimGuard.py --network testnet
```

### Option C: Manual Deploy via Portal

1. Go to [portal.genlayer.foundation](https://portal.genlayer.foundation)
2. Navigate to **Deploy Contract**
3. Upload `contracts/ClaimGuard.py`
4. Deploy and run `init()`

## Testnet Faucet

Get test GEN tokens:
- [testnet-faucet.genlayer.foundation](https://testnet-faucet.genlayer.foundation/)
- Requires 0.01 ETH on Ethereum mainnet
- 100 GEN / week

## GenLayer Portal Submission

**Category:** Builder → Intelligent Contracts

**Description:**
> ClaimGuard is a reusable GenLayer primitive for AI-powered on-chain claim verification. It fetches real-time web evidence using `gl.nondet.web.render`, evaluates claims through LLM consensus with `gl.eq_principle.json_eq`, and features a built-in appeal system. Includes BountyManager — a decentralized bounty platform integrated with ClaimGuard for automated task verification. Features RainbowKit wallet connect and full test suite.

**Why this is a strong primitive:**
- Reusable by other dApps (prediction markets, bounties, moderation)
- Real GenLayer consensus logic with `json_eq`
- Thoughtful validator design with confidence thresholds
- Clear state design and event emissions
- Full frontend + documentation

## License

MIT

## Deploy
- **Network:** GenLayer Bradbury Testnet
- **Contract Address:** `0x42f58D65B39F05d3cD95B9Fb8a021d7EC6998985`
- **Explorer:** https://explorer-bradbury.genlayer.com/address/0x42f58D65B39F05d3cD95B9Fb8a021d7EC6998985

## Deploy
- **Network:** GenLayer Bradbury Testnet
- **Contract Address:** `0x42f58D65B39F05d3cD95B9Fb8a021d7EC6998985`
