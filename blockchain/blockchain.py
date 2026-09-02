import os
import sys

from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account


# ============================================================
# Load environment variables
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_FILE = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(ENV_FILE)


RPC_URL = os.getenv(
    "SEPOLIA_RPC_URL"
)

PRIVATE_KEY = os.getenv(
    "SEPOLIA_PRIVATE_KEY"
)

CHAIN_ID = int(
    os.getenv(
        "SEPOLIA_CHAIN_ID",
        "11155111"
    )
)


# ============================================================
# Validate configuration
# ============================================================

if not RPC_URL:
    raise ValueError(
        "SEPOLIA_RPC_URL is missing from .env"
    )

if not PRIVATE_KEY:
    raise ValueError(
        "SEPOLIA_PRIVATE_KEY is missing from .env"
    )


# ============================================================
# Connect to Sepolia
# ============================================================

w3 = Web3(
    Web3.HTTPProvider(
        RPC_URL
    )
)


if not w3.is_connected():
    raise ConnectionError(
        "Could not connect to Sepolia."
    )


# ============================================================
# Load wallet from private key
# ============================================================

account = Account.from_key(
    PRIVATE_KEY
)

WALLET_ADDRESS = account.address


# ============================================================
# Display safe wallet information
# ============================================================

def get_wallet_info():

    balance_wei = w3.eth.get_balance(
        WALLET_ADDRESS
    )

    balance_eth = w3.from_wei(
        balance_wei,
        "ether"
    )

    return {
        "address": WALLET_ADDRESS,
        "balance_eth": float(balance_eth),
        "chain_id": w3.eth.chain_id
    }


# ============================================================
# Record SHA-256 hash on blockchain
# ============================================================

def record_hash_on_chain(
    sha256_hash
):

    # --------------------------------------------------------
    # Validate hash
    # --------------------------------------------------------

    if not isinstance(
        sha256_hash,
        str
    ):
        raise TypeError(
            "SHA-256 hash must be a string."
        )

    sha256_hash = sha256_hash.strip().lower()

    if len(sha256_hash) != 64:
        raise ValueError(
            "SHA-256 hash must contain exactly 64 hexadecimal characters."
        )

    if any(
        character not in "0123456789abcdef"
        for character in sha256_hash
    ):
        raise ValueError(
            "Invalid SHA-256 hash."
        )


    # --------------------------------------------------------
    # Create transaction payload
    # --------------------------------------------------------
    #
    # This text is stored permanently in the transaction data.
    #
    # Example:
    #
    # TRACEFACE|SHA256:d17cd66...
    #
    # --------------------------------------------------------

    payload = (
        "TRACEFACE|SHA256:"
        + sha256_hash
    )

    data = payload.encode(
        "utf-8"
    )


    # --------------------------------------------------------
    # Nonce
    # --------------------------------------------------------

    nonce = w3.eth.get_transaction_count(
        WALLET_ADDRESS,
        "pending"
    )


    # --------------------------------------------------------
    # EIP-1559 fee settings
    # --------------------------------------------------------

    latest_block = w3.eth.get_block(
        "latest"
    )

    base_fee = latest_block.get(
        "baseFeePerGas"
    )

    if base_fee is None:
        gas_price = w3.eth.gas_price

        max_fee_per_gas = gas_price
        max_priority_fee_per_gas = gas_price

    else:

        max_priority_fee_per_gas = w3.to_wei(
            1,
            "gwei"
        )

        max_fee_per_gas = (
            base_fee * 2
            + max_priority_fee_per_gas
        )


    # --------------------------------------------------------
    # Build transaction
    #
    # Zero ETH is transferred.
    # The transaction sends the SHA-256 in the data field.
    # It is sent back to the same wallet.
    # --------------------------------------------------------

    transaction = {

        "from": WALLET_ADDRESS,

        "to": WALLET_ADDRESS,

        "value": 0,

        "nonce": nonce,

        "chainId": CHAIN_ID,

        "data": data,

        "maxFeePerGas":
            max_fee_per_gas,

        "maxPriorityFeePerGas":
            max_priority_fee_per_gas,

        "type": 2
    }


    # --------------------------------------------------------
    # Estimate gas
    # --------------------------------------------------------

    estimated_gas = w3.eth.estimate_gas(
        transaction
    )

    transaction["gas"] = (
        estimated_gas + 5000
    )


    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    required_fee = (
        transaction["gas"]
        * transaction["maxFeePerGas"]
    )

    balance = w3.eth.get_balance(
        WALLET_ADDRESS
    )

    if balance < required_fee:

        raise RuntimeError(
            "Insufficient Sepolia ETH for transaction fee."
        )


    # --------------------------------------------------------
    # Sign transaction locally
    # --------------------------------------------------------

    signed_transaction = (
        w3.eth.account.sign_transaction(
            transaction,
            private_key=PRIVATE_KEY
        )
    )


    # --------------------------------------------------------
    # Broadcast transaction
    # --------------------------------------------------------

    tx_hash = w3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )


    return w3.to_hex(
        tx_hash
    )


