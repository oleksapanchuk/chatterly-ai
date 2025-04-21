from content_moderation_service import ContentModerationService

def test_content_moderation():
    # Create an instance of the ContentModerationService
    moderation_service = ContentModerationService()
    
    # Example texts to analyze
    safe_text = "Hello! I'm excited to chat with you about our new project."
    potentially_harmful_text = "I can't stand those people. They're all terrible and should be banned."
    
    # # Analyze the safe text
    # print("Analyzing safe text...")
    safe_result = moderation_service.analyze_content(safe_text)
    # print(f"Is harmful: {safe_result.is_harmful}")
    # print(f"Severity: {safe_result.severity}")
    # print(f"Categories: {safe_result.categories}")
    # print(f"Recommendation: {safe_result.recommendation}")
    # print()
    #
    # # Analyze the potentially harmful text
    # print("Analyzing potentially harmful text...")
    harmful_result = moderation_service.analyze_content(potentially_harmful_text)
    # print(f"Is harmful: {harmful_result.is_harmful}")
    # print(f"Severity: {harmful_result.severity}")
    # print(f"Categories: {harmful_result.categories}")
    # print(f"Recommendation: {harmful_result.recommendation}")
    # print()
    #
    # # Use the convenience method to check if content is safe
    # print(f"Is safe text safe? {moderation_service.is_content_safe(safe_text)}")
    # print(f"Is potentially harmful text safe? {moderation_service.is_content_safe(potentially_harmful_text)}")

    print(safe_result)
    print()

    print(harmful_result)
    print()

if __name__ == "__main__":
    test_content_moderation()