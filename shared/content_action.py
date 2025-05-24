from enum import Enum


class ContentAction(Enum):
    """
    Actions that can be taken based on content moderation score.
    """
    NOT_BLOCK = "NOT_BLOCK"                    # Content is safe, no action needed
    CHECK_BY_MODERATOR = "CHECK_BY_MODERATOR"  # Content needs human review
    BLOCK = "BLOCK"                            # Content should be blocked/removed

    def __str__(self):
        return self.value

    @property
    def description(self):
        """Get human-readable description of the action."""
        descriptions = {
            self.NOT_BLOCK: "Content is considered safe and can be displayed",
            self.CHECK_BY_MODERATOR: "Content requires manual review by a human moderator",
            self.BLOCK: "Content should be blocked or removed immediately"
        }
        return descriptions.get(self, "Unknown action") 