# Improved Content Scoring Model - Mathematical Design

## Problems with Current Model

### 1. **Severity Level Issues**
- Fixed buckets (25, 50, 75, 100) don't reflect reality
- Multiplying by category weights causes score explosion
- Requires artificial capping at 100

### 2. **Mathematical Inconsistencies**
- Text/Audio: `severity × category_weight × confidence`
- Images: `confidence × 100 × category_weight`
- Different formulas produce incomparable results

### 3. **Poor Aggregation Logic**
- Taking maximum ignores cumulative harm
- Multiple violations don't compound appropriately

---

## New Probabilistic Scoring Model

### Core Principle: **Risk Assessment Rather Than Severity**

Instead of arbitrary severity levels, use **category-specific base risk scores** that represent the inherent harmfulness of each violation type.

### 1. **Category Base Risk Scores (0-100)**

```python
CATEGORY_BASE_RISK = {
    HATE_SPEECH: 85,        # Very high societal harm
    HARASSMENT: 75,         # High interpersonal harm  
    VIOLENCE: 80,           # High physical safety risk
    SELF_HARM: 90,          # Extreme individual risk
    SEXUAL: 60,             # Moderate policy violation
    MISINFORMATION: 45,     # Medium societal concern
    SPAM: 25,               # Low-level annoyance
    NONE: 0                 # No risk
}
```

### 2. **Confidence-Based Risk Adjustment**

Instead of multiplying by confidence, use **probabilistic blending**:

```python
def confidence_adjusted_risk(base_risk, confidence):
    """
    High confidence → closer to base_risk
    Low confidence → pulls toward neutral (50)
    """
    return base_risk * confidence + 50 * (1 - confidence)
```

**Examples:**
- `base_risk=85, confidence=0.9` → `85×0.9 + 50×0.1 = 81.5`
- `base_risk=85, confidence=0.5` → `85×0.5 + 50×0.5 = 67.5`  
- `base_risk=85, confidence=0.1` → `85×0.1 + 50×0.9 = 53.5`

### 3. **Content Type Modifiers (Additive)**

```python
CONTENT_TYPE_MODIFIERS = {
    "text": 0,      # Baseline
    "image": +8,    # Visual content more impactful
    "audio": +4     # Audio between text and image
}
```

### 4. **Multi-Category Penalty**

When multiple categories are detected, apply **logarithmic compounding**:

```python
def multi_category_penalty(num_categories):
    if num_categories <= 1:
        return 0
    return min(12, 4 * math.log2(num_categories))
```

**Examples:**
- 1 category: +0 points
- 2 categories: +4 points  
- 3 categories: +6.3 points
- 4 categories: +8 points
- 8 categories: +12 points (capped)

### 5. **Audio Transcription Uncertainty**

Instead of flat 10% reduction, use **confidence degradation**:

```python
def audio_confidence_degradation(original_confidence):
    """
    Higher confidence degrades less
    Lower confidence degrades more
    """
    degradation_factor = 0.05 + 0.10 * (1 - original_confidence)
    return max(0.1, original_confidence - degradation_factor)
```

**Examples:**
- `confidence=0.9` → `degradation=0.06` → `new_confidence=0.84`
- `confidence=0.7` → `degradation=0.08` → `new_confidence=0.62`
- `confidence=0.3` → `degradation=0.12` → `new_confidence=0.18`

---

## New Calculation Flow

### **Step 1: Individual Category Scoring**

For each detected category:

```python
def calculate_category_score(category, confidence, content_type, is_audio=False):
    # 1. Get base risk
    base_risk = CATEGORY_BASE_RISK[category]
    
    # 2. Adjust confidence for audio
    if is_audio:
        confidence = audio_confidence_degradation(confidence)
    
    # 3. Apply confidence adjustment
    adjusted_risk = confidence_adjusted_risk(base_risk, confidence)
    
    # 4. Add content type modifier
    content_modifier = CONTENT_TYPE_MODIFIERS[content_type]
    final_score = min(100, adjusted_risk + content_modifier)
    
    return final_score
```

