# Content Scoring System - Detailed Flow Analysis

## Overview
The content scoring system evaluates harmful content across three media types: **Text**, **Image**, and **Audio**. Each type follows a specific calculation flow that considers different factors and weightings.

## Core Constants & Weights

### Content Type Weights
```python
CONTENT_TYPE_WEIGHTS = {
    "text": 1.0,      # Baseline weight
    "image": 1.2,     # 20% higher - visual content has more impact
    "audio": 1.1,     # 10% higher - between text and images
}
```

### Severity Level Base Scores
```python
SEVERITY_SCORES = {
    NONE: 0,          # No harmful content
    LOW: 25,          # Minor violations
    MEDIUM: 50,       # Moderate violations  
    HIGH: 75,         # Serious violations
    CRITICAL: 100     # Extreme violations
}
```

### Category Impact Multipliers
```python
CATEGORY_WEIGHTS = {
    HATE_SPEECH: 1.5,        # Most serious - 50% increase
    HARASSMENT: 1.4,         # Very serious - 40% increase
    SELF_HARM: 1.3,          # Serious - 30% increase
    VIOLENCE: 1.3,           # Serious - 30% increase
    SEXUAL: 1.2,             # Moderate - 20% increase
    MISINFORMATION: 1.1,     # Slight - 10% increase
    SPAM: 0.8,               # Less serious - 20% decrease
    NONE: 0                  # No impact
}
```

---

## 1. TEXT CONTENT SCORING FLOW

### Input: `List[GptTextAnalysisResult]`
Each result contains:
- `is_harmful`: Boolean flag
- `categories`: List of detected content categories
- `severity`: Overall severity level (NONE/LOW/MEDIUM/HIGH/CRITICAL)
- `confidence`: Dict mapping categories to confidence scores (0.0-1.0)
- `explanation`: Human-readable explanation

### Calculation Steps:

#### Step 1: Initialize
```python
max_score = 0  # Track highest score across all text items
```

#### Step 2: Process Each Text Item
```python
for each result in text_results:
    if not result.is_harmful:
        skip to next  # Only process harmful content
```

#### Step 3: Calculate Base Score
```python
severity_score = SEVERITY_SCORES[result.severity]
# Examples:
# LOW = 25, MEDIUM = 50, HIGH = 75, CRITICAL = 100
```

#### Step 4: Apply Category Multiplier
```python
category_multiplier = max(CATEGORY_WEIGHTS[cat] for cat in result.categories)
# Takes the HIGHEST category weight if multiple categories detected
# Example: [HATE_SPEECH, SPAM] → max(1.5, 0.8) = 1.5
```

#### Step 5: Factor in Confidence
```python
confidence_scores = list(result.confidence.values())
avg_confidence = sum(confidence_scores) / len(confidence_scores)
# Average confidence across all detected categories
```

#### Step 6: Calculate Final Item Score
```python
score = severity_score * category_multiplier * avg_confidence
# Example: 75 * 1.5 * 0.85 = 95.625
```

#### Step 7: Track Maximum
```python
max_score = max(max_score, score)
# Keep the highest score across all text items
```

#### Step 8: Finalize
```python
final_score = min(100, max_score)  # Cap at 100
```

### Example Calculation:
- **Text**: "I hate all people from [group]"
- **Severity**: HIGH (75 points)
- **Categories**: [HATE_SPEECH] 
- **Category Weight**: 1.5
- **Confidence**: 0.9
- **Score**: 75 × 1.5 × 0.9 = **101.25** → **100** (capped)

---

## 2. IMAGE CONTENT SCORING FLOW

### Input: `List[ModerationResult]`
Each result contains:
- `is_harmful`: Boolean flag
- `categories`: List of category names (strings)
- `score`: Dict mapping ContentCategory to confidence scores (0.0-1.0)

### Calculation Steps:

#### Step 1: Initialize
```python
max_score = 0  # Track highest score across all images
```

#### Step 2: Process Each Image
```python
for each result in image_results:
    if not result.is_harmful:
        skip to next  # Only process harmful content
```

#### Step 3: Find Highest Category Score
```python
highest_score = max(result.score.values())
# Get the highest confidence score among all categories
# Example: {VIOLENCE: 0.85, HATE_SPEECH: 0.75} → 0.85
```

#### Step 4: Identify Corresponding Category
```python
highest_category = max(result.score.items(), key=lambda x: x[1])[0]
# Get the category with the highest score
# Example: VIOLENCE (from above)
```

#### Step 5: Apply Category Weight
```python
category_weight = CATEGORY_WEIGHTS[highest_category]
# Example: VIOLENCE → 1.3
```

