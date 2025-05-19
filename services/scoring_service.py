from datetime import datetime, timedelta
from typing import List, Optional

from shared.gpt_text_analysis_result import GptTextAnalysisResult
from shared.moderation_result import ModerationResult
from shared.user_reputation import UserReputation, UserReputationLevel, UserBanStatus
from shared.validation_types import ContentCategory, SeverityLevel


class ScoringService:
    # Weights for different content types
    CONTENT_TYPE_WEIGHTS = {
        "text": 1.0,
        "image": 1.2,  # Images weighted slightly higher due to potential impact
        "audio": 1.1,  # Audio weighted between text and images
    }

    # Base scores for different severity levels
    SEVERITY_SCORES = {
        SeverityLevel.NONE: 0,
        SeverityLevel.LOW: 25,
        SeverityLevel.MEDIUM: 50,
        SeverityLevel.HIGH: 75,
        SeverityLevel.CRITICAL: 100
    }

    # Category weights for reputation impact
    CATEGORY_WEIGHTS = {
        ContentCategory.HATE_SPEECH: 1.5,
        ContentCategory.HARASSMENT: 1.4,
        ContentCategory.SELF_HARM: 1.3,
        ContentCategory.SEXUAL: 1.2,
        ContentCategory.VIOLENCE: 1.3,
        ContentCategory.MISINFORMATION: 1.1,
        ContentCategory.SPAM: 0.8,
        ContentCategory.NONE: 0
    }

    def calculate_content_score(
            self,
            text_results: Optional[List[GptTextAnalysisResult]] = None,
            image_results: Optional[List[ModerationResult]] = None,
            audio_results: Optional[List[GptTextAnalysisResult]] = None
    ) -> float:
        """Calculate overall content score based on all content types."""
        scores = []

        if text_results:
            text_score = self._calculate_text_score(text_results)
            scores.append(text_score * self.CONTENT_TYPE_WEIGHTS["text"])

        if image_results:
            image_score = self._calculate_image_score(image_results)
            scores.append(image_score * self.CONTENT_TYPE_WEIGHTS["image"])

        if audio_results:
            audio_score = self._calculate_text_score(audio_results)  # Audio uses same logic as text
            scores.append(audio_score * self.CONTENT_TYPE_WEIGHTS["audio"])

        if not scores:
            return 0

        # Use the maximum score instead of average to ensure high severity violations aren't diluted
        return min(100, max(scores))

    def _calculate_text_score(self, results: List[GptTextAnalysisResult]) -> float:
        """Calculate score for text content."""
        if not results:
            return 0

        max_score = 0
        for result in results:
            if not result.is_harmful:
                continue

            # Base score from severity
            severity_score = self.SEVERITY_SCORES[result.severity]

            # Apply category weights
            category_multiplier = max(
                self.CATEGORY_WEIGHTS[cat] for cat in result.categories
            )

            # Factor in confidence
            confidence_scores = list(result.confidence.values())
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5

            score = severity_score * category_multiplier * avg_confidence
            max_score = max(max_score, score)

        return min(100, max_score)

    def _calculate_image_score(self, results: List[ModerationResult]) -> float:
        """Calculate score for image content."""
        if not results:
            return 0

        max_score = 0
        for result in results:
            if not result.is_harmful:
                continue

            # For images, we directly use the highest category score as the base
            highest_score = max(result.score.values(), default=0.0)
            # Convert to 0-100 scale and apply the highest category weight
            highest_category = max(result.score.items(), key=lambda x: x[1])[0] if result.score else ContentCategory.NONE
            category_weight = self.CATEGORY_WEIGHTS[highest_category]
            
            score = highest_score * 100 * category_weight
            max_score = max(max_score, score)

        return min(100, max_score)

    def update_user_reputation(
            self,
            user_reputation: UserReputation,
            content_score: float,
            violation_details: Optional[dict] = None
    ) -> UserReputation:
        """Update user reputation based on content score."""
        # Record violation if content is harmful
        if content_score > 0 and violation_details:
            violation_details["timestamp"] = datetime.utcnow()
            user_reputation.violation_history.append(violation_details)

        # Calculate reputation impact
        impact = self._calculate_reputation_impact(content_score, len(user_reputation.violation_history))
        new_score = max(0, min(100, user_reputation.reputation_score - impact))

        # Update reputation
        user_reputation.reputation_score = new_score
        user_reputation.reputation_level = self._get_reputation_level(new_score)
        user_reputation.last_updated = datetime.utcnow()

        # Check if ban is needed
        self._update_ban_status(user_reputation)

        return user_reputation

    def _calculate_reputation_impact(self, content_score: float, violation_count: int) -> float:
        """Calculate impact on reputation score."""
        # Base impact is proportional to content score
        base_impact = content_score / 10  # A score of 100 results in -10 reputation

        # Multiply impact based on violation history
        history_multiplier = 1 + (violation_count * 0.2)  # Each violation increases impact by 20%

        return base_impact * history_multiplier

    def _get_reputation_level(self, score: float) -> UserReputationLevel:
        """Get reputation level based on score."""
        if score > 90:
            return UserReputationLevel.EXCELLENT
        elif score > 70:
            return UserReputationLevel.GOOD
        elif score > 40:
            return UserReputationLevel.NEUTRAL
        elif score > 20:
            return UserReputationLevel.WARNING
        else:
            return UserReputationLevel.PROBLEMATIC

    def _update_ban_status(self, user_reputation: UserReputation):
        """Update user ban status based on reputation and violation history."""
        if user_reputation.ban_status != UserBanStatus.NONE:
            # Check if temporary ban has expired
            if (user_reputation.ban_status == UserBanStatus.TEMPORARY and
                    user_reputation.ban_end_date and
                    user_reputation.ban_end_date < datetime.utcnow()):
                user_reputation.ban_status = UserBanStatus.NONE
                user_reputation.ban_end_date = None
            return

        recent_violations = [
            v for v in user_reputation.violation_history
            if v["timestamp"] > datetime.utcnow() - timedelta(days=30)
        ]

        # Permanent ban conditions
        if (user_reputation.reputation_score < 10 or
                len(recent_violations) >= 10 or
                any(v.get("severity") == SeverityLevel.CRITICAL for v in recent_violations)):
            user_reputation.ban_status = UserBanStatus.PERMANENT
            return

        # Temporary ban conditions
        if (user_reputation.reputation_score < 20 or
                len(recent_violations) >= 5 or
                any(v.get("severity") == SeverityLevel.HIGH for v in recent_violations)):
            user_reputation.ban_status = UserBanStatus.TEMPORARY
            user_reputation.ban_end_date = datetime.utcnow() + timedelta(days=7)  # 7-day ban
