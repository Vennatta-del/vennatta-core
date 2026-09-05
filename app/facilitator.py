"""Custom x402 facilitator for Vennatta Core."""

from __future__ import annotations

import logging
import time
import traceback
from typing import Any

from eth_account import Account
from web3 import Web3

from x402.schemas import Network, PaymentPayload, PaymentRequirements, SettleResponse, SupportedKind, SupportedResponse, VerifyResponse
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
        logger.info(f"✅ VennattaFacilitator initialized on chain {self.chain_id}")

    def supported(self) -> SupportedResponse:
        kinds = [SupportedKind(network=net, scheme=scheme, x402_version=2, required_extensions=[]) for net in self.supported_networks for scheme in self.supported_schemes]
        return SupportedResponse(kinds=kinds, extensions=[], signers={})

    async def verify(self, payload: PaymentPayload, requirements: PaymentRequirements) -> VerifyResponse:
        logger.info(f"🔍 verify() called")
        try:
            logger.info(f"  payload: {payload}")
            logger.info(f"  requirements: {requirements}")
            
            payload_data = payload.payload
            if not payload_data or "authorization" not in payload_data:
                logger.warning("Missing authorization")
                return VerifyResponse(is_valid=False, invalid_reason="missing_authorization", invalid_message="Missing authorization", payer=None)

            authorization = payload_data["authorization"]
            signature = payload_data.get("signature")
            logger.info(f"  authorization: {authorization}")
            logger.info(f"  signature present: {bool(signature)}")

            if not signature:
                logger.warning("Missing signature")
                return VerifyResponse(is_valid=False, invalid_reason="missing_signature", invalid_message="Missing signature", payer=None)

            payer = authorization.get("from")
            if not payer:
                logger.warning("Cannot extract payer")
                return VerifyResponse(is_valid=False, invalid_reason="invalid_authorization", invalid_message="Cannot extract payer", payer=None)

            for field in ["from", "to", "value", "validAfter", "validBefore", "nonce"]:
                if field not in authorization:
                    logger.warning(f"Missing field: {field}")
                    return VerifyResponse(is_valid=False, invalid_reason=f"missing_{field.lower()}", invalid_message=f"Missing {field}", payer=payer)

            if not signature.startswith("0x") or len(signature) != 132:
                logger.warning(f"Invalid signature format: {signature[:20]}...")
                return VerifyResponse(is_valid=False, invalid_reason="invalid_signature_format", invalid_message="Invalid signature format", payer=payer)

            current_time = int(time.time())
            valid_after = int(authorization["validAfter"])
            valid_before = int(authorization["validBefore"])
            logger.info(f"  time check: now={current_time}, valid_after={valid_after}, valid_before={valid_before}")
            
            if current_time < valid_after:
                logger.warning("Not yet valid")
                return VerifyResponse(is_valid=False, invalid_reason="valid_after_future", invalid_message="Not yet valid", payer=payer)

            if current_time > valid_before:
                logger.warning("Expired")
                return VerifyResponse(is_valid=False, invalid_reason="valid_before_expired", invalid_message="Expired", payer=payer)

            logger.info("  Verifying signature...")
            if not self._verify_eip3009_signature(authorization, signature, payer, requirements.asset):
                logger.warning("Signature verification FAILED")
                return VerifyResponse(is_valid=False, invalid_reason="invalid_signature", invalid_message="Signature verification failed", payer=payer)

            logger.info("  Checking balance...")
            if not await self._check_balance(payer, requirements.asset, int(requirements.amount)):
                logger.warning("Insufficient balance")
                return VerifyResponse(is_valid=False, invalid_reason="insufficient_balance", invalid_message="Insufficient balance", payer=payer)

            logger.info(f"✅ Payment VERIFIED: {payer}, {int(requirements.amount)}")
            return VerifyResponse(is_valid=True, invalid_reason=None, invalid_message=None, payer=payer)

        except Exception as e:
            logger.error(f"❌ Verification EXCEPTION: {e}")
            logger.error(traceback.format_exc())
            return VerifyResponse(is_valid=False, invalid_reason="verification_error", invalid_message=str(e), payer=None)

    async def settle(self, payload: PaymentPayload, requirements: PaymentRequirements) -> SettleResponse:
        logger.info(f"⚠️ settle() called")
        try:
            authorization = payload.payload["authorization"]
            payer = authorization.get("from", "")
            value = authorization.get("value", requirements.amount)
            logger.info(f"⚠️ Settlement mocked: {payer}, {value}")
            return SettleResponse(success=True, error_reason=None, error_message=None, payer=payer, transaction="0x" + "00" * 32, network=requirements.network, amount=value)
        except Exception as e:
            logger.error(f"Settlement error: {e}")
            return SettleResponse(success=False, error_reason="settlement_error", error_message=str(e), payer="", transaction="", network=requirements.network, amount=None)

    def _verify_eip3009_signature(self, authorization: dict[str, Any], signature: str, expected_signer: str, token_address: str) -> bool:
        """Verify EIP-3009 signature."""
        try:
            logger.info(f"  _verify_eip3009_signature: token={token_address}, signer={expected_signer}")
            from eth_account.messages import encode_typed_data
            
            signable = encode_typed_data(
                domain_data={"name": "USD Coin", "version": "2", "chainId": self.chain_id, "verifyingContract": Web3.to_checksum_address(token_address)},
                message_types={"TransferWithAuthorization": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "validAfter", "type": "uint256"}, {"name": "validBefore", "type": "uint256"}, {"name": "nonce", "type": "bytes32"}]},
                message_data={"from": Web3.to_checksum_address(authorization["from"]), "to": Web3.to_checksum_address(authorization["to"]), "value": int(authorization["value"]), "validAfter": int(authorization["validAfter"]), "validBefore": int(authorization["validBefore"]), "nonce": authorization["nonce"]},
            )
            
            recovered = Account.recover_message(signable, signature=signature)
            logger.info(f"  Recovered: {recovered}, Expected: {expected_signer}")
            result = recovered.lower() == Web3.to_checksum_address(expected_signer).lower()
            logger.info(f"  Signature valid: {result}")
            return result

        except Exception as e:
            logger.error(f"  Signature verification EXCEPTION: {e}")
            logger.error(traceback.format_exc())
            return False

    async def _check_balance(self, payer: str, token_address: str, required_amount: int) -> bool:
        try:
            logger.info(f"  _check_balance: {payer}, {token_address}, {required_amount}")
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            balance = contract.functions.balanceOf(Web3.to_checksum_address(payer)).call()
            logger.info(f"  Balance: {balance}")
            return balance >= required_amount
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return False
