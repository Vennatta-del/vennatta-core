"""Custom x402 facilitator for Vennatta Core."""

from __future__ import annotations

import logging
import time
from typing import Any

from eth_account import Account
from eth_utils import keccak
from web3 import Web3

from x402.schemas import (
    Network,
    PaymentPayload,
    PaymentRequirements,
    SettleResponse,
    SupportedKind,
    SupportedResponse,
    VerifyResponse,
)
from x402.server_base import FacilitatorClient

logger = logging.getLogger("x402")

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "success", "type": "bool"}], "type": "function"},
]


class VennattaFacilitator(FacilitatorClient):
    def __init__(self, rpc_url: str, supported_networks: list[Network] | None = None, supported_schemes: list[str] | None = None) -> None:
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain_id = self.w3.eth.chain_id
        self.supported_networks = supported_networks or [Network(id="eip155:8453", name="Base")]
        self.supported_schemes = supported_schemes or ["exact"]
        logger.info(f"Initialized VennattaFacilitator on chain {self.chain_id}")

    def supported(self) -> SupportedResponse:
        kinds = [SupportedKind(network=net, scheme=scheme, x402_version=2, required_extensions=[]) for net in self.supported_networks for scheme in self.supported_schemes]
        return SupportedResponse(kinds=kinds, extensions=[], signers={})

    async def verify(self, payload: PaymentPayload, requirements: PaymentRequirements) -> VerifyResponse:
        try:
            payload_data = payload.payload
            if not payload_data or "authorization" not in payload_data:
                return VerifyResponse(is_valid=False, invalid_reason="missing_authorization", invalid_message="Payment payload missing authorization", payer=None)

            authorization = payload_data["authorization"]
            signature = payload_data.get("signature")

            if not signature:
                return VerifyResponse(is_valid=False, invalid_reason="missing_signature", invalid_message="Payment payload missing signature", payer=None)

            payer = authorization.get("from")
            if not payer:
                return VerifyResponse(is_valid=False, invalid_reason="invalid_authorization", invalid_message="Cannot extract payer from authorization", payer=None)

            for field in ["from", "to", "value", "validAfter", "validBefore", "nonce"]:
                if field not in authorization:
                    return VerifyResponse(is_valid=False, invalid_reason=f"missing_{field.lower()}", invalid_message=f"Authorization missing {field}", payer=payer)

            if not signature.startswith("0x") or len(signature) != 132:
                return VerifyResponse(is_valid=False, invalid_reason="invalid_signature_format", invalid_message="Signature must be 65 bytes (0x-prefixed)", payer=payer)

            current_time = int(time.time())
            valid_after = int(authorization["validAfter"])
            valid_before = int(authorization["validBefore"])

            if current_time < valid_after:
                return VerifyResponse(is_valid=False, invalid_reason="valid_after_future", invalid_message="Authorization not yet valid", payer=payer)

            if current_time > valid_before:
                return VerifyResponse(is_valid=False, invalid_reason="valid_before_expired", invalid_message="Authorization has expired", payer=payer)

            # Verify EIP-3009 signature
            if not self._verify_eip3009_signature(authorization, signature, payer, requirements.asset):
                return VerifyResponse(is_valid=False, invalid_reason="invalid_signature", invalid_message="EIP-3009 signature verification failed", payer=payer)

            # Check balance
            if not await self._check_balance(payer, requirements.asset, int(requirements.amount)):
                return VerifyResponse(is_valid=False, invalid_reason="insufficient_balance", invalid_message="Payer has insufficient balance", payer=payer)

            logger.info(f"✅ Payment verified for payer: {payer}, amount: {int(requirements.amount)}")
            return VerifyResponse(is_valid=True, invalid_reason=None, invalid_message=None, payer=payer)

        except Exception as e:
            logger.error(f"Verification error: {e}", exc_info=True)
            return VerifyResponse(is_valid=False, invalid_reason="verification_error", invalid_message=str(e), payer=None)

    async def settle(self, payload: PaymentPayload, requirements: PaymentRequirements) -> SettleResponse:
        try:
            payload_data = payload.payload
            authorization = payload_data["authorization"]
            payer = authorization.get("from", "")
            value = authorization.get("value", requirements.amount)
            tx_hash = "0x" + "00" * 32
            logger.info(f"⚠️ Settlement mocked for payer: {payer}, amount: {value}")
            return SettleResponse(success=True, error_reason=None, error_message=None, payer=payer, transaction=tx_hash, network=requirements.network, amount=value)
        except Exception as e:
            logger.error(f"Settlement error: {e}", exc_info=True)
            return SettleResponse(success=False, error_reason="settlement_error", error_message=str(e), payer="", transaction="", network=requirements.network, amount=None)

    def _verify_eip3009_signature(self, authorization: dict[str, Any], signature: str, expected_signer: str, token_address: str) -> bool:
        """Verify EIP-3009 signature using manual EIP-712 hashing."""
        try:
            # Use eth_account's encode_typed_data which matches the client
            from eth_account.messages import encode_typed_data
            
            domain = {"name": "USD Coin", "version": "2", "chainId": self.chain_id, "verifyingContract": Web3.to_checksum_address(token_address)}
            message = {
                "from": Web3.to_checksum_address(authorization["from"]),
                "to": Web3.to_checksum_address(authorization["to"]),
                "value": int(authorization["value"]),
                "validAfter": int(authorization["validAfter"]),
                "validBefore": int(authorization["validBefore"]),
                "nonce": authorization["nonce"],
            }
            
            full_message = {
                "types": {
                    "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}, {"name": "chainId", "type": "uint256"}, {"name": "verifyingContract", "type": "address"}],
                    "TransferWithAuthorization": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "validAfter", "type": "uint256"}, {"name": "validBefore", "type": "uint256"}, {"name": "nonce", "type": "bytes32"}],
                },
                "primaryType": "TransferWithAuthorization",
                "domain": domain,
                "message": message,
            }
            
            signable = encode_typed_data(full_message=full_message)
            recovered = Account.recover_message(signable, signature=signature)
            return recovered.lower() == Web3.to_checksum_address(expected_signer).lower()

        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    async def _check_balance(self, payer: str, token_address: str, required_amount: int) -> bool:
        try:
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            balance = contract.functions.balanceOf(Web3.to_checksum_address(payer)).call()
            return balance >= required_amount
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return False
