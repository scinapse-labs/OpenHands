from __future__ import annotations

import warnings
from typing import Any, cast

from pydantic import SecretStr


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import litellm


def infer_litellm_provider(*, model: str, api_base: str | None) -> str | None:
    """Infer the LiteLLM provider for a given model.

    This delegates to LiteLLM's provider inference logic.
    """
    try:
        get_llm_provider = cast(Any, litellm).get_llm_provider
        _model, provider, _dynamic_key, _api_base = get_llm_provider(
            model=model,
            custom_llm_provider=None,
            api_base=api_base,
            api_key=None,
        )
    except Exception:
        return None

    return provider


def coerce_llm_api_key_for_model(
    *,
    api_key: SecretStr | None,
    model: str | None,
    api_base: str | None,
) -> SecretStr | None:
    """Return an api_key value appropriate for the given model/provider.

    For Bedrock models, LiteLLM treats api_key as an AWS bearer token. When using
    IAM/SigV4 auth, this should be omitted.
    """
    if api_key is None or model is None:
        return api_key

    if infer_litellm_provider(model=model, api_base=api_base) == "bedrock":
        return None

    return api_key