#### Step 6: Calculate Final Score
```python
score = highest_score * 100 * category_weight
# Convert 0-1 scale to 0-100, then apply category weight
# Example: 0.85 * 100 * 1.3 = 110.5
```

#### Step 7: Track Maximum
```python
max_score = max(max_score, score)
```

#### Step 8: Finalize
```python
final_score = min(100, max_score)  # Cap at 100
```

### Example Calculation:
- **Image**: Contains violent content
- **Categories**: {VIOLENCE: 0.85, SEXUAL: 0.30}
- **Highest Score**: 0.85 (VIOLENCE)
- **Category Weight**: 1.3
- **Score**: 0.85 × 100 × 1.3 = **110.5** → **100** (capped)

---

## 3. AUDIO CONTENT SCORING FLOW

### Input: `List[GptTextAnalysisResult]` (same as text, from transcription)
Audio follows the same structure as text but with additional considerations.

### Special Audio Factor:
```python
TRANSCRIPTION_ACCURACY_FACTOR = 0.9
# 10% reduction to account for potential transcription errors
```

### Calculation Steps:

#### Steps 1-4: Same as Text
Follow text flow through severity and category calculations.

#### Step 5: Adjusted Confidence Calculation
```python
confidence_scores = list(result.confidence.values())
avg_confidence = sum(confidence_scores) / len(confidence_scores)

# AUDIO-SPECIFIC ADJUSTMENT
adjusted_confidence = avg_confidence * TRANSCRIPTION_ACCURACY_FACTOR
# Example: 0.9 * 0.9 = 0.81
```

#### Step 6: Calculate Final Score
```python
score = severity_score * category_multiplier * adjusted_confidence
# Note: Uses adjusted_confidence instead of raw confidence
```

#### Steps 7-8: Same as Text
Track maximum and finalize with cap.

### Example Calculation:
- **Audio**: Transcribed hate speech
- **Severity**: HIGH (75 points)
- **Categories**: [HATE_SPEECH]
- **Category Weight**: 1.5
- **Original Confidence**: 0.9
- **Adjusted Confidence**: 0.9 × 0.9 = 0.81
- **Score**: 75 × 1.5 × 0.81 = **91.125**

---

## 4. FINAL CONTENT SCORE AGGREGATION

### Input: Individual scores from each content type

### Steps:

#### Step 1: Apply Content Type Weights
```python
if text_results:
    weighted_text_score = text_score * 1.0

if image_results:
    weighted_image_score = image_score * 1.2

if audio_results:
    weighted_audio_score = audio_score * 1.1
```

#### Step 2: Collect All Weighted Scores
```python
scores = [weighted_text_score, weighted_image_score, weighted_audio_score]
# Only includes scores for content types that were processed
```

#### Step 3: Take Maximum (Not Average!)
```python
final_score = min(100, max(scores))
# Uses MAX to ensure high violations aren't diluted by safe content
```

### Example Final Calculation:
- **Text Score**: 91.0 × 1.0 = 91.0
- **Image Score**: 100.0 × 1.2 = 120.0 → 100.0 (capped)
- **Audio Score**: 91.125 × 1.1 = 100.24 → 100.0 (capped)
- **Final Score**: max(91.0, 100.0, 100.0) = **100.0**

---

## 5. KEY DESIGN DECISIONS

### Maximum vs Average
- **Uses MAX** instead of average to prevent harmful content from being diluted
- One serious violation should trigger high score regardless of other safe content

### Content Type Weights
- **Images weighted highest (1.2)** - visual content often has more immediate impact
- **Audio medium weight (1.1)** - between text and images
- **Text baseline (1.0)** - reference point

### Audio Transcription Adjustment
- **10% confidence reduction** acknowledges speech-to-text errors
- Prevents false positives from transcription mistakes
- More conservative approach for audio content

### Category Hierarchy
- **Hate Speech** weighted highest (1.5) - most serious societal harm
- **Violence/Self-harm** high weight (1.3) - physical safety concerns  
- **Spam** reduced weight (0.8) - less harmful, more annoying

### Score Capping
- **All scores capped at 100** to maintain consistent scale
- Prevents extreme multiplier combinations from breaking the scale

---

## 6. HARMFULNESS THRESHOLD

### Final Decision
```python
is_harmful = content_score >= 25
# Anything scoring 25 or above is considered harmful
# Corresponds to LOW severity baseline
```

This threshold means content needs at least:
- LOW severity + minimal category weight + decent confidence, OR
- Lower severity with high category multipliers, OR  
- Higher confidence compensating for lower severity/category weights 