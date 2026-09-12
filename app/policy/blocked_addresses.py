from __future__ import annotations

BLOCKED_ADDRESSES: frozenset[str] = frozenset({
    "0xf111122404b8C2FC01dfF89C65D3104fbb608008".lower(),
    "0x60f456333b4f57e41140d484fb7d2bACe824109c".lower(),
    "0x8Ca0c75932E845fF4291D6eBEDc17cfbBC584D40".lower(),
    "0x52F7B438B3C72d9a834FE7CBc00D78E948d706D5".lower(),
    "0xDFd5293D8e347dFe59E90eFd55b2956a1343963d".lower(),
    "0x28C6c06298d514Db089934071355E5743bf21d60".lower(),
    "0x00799bbc833D5B168F0410312d2a8fD9e0e3079c".lower(),
    "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE".lower(),
    "0x001866Ae5B3de6cAa5a51543FD9fB64f524F5478".lower(),
    "0x00D3BE4ac3563b8E8b8704cf11e074f9959D749f".lower(),
    "0x04ec44dCDfEBf59Cb3C96E62B95F4fffFE3c22F0".lower(),
    "0x0E3508c8dE4A863c874918840894bC9E7D56D582".lower(),
    "0xbAc84302846B3501b803c8A239D30355a3A88633".lower(),
})

def is_blocked_address(address: str | None) -> bool:
    return bool(address) and address.lower() in BLOCKED_ADDRESSES
