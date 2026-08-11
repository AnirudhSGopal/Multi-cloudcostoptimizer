"""
Cloud provider service module dispatcher.
"""
from types import ModuleType
from app.services.cloud import aws, gcp, azure

_PROVIDERS = {
    "aws": aws,
    "gcp": gcp,
    "azure": azure,
}


def get_provider_service(provider: str) -> ModuleType:
    """
    Return the provider service module (aws, gcp, or azure) for *provider*.
    Raises ValueError if provider is unknown.
    """
    key = (provider or "").strip().lower()
    if key not in _PROVIDERS:
        raise ValueError(f"Unsupported cloud provider: {provider!r}. Supported providers: {list(_PROVIDERS.keys())}")
    return _PROVIDERS[key]
