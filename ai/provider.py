"""Abstract Base Class for LLM Providers."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface for generative AI integrations."""

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Send prompt to LLM and return generated text response."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials and configuration are present."""
        pass
