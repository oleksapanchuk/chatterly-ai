from typing import Optional

from shared.action_threshold_config import ActionThresholdConfig
from shared.content_action import ContentAction
from shared.logger_config import get_logger


class ContentDecisionService:
    """
    Service responsible for deciding what action to take based on content moderation scores.
    Uses configurable thresholds to determine whether content should be blocked,
    reviewed by a moderator, or allowed.
    """

    def __init__(self, threshold_config: Optional[ActionThresholdConfig] = None):
        self.logger = get_logger(__name__)
        self.threshold_config = threshold_config or ActionThresholdConfig.get_default_config()
        self.logger.info("ContentDecisionService initialized")
        self.logger.debug(f"Using threshold configuration: {self.threshold_config.to_dict()}")

    def decide_action(self, score: float) -> ContentAction:
        """
        Determine the appropriate action based on the content score.
        
        Args:
            score: Content moderation score (0-100)
            
        Returns:
            ContentAction: The recommended action to take
        """
        action = self.threshold_config.determine_action(score)

        self.logger.info(f"Content decision: score={score:.2f} -> action={action.value}")
        self.logger.debug(f"Threshold ranges: {self.threshold_config.get_threshold_ranges()}")

        return action

    def get_decision_explanation(self, score: float, action: ContentAction) -> str:
        """
        Get a human-readable explanation of the decision.
        
        Args:
            score: Content moderation score
            action: The determined action
            
        Returns:
            str: Human-readable explanation
        """
        ranges = self.threshold_config.get_threshold_ranges()
        range_text = ranges.get(action, "unknown range")

        explanation = (
            f"Content score of {score:.2f} falls in the {action.value} range ({range_text}). "
            f"{action.description}."
        )

        return explanation

    def update_threshold_config(self, new_config: ActionThresholdConfig):
        """
        Update the threshold configuration.
        
        Args:
            new_config: New threshold configuration to use
        """
        self.threshold_config = new_config
        self.logger.info(f"Threshold configuration updated: {new_config.to_dict()}")

    def get_current_thresholds(self) -> ActionThresholdConfig:
        """Get the current threshold configuration."""
        return self.threshold_config