# ============================================================
# Wait for confirmation
# ============================================================

def wait_for_confirmation(
    transaction_hash
):

    receipt = (
        w3.eth.wait_for_transaction_receipt(
            transaction_hash,
            timeout=180
        )
    )

    return receipt


# ============================================================
# Read SHA-256 back from blockchain
# ============================================================

def read_hash_from_transaction(
    transaction_hash
):

    tx = w3.eth.get_transaction(
        transaction_hash
    )

    input_data = tx["input"]

    if isinstance(
        input_data,
        str
    ):
        raw_data = bytes.fromhex(
            input_data[2:]
        )

    else:
        raw_data = bytes(
            input_data
        )

    payload = raw_data.decode(
        "utf-8"
    )

    prefix = "TRACEFACE|SHA256:"

    if not payload.startswith(
        prefix
    ):
        raise ValueError(
            "This transaction is not a TraceFace evidence transaction."
        )

    stored_hash = payload[
        len(prefix):
    ]

    return stored_hash


# ============================================================
# Verify SHA-256 against blockchain
# ============================================================

def verify_hash(
    transaction_hash,
    expected_hash
):

    expected_hash = (
        expected_hash.strip().lower()
    )

    blockchain_hash = (
        read_hash_from_transaction(
            transaction_hash
        )
    )

    is_valid = (
        blockchain_hash
        == expected_hash
    )

    return {
        "valid": is_valid,
        "expected_hash": expected_hash,
        "blockchain_hash": blockchain_hash
    }


# ============================================================
# Command-line test
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "========================================"
    )
    print(
        "        TRACEFACE BLOCKCHAIN TEST"
    )
    print(
        "========================================"
    )

    wallet_info = get_wallet_info()

    print(
        "Wallet:",
        wallet_info["address"]
    )

    print(
        "Connected:",
        w3.is_connected()
    )

    print(
        "Chain ID:",
        wallet_info["chain_id"]
    )

    print(
        "Sepolia balance:",
        wallet_info["balance_eth"],
        "ETH"
    )

    print()

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            'python blockchain/blockchain.py "<SHA256_HASH>"'
        )

        sys.exit(1)

    sha256_hash = sys.argv[1]

    print(
        "SHA-256:",
        sha256_hash
    )

    print()
    print(
        "Creating blockchain transaction..."
    )

    tx_hash = record_hash_on_chain(
        sha256_hash
    )

    print()
    print(
        "Transaction sent!"
    )

    print(
        "Transaction hash:",
        tx_hash
    )

    print()
    print(
        "Waiting for confirmation..."
    )

    receipt = wait_for_confirmation(
        tx_hash
    )

    print(
        "Block number:",
        receipt["blockNumber"]
    )

    print(
        "Transaction status:",
        receipt["status"]
    )

    print()
    print(
        "Reading SHA-256 from blockchain..."
    )

    blockchain_hash = (
        read_hash_from_transaction(
            tx_hash
        )
    )

    print(
        "On-chain SHA-256:",
        blockchain_hash
    )

    print()

    verification = verify_hash(
        tx_hash,
        sha256_hash
    )

    if verification["valid"]:

        print(
            "VERIFICATION: SUCCESS ✅"
        )

    else:

        print(
            "VERIFICATION: FAILED ❌"
        )

    print(
        "========================================"
    )