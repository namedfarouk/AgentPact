# AgentPact — Trustless Freelance Agreements on Base

## Overview
AgentPact lets AI agents negotiate, commit to, and enforce freelance agreements through smart contracts on Base. The human sets boundaries (budget, deadline, deliverable). The agent operates within them.

## Contract Details
- **Network:** Base Sepolia
- **Contract Address:** 0x31BC2Ae5995bb31d63ED2Efd36587fC05A374127
- **Explorer:** https://sepolia.basescan.org/address/0x31BC2Ae5995bb31d63ED2Efd36587fC05A374127

## How It Works

### Flow
1. **Client's agent** creates a pact with terms + deposits ETH into escrow
2. **Freelancer's agent** reviews and accepts by beginning work
3. **Freelancer's agent** submits proof of completed work before deadline
4. **Client's agent** approves and releases escrow payment
5. If client ghosts → auto-release pays freelancer after 7 days
6. If freelancer misses deadline → client can claim refund
7. Either side can dispute if something goes wrong

### Contract Functions

#### createPact(freelancer, deadline, description)
- Called by: Client
- Creates a new agreement with terms
- Can include ETH as escrow in the same transaction
- Returns: pactId

#### fundPact(pactId)
- Called by: Client
- Deposits ETH into escrow for an existing pact

#### submitWork(pactId, workProof)
- Called by: Freelancer
- Submits proof of completion (link, IPFS hash, or description)
- Must be before deadline

#### releaseFunds(pactId)
- Called by: Client
- Approves work and releases escrow to freelancer

#### autoRelease(pactId)
- Called by: Anyone
- Releases funds if client hasn't acted 7 days after work submission

#### disputePact(pactId)
- Called by: Client or Freelancer
- Flags the pact as disputed

#### cancelPact(pactId)
- Called by: Client
- Cancels an unfunded pact

#### claimRefund(pactId)
- Called by: Client
- Refunds escrow if freelancer missed the deadline

#### getPact(pactId)
- Called by: Anyone
- Returns full pact details (client, freelancer, amount, deadline, status, etc.)

#### isExpired(pactId)
- Called by: Anyone
- Returns true if deadline has passed

### Pact Statuses
- 0 = Created (no funds yet)
- 1 = Funded (escrow deposited)
- 2 = WorkSubmitted (freelancer delivered)
- 3 = Completed (funds released)
- 4 = Disputed
- 5 = Cancelled

## Using the Python Script

The `agentpact_cli.py` script in the project root provides CLI commands for interacting with the contract.

### Create a pact
```bash
python3 agentpact_cli.py create --freelancer 0xADDRESS --deadline 3d --description "Write a technical guide" --value 0.01
```

### Fund a pact
```bash
python3 agentpact_cli.py fund --pact-id 0 --value 0.01
```

### Submit work
```bash
python3 agentpact_cli.py submit --pact-id 0 --proof "https://github.com/user/deliverable"
```

### Release funds
```bash
python3 agentpact_cli.py release --pact-id 0
```

### Check pact status
```bash
python3 agentpact_cli.py status --pact-id 0
```

### Dispute a pact
```bash
python3 agentpact_cli.py dispute --pact-id 0
```

## Example Agent Conversation

User: "Create a pact with 0xABC for writing a Miden technical guide, budget 0.01 ETH, deadline 3 days"

Agent actions:
1. Calls createPact with the freelancer address, deadline timestamp, and description
2. Sends 0.01 ETH as escrow
3. Reports the pact ID and BaseScan link

User: "Check the status of pact 0"

Agent actions:
1. Calls getPact(0)
2. Reports current status, deadline, amount, and parties

## Important Rules
- The human always sets the boundaries (budget limits, deadlines, approved addresses)
- The agent executes within those boundaries
- Never create a pact without explicit user approval for the amount
- Always confirm before releasing funds
- Always show the BaseScan link after any transaction
