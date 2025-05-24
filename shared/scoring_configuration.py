from typing import Dict, Optional
from dataclasses import dataclass, field
from shared.validation_types import ContentCategory


@dataclass
class ScoringConfiguration:
    """
    Configuration class for scoring parameters.
    Allows customization of category base risks and content type modifiers per request.
    """
    
    category_base_risk: Dict[ContentCategory, float] = field(default_factory=lambda: {
        ContentCategory.HATE_SPEECH: 85,      # Very high societal harm
        ContentCategory.HARASSMENT: 75,       # High interpersonal harm
        ContentCategory.VIOLENCE: 80,         # High physical safety risk
        ContentCategory.SELF_HARM: 90,        # Extreme individual risk
        ContentCategory.SEXUAL: 60,           # Moderate policy violation
        ContentCategory.MISINFORMATION: 45,   # Medium societal concern
        ContentCategory.SPAM: 25,             # Low-level annoyance
        ContentCategory.NONE: 0               # No risk
    })
    
    content_type_modifiers: Dict[str, float] = field(default_factory=lambda: {
        "text": 0,      # Baseline - requires cognitive processing
        "image": 12,    # High impact - immediate emotional processing, 90% visual preference  
        "audio": 6      # Medium impact - temporal + emotional but with transcription degradation
    })

    def __post_init__(self):
        """Validate configuration values after initialization."""
        # Validate category base risks
        for category, risk in self.category_base_risk.items():
            if not 0 <= risk <= 100:
                raise ValueError(f"Category base risk for {category.value} must be between 0 and 100, got {risk}")
        
        # Validate content type modifiers
        for content_type, modifier in self.content_type_modifiers.items():
            if not 0 <= modifier <= 50:  # Reasonable upper bound for modifiers
                raise ValueError(f"Content type modifier for {content_type} must be between 0 and 50, got {modifier}")

    @classmethod
    def get_default_configuration(cls) -> 'ScoringConfiguration':
        """Get default scoring configuration with empirically-based values."""
        return cls()

    def get_category_base_risk(self, category: ContentCategory) -> float:
        """Get base risk for a specific category."""
        return self.category_base_risk.get(category, 0)

    def get_content_type_modifier(self, content_type: str) -> float:
        """Get modifier for a specific content type."""
        return self.content_type_modifiers.get(content_type, 0)

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for serialization."""
        return {
            "category_base_risk": {k.value: v for k, v in self.category_base_risk.items()},
            "content_type_modifiers": self.content_type_modifiers
        }

    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'ScoringConfiguration':
        """Create configuration from dictionary."""
        category_base_risk = {}
        if "category_base_risk" in config_dict:
            for category_str, risk in config_dict["category_base_risk"].items():
                try:
                    category = ContentCategory(category_str)
                    category_base_risk[category] = float(risk)
                except (ValueError, TypeError):
                    continue  # Skip invalid categories
        
        content_type_modifiers = {}
        if "content_type_modifiers" in config_dict:
            for content_type, modifier in config_dict["content_type_modifiers"].items():
                try:
                    content_type_modifiers[str(content_type)] = float(modifier)
                except (ValueError, TypeError):
                    continue  # Skip invalid modifiers
        
        return cls(
            category_base_risk=category_base_risk if category_base_risk else cls().category_base_risk,
            content_type_modifiers=content_type_modifiers if content_type_modifiers else cls().content_type_modifiers
        ) 