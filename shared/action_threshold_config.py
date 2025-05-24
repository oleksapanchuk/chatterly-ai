from typing import Dict, Any
from dataclasses import dataclass
from shared.content_action import ContentAction


@dataclass
class ActionThresholdConfig:
    """
    Configuration for action thresholds based on content scores.
    Determines what action to take for different score ranges.
    """
    
    # Default thresholds
    not_block_threshold: float = 25.0      # Scores below this are NOT_BLOCK
    block_threshold: float = 75.0          # Scores at or above this are BLOCK
                                          # Scores between are CHECK_BY_MODERATOR

    def __post_init__(self):
        """Validate threshold configuration after initialization."""
        if not 0 <= self.not_block_threshold <= 100:
            raise ValueError(f"not_block_threshold must be between 0 and 100, got {self.not_block_threshold}")
        
        if not 0 <= self.block_threshold <= 100:
            raise ValueError(f"block_threshold must be between 0 and 100, got {self.block_threshold}")
        
        if self.not_block_threshold >= self.block_threshold:
            raise ValueError(f"not_block_threshold ({self.not_block_threshold}) must be less than block_threshold ({self.block_threshold})")

    @classmethod
    def get_default_config(cls) -> 'ActionThresholdConfig':
        """Get default threshold configuration."""
        return cls()

    def determine_action(self, score: float) -> ContentAction:
        """
        Determine the appropriate action based on the content score.
        
        Args:
            score: Content moderation score (0-100)
            
        Returns:
            ContentAction: The action to take
        """
        if score < self.not_block_threshold:
            return ContentAction.NOT_BLOCK
        elif score >= self.block_threshold:
            return ContentAction.BLOCK
        else:
            return ContentAction.CHECK_BY_MODERATOR

    def get_threshold_ranges(self) -> Dict[ContentAction, str]:
        """Get human-readable threshold ranges for each action."""
        return {
            ContentAction.NOT_BLOCK: f"< {self.not_block_threshold}",
            ContentAction.CHECK_BY_MODERATOR: f"{self.not_block_threshold} - {self.block_threshold - 0.01:.2f}",
            ContentAction.BLOCK: f">= {self.block_threshold}"
        }

    def to_dict(self) -> Dict[str, float]:
        """Convert configuration to dictionary for serialization."""
        return {
            "not_block_threshold": self.not_block_threshold,
            "block_threshold": self.block_threshold
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ActionThresholdConfig':
        """Create configuration from dictionary."""
        not_block_threshold = 25.0  # Default
        block_threshold = 75.0      # Default
        
        if "not_block_threshold" in config_dict:
            try:
                not_block_threshold = float(config_dict["not_block_threshold"])
            except (ValueError, TypeError):
                pass  # Use default
        
        if "block_threshold" in config_dict:
            try:
                block_threshold = float(config_dict["block_threshold"])
            except (ValueError, TypeError):
                pass  # Use default
        
        return cls(not_block_threshold=not_block_threshold, block_threshold=block_threshold) 