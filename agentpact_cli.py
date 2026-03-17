#!/usr/bin/env python3
"""
AgentPact CLI — Interact with the AgentPact smart contract on Base Sepolia.
Used by Hermes Agent to create, fund, and manage trustless freelance agreements.
"""

import argparse
import json
import os
import sys
import time

try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
except ImportError:
    print("Error: web3 not installed. Run: pip3 install web3")
    sys.exit(1)

# ── Configuration ────────────────────────────────────────

RPC_URL = os.environ.get("RPC_URL", "https://sepolia.base.org")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "")
CONTRACT_ADDRESS = "0x31BC2Ae5995bb31d63ED2Efd36587fC05A374127"
EXPLORER_URL = "https://sepolia.basescan.org"

CONTRACT_ABI = [
    {
        "type": "function",
        "name": "createPact",
        "inputs": [
            {"name": "_freelancer", "type": "address"},
            {"name": "_deadline", "type": "uint256"},
            {"name": "_deliverableDescription", "type": "string"}
        ],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "payable"
    },
    {
        "type": "function",
        "name": "fundPact",
        "inputs": [{"name": "_pactId", "type": "uint256"}],
        "outputs": [],
        "stateMutability": "payable"
    },
    {
        "type": "function",
        "name": "submitWork",
        "inputs": [
            {"name": "_pactId", "type": "uint256"},
            {"name": "_workProof", "type": "string"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "releaseFunds",
        "inputs": [{"name": "_pactId", "type": "uint256"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "disputePact",
        "inputs": [{"name": "_pactId", "type": "uint256"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "cancelPact",
        "inputs": [{"name": "_pactId", "type": "uint256"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "claimRefund",
        "inputs": [{"name": "_pactId", "type": "uint256"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "autoRelease",
        "inputs": [{"name": "_pactId", "type": "uint256"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "getPact",
        "inputs": [{"name": "_pactId", "type": "uint256"}],
        "outputs": [
            {
                "name": "",
                "type": "tuple",
                "components": [
                    {"name": "client", "type": "address"},
                    {"name": "freelancer", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "deliverableDescription", "type": "string"},
                    {"name": "workProof", "type": "string"},
                    {"name": "status", "type": "uint8"},
                    {"name": "createdAt", "type": "uint256"}
                ]
            }
        ],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "isExpired",
        "inputs": [{"name": "_pactId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "pactCount",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view"
    }
]

STATUS_NAMES = {
    0: "Created",
    1: "Funded",
    2: "WorkSubmitted",
    3: "Completed",
    4: "Disputed",
    5: "Cancelled"
}

# ── Helpers ──────────────────────────────────────────────

def get_web3():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"Error: Cannot connect to {RPC_URL}")
        sys.exit(1)
    return w3


def resolve_ens(w3, name_or_address):
    """Resolve ENS name to address, or return address as-is."""
    if name_or_address.endswith(".eth"):
        print(f"Resolving ENS name: {name_or_address}")
        ens_rpc = Web3(Web3.HTTPProvider("https://eth.llamarpc.com"))
        address = ens_rpc.ens.address(name_or_address)
        if address is None:
            print(f"Error: Could not resolve ENS name '{name_or_address}'")
            sys.exit(1)
        print(f"Resolved to: {address}")
        return address
    return Web3.to_checksum_address(name_or_address)


def get_contract(w3):
    return w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=CONTRACT_ABI
    )


def get_account(w3):
    if not PRIVATE_KEY:
        print("Error: Set PRIVATE_KEY environment variable")
        sys.exit(1)
    account = w3.eth.account.from_key(PRIVATE_KEY)
    return account


def send_tx(w3, account, tx_func, value=0):
    """Build, sign, and send a transaction."""
    tx = tx_func.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 500000,
        "maxFeePerGas": w3.to_wei(0.5, "gwei"),
        "maxPriorityFeePerGas": w3.to_wei(0.1, "gwei"),
        "value": value,
        "chainId": 84532,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Transaction sent: {EXPLORER_URL}/tx/{tx_hash.hex()}")
    print("Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status == 1:
        print("Transaction confirmed!")
    else:
        print("Transaction FAILED!")
    return receipt


def parse_deadline(deadline_str):
    """Parse deadline string like '3d', '12h', '1w' into a future timestamp."""
    now = int(time.time())
    unit = deadline_str[-1].lower()
    amount = int(deadline_str[:-1])
    if unit == "d":
        return now + (amount * 86400)
    elif unit == "h":
        return now + (amount * 3600)
    elif unit == "w":
        return now + (amount * 604800)
    else:
        return int(deadline_str)


# ── Commands ─────────────────────────────────────────────

def cmd_create(args):
    """Create a new pact."""
    w3 = get_web3()
    contract = get_contract(w3)
    account = get_account(w3)

    deadline = parse_deadline(args.deadline)
    value = w3.to_wei(args.value, "ether") if args.value else 0

    print(f"\nCreating pact:")
    print(f"  Freelancer: {args.freelancer}")
    print(f"  Deadline: {time.ctime(deadline)}")
    print(f"  Description: {args.description}")
    print(f"  Escrow: {args.value or 0} ETH")
    print()

    tx_func = contract.functions.createPact(
        resolve_ens(w3, args.freelancer),
        deadline,
        args.description
    )
    receipt = send_tx(w3, account, tx_func, value=value)

    # Parse pactId from logs
    pact_count = contract.functions.pactCount().call()
    pact_id = pact_count - 1
    print(f"\nPact created! ID: {pact_id}")
    print(f"View: {EXPLORER_URL}/tx/{receipt.transactionHash.hex()}")


def cmd_fund(args):
    """Fund an existing pact."""
    w3 = get_web3()
    contract = get_contract(w3)
    account = get_account(w3)

    value = w3.to_wei(args.value, "ether")
    print(f"\nFunding pact {args.pact_id} with {args.value} ETH...")

    tx_func = contract.functions.fundPact(args.pact_id)
    receipt = send_tx(w3, account, tx_func, value=value)
    print(f"View: {EXPLORER_URL}/tx/{receipt.transactionHash.hex()}")


def cmd_submit(args):
    """Submit work proof."""
    w3 = get_web3()
    contract = get_contract(w3)
    account = get_account(w3)

    print(f"\nSubmitting work for pact {args.pact_id}...")
    print(f"  Proof: {args.proof}")

    tx_func = contract.functions.submitWork(args.pact_id, args.proof)
    receipt = send_tx(w3, account, tx_func)
    print(f"View: {EXPLORER_URL}/tx/{receipt.transactionHash.hex()}")


def cmd_release(args):
    """Release funds to freelancer."""
    w3 = get_web3()
    contract = get_contract(w3)
    account = get_account(w3)

    print(f"\nReleasing funds for pact {args.pact_id}...")

    tx_func = contract.functions.releaseFunds(args.pact_id)
    receipt = send_tx(w3, account, tx_func)
    print(f"View: {EXPLORER_URL}/tx/{receipt.transactionHash.hex()}")


def cmd_dispute(args):
    """Dispute a pact."""
    w3 = get_web3()
    contract = get_contract(w3)
    account = get_account(w3)

    print(f"\nDisputing pact {args.pact_id}...")

    tx_func = contract.functions.disputePact(args.pact_id)
    receipt = send_tx(w3, account, tx_func)
    print(f"View: {EXPLORER_URL}/tx/{receipt.transactionHash.hex()}")


def cmd_cancel(args):
    """Cancel an unfunded pact."""
    w3 = get_web3()
    contract = get_contract(w3)
    account = get_account(w3)

    print(f"\nCancelling pact {args.pact_id}...")

    tx_func = contract.functions.cancelPact(args.pact_id)
    receipt = send_tx(w3, account, tx_func)
    print(f"View: {EXPLORER_URL}/tx/{receipt.transactionHash.hex()}")


def cmd_refund(args):
    """Claim refund for missed deadline."""
    w3 = get_web3()
    contract = get_contract(w3)
    account = get_account(w3)

    print(f"\nClaiming refund for pact {args.pact_id}...")

    tx_func = contract.functions.claimRefund(args.pact_id)
    receipt = send_tx(w3, account, tx_func)
    print(f"View: {EXPLORER_URL}/tx/{receipt.transactionHash.hex()}")


def cmd_status(args):
    """Check pact status."""
    w3 = get_web3()
    contract = get_contract(w3)

    pact = contract.functions.getPact(args.pact_id).call()
    expired = contract.functions.isExpired(args.pact_id).call()

    print(f"\nPact #{args.pact_id}")
    print(f"  Client:      {pact[0]}")
    print(f"  Freelancer:  {pact[1]}")
    print(f"  Amount:      {w3.from_wei(pact[2], 'ether')} ETH")
    print(f"  Deadline:    {time.ctime(pact[3])}")
    print(f"  Description: {pact[4]}")
    print(f"  Work Proof:  {pact[5] or 'Not submitted'}")
    print(f"  Status:      {STATUS_NAMES.get(pact[6], 'Unknown')}")
    print(f"  Created:     {time.ctime(pact[7])}")
    print(f"  Expired:     {'Yes' if expired else 'No'}")
    print(f"  View:        {EXPLORER_URL}/address/{CONTRACT_ADDRESS}")


def cmd_count(args):
    """Get total pact count."""
    w3 = get_web3()
    contract = get_contract(w3)
    count = contract.functions.pactCount().call()
    print(f"\nTotal pacts created: {count}")


# ── Main ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AgentPact CLI — Trustless freelance agreements on Base"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create
    p_create = subparsers.add_parser("create", help="Create a new pact")
    p_create.add_argument("--freelancer", required=True, help="Freelancer wallet address")
    p_create.add_argument("--deadline", required=True, help="Deadline (e.g. 3d, 12h, 1w)")
    p_create.add_argument("--description", required=True, help="Deliverable description")
    p_create.add_argument("--value", type=float, default=0, help="ETH to escrow")

    # fund
    p_fund = subparsers.add_parser("fund", help="Fund an existing pact")
    p_fund.add_argument("--pact-id", type=int, required=True)
    p_fund.add_argument("--value", type=float, required=True, help="ETH to deposit")

    # submit
    p_submit = subparsers.add_parser("submit", help="Submit work proof")
    p_submit.add_argument("--pact-id", type=int, required=True)
    p_submit.add_argument("--proof", required=True, help="Link or hash of deliverable")

    # release
    p_release = subparsers.add_parser("release", help="Release funds to freelancer")
    p_release.add_argument("--pact-id", type=int, required=True)

    # dispute
    p_dispute = subparsers.add_parser("dispute", help="Dispute a pact")
    p_dispute.add_argument("--pact-id", type=int, required=True)

    # cancel
    p_cancel = subparsers.add_parser("cancel", help="Cancel an unfunded pact")
    p_cancel.add_argument("--pact-id", type=int, required=True)

    # refund
    p_refund = subparsers.add_parser("refund", help="Claim refund for missed deadline")
    p_refund.add_argument("--pact-id", type=int, required=True)

    # status
    p_status = subparsers.add_parser("status", help="Check pact status")
    p_status.add_argument("--pact-id", type=int, required=True)

    # count
    subparsers.add_parser("count", help="Get total pact count")

    args = parser.parse_args()

    commands = {
        "create": cmd_create,
        "fund": cmd_fund,
        "submit": cmd_submit,
        "release": cmd_release,
        "dispute": cmd_dispute,
        "cancel": cmd_cancel,
        "refund": cmd_refund,
        "status": cmd_status,
        "count": cmd_count,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