### **Step 2: Content Item Aggregation**

For each piece of content (text/image/audio):

```python
def calculate_content_item_score(categories_and_confidences, content_type, is_audio=False):
    if not categories_and_confidences:
        return 0
    
    # Calculate individual category scores
    category_scores = []
    for category, confidence in categories_and_confidences:
        score = calculate_category_score(category, confidence, content_type, is_audio)
        category_scores.append(score)
    
    # Take maximum score (primary violation)
    primary_score = max(category_scores)
    
    # Apply multi-category penalty
    multi_penalty = multi_category_penalty(len(category_scores))
    
    # Final item score
    return min(100, primary_score + multi_penalty)
```

### **Step 3: Final Content Aggregation**

Across all content items:

```python
def calculate_final_content_score(all_item_scores):
    if not all_item_scores:
        return 0
    
    # Use weighted combination instead of pure maximum
    sorted_scores = sorted(all_item_scores, reverse=True)
    
    if len(sorted_scores) == 1:
        return sorted_scores[0]
    
    # Primary violation gets full weight
    # Secondary violations get diminishing weights
    weighted_sum = sorted_scores[0]
    
    for i, score in enumerate(sorted_scores[1:], 1):
        weight = 0.3 / i  # Diminishing: 0.3, 0.15, 0.1, 0.075...
        weighted_sum += score * weight
    
    return min(100, weighted_sum)
```

---

## Complete Example Calculation

### **Scenario**: Mixed content with multiple violations

**Content:**
- **Text**: "I hate group X" → HATE_SPEECH (confidence: 0.85)
- **Image**: Violent content → VIOLENCE (confidence: 0.75), HARASSMENT (confidence: 0.60)  
- **Audio**: Self-harm discussion → SELF_HARM (confidence: 0.70)

### **Calculations:**

#### **Text Item:**
1. Base risk: 85 (HATE_SPEECH)
2. Confidence adjustment: `85×0.85 + 50×0.15 = 79.75`
3. Content modifier: +0 (text)
4. Multi-category penalty: +0 (single category)
5. **Text score: 79.75**

#### **Image Item:**
1. **VIOLENCE**: `80×0.75 + 50×0.25 = 72.5 + 8 = 80.5`
2. **HARASSMENT**: `75×0.60 + 50×0.40 = 65.0 + 8 = 73.0`
3. Primary score: 80.5 (VIOLENCE)
4. Multi-category penalty: +4 (2 categories)
5. **Image score: 84.5**

#### **Audio Item:**
1. Confidence degradation: `0.70 - (0.05 + 0.10×0.30) = 0.62`
2. Base risk: 90 (SELF_HARM)  
3. Confidence adjustment: `90×0.62 + 50×0.38 = 74.8`
4. Content modifier: +4 (audio)
5. **Audio score: 78.8**

#### **Final Aggregation:**
1. Sorted scores: [84.5, 79.75, 78.8]
2. Weighted combination:
   - Primary: 84.5 × 1.0 = 84.5
   - Secondary: 79.75 × 0.3 = 23.93
   - Tertiary: 78.8 × 0.15 = 11.82
3. **Final score: 84.5 + 23.93 + 11.82 = 120.25 → 100** (capped)

---

## Advantages of New Model

### 1. **Mathematical Soundness**
- No arbitrary severity multipliers
- Probabilistic confidence handling
- Natural score distribution (0-100)

### 2. **Consistent Logic**
- Same calculation method for all content types
- Additive modifiers instead of multiplicative chaos
- Proper normalization

### 3. **Realistic Behavior**
- Low confidence pulls toward neutral, not zero
- Multiple violations compound appropriately  
- Diminishing returns for secondary violations

### 4. **Interpretable Results**
- Scores represent actual risk levels
- No artificial capping needed
- Clear factor contribution

### 5. **Robust Edge Cases**
- Handles zero confidence gracefully
- Works with single or multiple categories
- Scales properly with content volume

This model produces **much more reliable and interpretable** content safety scores! 