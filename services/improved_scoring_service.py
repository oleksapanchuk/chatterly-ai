import math
from datetime import datetime
from typing import List, Optional, Tuple

from shared.gpt_text_analysis_result import GptTextAnalysisResult
from shared.logger_config import get_logger
from shared.moderation_result import ModerationResult
from shared.scoring_configuration import ScoringConfiguration
from shared.user_reputation import UserReputation, UserReputationLevel
from shared.validation_types import ContentCategory


class ImprovedScoringService:
    """
    Improved probabilistic scoring service that addresses mathematical flaws
    in the original severity-based system.
    """

    def __init__(self, scoring_config: Optional[ScoringConfiguration] = None):
        self.logger = get_logger(__name__)
        self.scoring_config = scoring_config or ScoringConfiguration.get_default_configuration()
        self.logger.info("ImprovedScoringService initialized")
        self.logger.debug(f"Using scoring configuration: {self.scoring_config.to_dict()}")

    def confidence_adjusted_risk(self, base_risk: float, confidence: float) -> float:
        """
        Apply probabilistic confidence adjustment.
        High confidence → closer to base_risk
        Low confidence → pulls toward neutral (50)
        """
        return base_risk * confidence + 50 * (1 - confidence)

    def multi_category_penalty(self, num_categories: int) -> float:
        """
        Apply logarithmic compounding for multiple category violations.
        """
        if num_categories <= 1:
            return 0
        return min(12, 4 * math.log2(num_categories))

    def audio_confidence_degradation(self, original_confidence: float) -> float:
        """
        Dynamic confidence degradation for audio content based on transcription uncertainty.
        Higher confidence degrades less, lower confidence degrades more.
        """
        degradation_factor = 0.05 + 0.10 * (1 - original_confidence)
        return max(0.1, original_confidence - degradation_factor)

    def calculate_category_score(self, category: ContentCategory, confidence: float,
                                 content_type: str, is_audio: bool = False) -> float:
        """
        Calculate score for individual category detection.
        """
        # 1. Get base risk for this category from configuration
        base_risk = self.scoring_config.get_category_base_risk(category)

        # 2. Adjust confidence for audio content
        if is_audio:
            confidence = self.audio_confidence_degradation(confidence)
            self.logger.debug(f"Audio confidence degraded to {confidence:.3f} for {category.value}")

        # 3. Apply probabilistic confidence adjustment
        adjusted_risk = self.confidence_adjusted_risk(base_risk, confidence)

        # 4. Add content type modifier from configuration
        content_modifier = self.scoring_config.get_content_type_modifier(content_type)
        final_score = min(100, adjusted_risk + content_modifier)

        self.logger.debug(f"Category {category.value}: base_risk={base_risk}, "
                          f"confidence={confidence:.3f}, adjusted_risk={adjusted_risk:.2f}, "
                          f"modifier={content_modifier}, final_score={final_score:.2f}")

        return final_score

    def calculate_content_item_score(self, categories_and_confidences: List[Tuple[ContentCategory, float]],
                                     content_type: str, is_audio: bool = False) -> float:
        """
        Calculate score for a single content item (text/image/audio piece).
        """
        if not categories_and_confidences:
            return 0

        # Calculate individual category scores
        category_scores = []
        for category, confidence in categories_and_confidences:
            score = self.calculate_category_score(category, confidence, content_type, is_audio)
            category_scores.append(score)

        if not category_scores:
            return 0

        # Take maximum score as primary violation
        primary_score = max(category_scores)

        # Apply multi-category penalty for multiple violations
        multi_penalty = self.multi_category_penalty(len(category_scores))

        # Final item score
        final_score = min(100, primary_score + multi_penalty)

        self.logger.debug(f"Content item ({content_type}): primary_score={primary_score:.2f}, "
                          f"multi_penalty={multi_penalty:.2f}, final_score={final_score:.2f}")

        return final_score

    def calculate_final_content_score(self, all_item_scores: List[float]) -> float:
        """
        Aggregate scores across all content items using weighted combination.
        """
        if not all_item_scores:
            return 0

        # Filter out zero scores and sort in descending order
        non_zero_scores = [score for score in all_item_scores if score > 0]
        if not non_zero_scores:
            return 0

        sorted_scores = sorted(non_zero_scores, reverse=True)

        if len(sorted_scores) == 1:
            return sorted_scores[0]

        # Primary violation gets full weight
        # Secondary violations get diminishing weights
        weighted_sum = sorted_scores[0]

        for i, score in enumerate(sorted_scores[1:], 1):
            weight = 0.3 / i  # Diminishing: 0.3, 0.15, 0.1, 0.075...
            weighted_sum += score * weight
            self.logger.debug(f"Secondary violation {i}: score={score:.2f}, weight={weight:.3f}")

        final_score = min(100, weighted_sum)
        self.logger.info(f"Final aggregated score: {final_score:.2f} from {len(sorted_scores)} violations")

        return final_score

    def calculate_content_score(self,
                                text_results: Optional[List[GptTextAnalysisResult]] = None,
                                image_results: Optional[List[ModerationResult]] = None,
                                audio_results: Optional[List[GptTextAnalysisResult]] = None) -> float:
        """
        Calculate overall content score using the improved probabilistic model.
        """
        self.logger.info("Starting improved content score calculation")
        self.logger.debug(f"Input counts - Text: {len(text_results) if text_results else 0}, "
                          f"Image: {len(image_results) if image_results else 0}, "
                          f"Audio: {len(audio_results) if audio_results else 0}")

        all_item_scores = []

        # Process text results
        if text_results:
            for i, result in enumerate(text_results):
                if result.is_harmful and result.categories:
                    categories_and_confidences = [
                        (category, result.confidence.get(category, 0.0))
                        for category in result.categories
                    ]
                    score = self.calculate_content_item_score(categories_and_confidences, "text", False)
                    if score > 0:
                        all_item_scores.append(score)
                        self.logger.debug(f"Text item {i + 1} score: {score:.2f}")

        # Process image results
        if image_results:
            for i, result in enumerate(image_results):
                if result.is_harmful and result.score:
                    # Convert image results to category-confidence pairs
                    categories_and_confidences = [
                        (category, confidence)
                        for category, confidence in result.score.items()
                        if confidence >= 0.7  # Only include high-confidence detections
                    ]
                    if categories_and_confidences:
                        score = self.calculate_content_item_score(categories_and_confidences, "image", False)
                        if score > 0:
                            all_item_scores.append(score)
                            self.logger.debug(f"Image item {i + 1} score: {score:.2f}")

        # Process audio results
        if audio_results:
            for i, result in enumerate(audio_results):
                if result.is_harmful and result.categories:
                    categories_and_confidences = [
                        (category, result.confidence.get(category, 0.0))
                        for category in result.categories
                    ]
                    score = self.calculate_content_item_score(categories_and_confidences, "audio", True)
                    if score > 0:
                        all_item_scores.append(score)
                        self.logger.debug(f"Audio item {i + 1} score: {score:.2f}")

        # Calculate final aggregated score
        final_score = self.calculate_final_content_score(all_item_scores)

        self.logger.info(f"Improved scoring calculation complete. Final score: {final_score:.2f}")
        return final_score

    def update_user_reputation(self,
                               user_reputation: UserReputation,
                               content_score: float,
                               violation_details: Optional[dict] = None) -> UserReputation:
        """
        Update user reputation based on improved content score.
        """
        self.logger.info(f"Updating user reputation. Current score: {user_reputation.reputation_score}, "
                         f"Content score: {content_score}")

        # Record violation if content is harmful
        if content_score > 0 and violation_details:
            violation_details["timestamp"] = datetime.utcnow()
            user_reputation.violation_history.append(violation_details)
            self.logger.warning(f"Violation recorded. Total violations: {len(user_reputation.violation_history)}")

        # Calculate reputation impact using improved scoring
        impact = self._calculate_reputation_impact(content_score, len(user_reputation.violation_history))
        new_score = max(0, min(100, user_reputation.reputation_score - impact))

        # Update reputation
        old_level = user_reputation.reputation_level
        user_reputation.reputation_score = new_score
        user_reputation.reputation_level = self._get_reputation_level(new_score)
        user_reputation.last_updated = datetime.utcnow()

        if old_level != user_reputation.reputation_level:
            self.logger.warning(
                f"User reputation level changed from {old_level.value} to {user_reputation.reputation_level.value}")

        # Check if user should be banned
        self._update_ban_status(user_reputation)

        return user_reputation

    def _calculate_reputation_impact(self, content_score: float, violation_count: int) -> float:
        """
        Calculate reputation impact using improved scoring logic.
        """
        # Base impact scales with content score more smoothly
        base_impact = content_score * 0.6  # 60% of content score affects reputation

        # Escalating penalty for repeat offenders (logarithmic)
        repeat_multiplier = 1.0 + (0.2 * math.log2(max(1, violation_count)))

        total_impact = base_impact * repeat_multiplier
        self.logger.debug(f"Reputation impact: base={base_impact:.2f}, "
                          f"repeat_multiplier={repeat_multiplier:.2f}, total={total_impact:.2f}")

        return min(50, total_impact)  # Cap impact at 50 points

    def _get_reputation_level(self, score: float) -> UserReputationLevel:
        """Get reputation level based on score."""
        if score >= 80:
            return UserReputationLevel.EXCELLENT
        elif score >= 60:
            return UserReputationLevel.GOOD
        elif score >= 40:
            return UserReputationLevel.FAIR
        elif score >= 20:
            return UserReputationLevel.POOR
        else:
            return UserReputationLevel.TERRIBLE

    def _update_ban_status(self, user_reputation: UserReputation):
        """Update ban status based on reputation and violations."""
        # More sophisticated ban logic
        if (user_reputation.reputation_score <= 10 and
                len(user_reputation.violation_history) >= 3):
            user_reputation.is_banned = True
            self.logger.warning("User banned due to low reputation and multiple violations")
        elif (len(user_reputation.violation_history) >= 5 and
              user_reputation.reputation_score <= 25):
            user_reputation.is_banned = True
            self.logger.warning("User banned due to excessive violations")
