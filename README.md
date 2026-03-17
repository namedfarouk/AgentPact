# AgentPact

Trustless freelance agreements between AI agents on Base.

Built for [The Synthesis](https://synthesis.md) hackathon — **Agents that cooperate** track.

## The Problem

You're a freelancer in Web3. A DAO says "write us a guide, we'll pay you 0.05 ETH." You do the work. Then they ghost you, change the terms, or delay payment indefinitely.

There's no neutral enforcement layer. You trusted a Discord handshake.

When AI agents start making deals on behalf of humans, this problem gets worse. The agent commits to something, but the platform enforcing the deal can rewrite the rules without your consent.

## The Solution

AgentPact lets AI agents negotiate, commit to, and enforce freelance agreements through smart contracts on Base.

The human sets boundaries (budget, deadline, deliverables). The agent operates within them. Payment sits in escrow. When work is submitted and verified, funds release automatically. No middleman, no ghosting.

## How It Works

```
Client's Agent                          Freelancer's Agent
      |                                        |
      |── createPact(terms + ETH escrow) ──>   |
      |                                        |
      |                                        |── submitWork(proof) ──>
      |                                        |
      |── releaseFunds() ──>                   |
      |        (escrow released to freelancer) |
```

### Safety Mechanisms

- **Auto-release:** If the client doesn't respond within 7 days of work submission, funds release automatically to the freelancer
- **Refund:** If the freelancer misses the deadline, the client can reclaim their escrow
- **Dispute:** Either party can flag a pact as disputed
- **Cancel:** Client can cancel unfunded pacts

## Contract

- **Network:** Base Sepolia
- **Address:** [`0x31BC2Ae5995bb31d63ED2Efd36587fC05A374127`](https://sepolia.basescan.org/address/0x31BC2Ae5995bb31d63ED2Efd36587fC05A374127)
- **Solidity:** 0.8.28
- **License:** MIT

### Functions

| Function | Called By | Description |
|---|---|---|
| `createPact` | Client | Create agreement + deposit escrow |
| `fundPact` | Client | Add escrow to existing pact |
| `submitWork` | Freelancer | Submit proof of completion |
| `releaseFunds` | Client | Approve and release payment |
| `autoRelease` | Anyone | Release after 7-day timeout |
| `disputePact` | Either party | Flag as disputed |
| `cancelPact` | Client | Cancel unfunded pact |
| `claimRefund` | Client | Refund if deadline missed |
| `getPact` | Anyone | View pact details |
| `isExpired` | Anyone | Check deadline status |

## Hermes Agent Integration

AgentPact includes a [Hermes Agent](https://nousresearch.com/hermes-agent/) skill that lets the agent interact with the contract autonomously.

### Install the skill

```bash
mkdir -p ~/.hermes/skills/agentpact
cp SKILL.md ~/.hermes/skills/agentpact/SKILL.md
```

### Example conversation

```
You: Create a pact with 0xABC for writing a technical guide, budget 0.01 ETH, deadline 3 days

Hermes: Creating pact...
  Freelancer: 0xABC
  Deadline: 3 days from now
  Description: Write a technical guide
  Escrow: 0.01 ETH
  Transaction confirmed!
  Pact ID: 0
  View: https://sepolia.basescan.org/tx/...
```

## CLI Usage

### Setup

```bash
pip3 install web3
export PRIVATE_KEY="your_private_key"
```

### Commands

```bash
# Create a pact with escrow
python3 agentpact_cli.py create \
  --freelancer 0xADDRESS \
  --deadline 3d \
  --description "Write a technical guide" \
  --value 0.01

# Check pact status
python3 agentpact_cli.py status --pact-id 0

# Submit work proof
python3 agentpact_cli.py submit --pact-id 0 --proof "https://github.com/user/deliverable"

# Release funds
python3 agentpact_cli.py release --pact-id 0

# Dispute a pact
python3 agentpact_cli.py dispute --pact-id 0

# Get total pact count
python3 agentpact_cli.py count
```

### Deadline formats

- `3d` — 3 days
- `12h` — 12 hours
- `1w` — 1 week

## Build from Source

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Clone and build
git clone https://github.com/namedfarouk/AgentPact.git
cd AgentPact
forge build

# Deploy to Base Sepolia
forge create src/AgentPact.sol:AgentPact \
  --rpc-url https://sepolia.base.org \
  --private-key YOUR_PRIVATE_KEY \
  --broadcast
```

## On-Chain Activity

Two test pacts have been created on Base Sepolia:

- **Pact #0:** 0.001 ETH escrow, test pact created via CLI
- **Pact #1:** 0.002 ETH escrow, created autonomously by Hermes Agent

Both transactions are verifiable on [BaseScan](https://sepolia.basescan.org/address/0x31BC2Ae5995bb31d63ED2Efd36587fC05A374127).

## Tech Stack

- **Smart Contract:** Solidity 0.8.28 (Base Sepolia)
- **Build Tool:** Foundry
- **Agent:** Hermes Agent (Nous Research)
- **CLI:** Python 3 + web3.py
- **Chain:** Base (Ethereum L2)

## The Synthesis

This project was built for [The Synthesis](https://synthesis.md) hackathon under the **Agents that cooperate** track.

> Your agents make deals on your behalf. But the commitments they make are enforced by centralized platforms. If the platform changes its rules, the deal your agent made can be rewritten without your consent.

AgentPact solves this by putting the enforcement layer on Ethereum, where no platform can alter the agreement after the fact.

## Author

Built by [Farouk Adam](https://x.com/NamedFarouk) with [Hermes Agent](https://nousresearch.com/hermes-agent/).

## License

MIT
