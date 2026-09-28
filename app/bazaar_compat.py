from typing import Any

from x402.extensions.bazaar import OutputConfig
from x402.extensions.bazaar.resource_service import (
    _create_body_discovery_extension,
)


def declare_body_discovery_extension(
    *,
    input: dict[str, Any] | None = None,
    input_schema: dict[str, Any] | None = None,
    path_params_schema: dict[str, Any] | None = None,
    body_type: str = "json",
    output: OutputConfig | None = None,
    method: str = "POST",
) -> dict[str, Any]:
    if method not in {"POST", "PUT", "PATCH"}:
        raise ValueError(f"Unsupported body method: {method}")

    extension = _create_body_discovery_extension(
        input_data=input,
        input_schema=input_schema,
        path_params_schema=path_params_schema,
        body_type=body_type,
        output=output,
    )

    result = extension.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )

    result.setdefault("info", {}).setdefault("input", {})["method"] = method

    return result
