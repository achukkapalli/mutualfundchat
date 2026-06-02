import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.validator import OutputValidator

def test_pii_redaction():
    validator = OutputValidator()
    
    # Test PAN
    assert "[REDACTED_PAN]" in validator.redact_pii("My PAN number is ABCDE1234Z.")
    assert "[REDACTED_PAN]" in validator.redact_pii("PAN: abcde5678a")
    
    # Test Aadhaar
    assert "[REDACTED_AADHAAR]" in validator.redact_pii("My Aadhaar is 2345 6789 0123.")
    assert "[REDACTED_AADHAAR]" in validator.redact_pii("Aadhaar: 999988887777")
    
    # Test Email
    assert "[REDACTED_EMAIL]" in validator.redact_pii("Send email to contact@hdfc.com.")
    
    # Test Phone
    assert "[REDACTED_PHONE]" in validator.redact_pii("Call me at 9876543210.")
    assert "[REDACTED_PHONE]" in validator.redact_pii("Mobile: +91 7001234567")
    
    # Test OTP
    assert "[REDACTED_OTP]" in validator.redact_pii("Your OTP is 4839.")
    assert "[REDACTED_OTP]" in validator.redact_pii("Verification code 928374 is active.")
    assert "123456" in validator.redact_pii("The fund size is 123456 Cr.")  # Normal numbers should not be redacted
    
    print(">>> PII Redaction Tests Passed!")

def test_sentence_enforcement():
    validator = OutputValidator()
    
    # 4 sentences, link in the 4th
    text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four [Groww Link](https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth)."
    truncated = validator.enforce_sentence_limit(text)
    
    # Sentence count should be exactly 3
    sentences = validator.count_sentences(truncated)
    assert len(sentences) == 3, f"Expected 3 sentences, got {len(sentences)}"
    # Link should be preserved and appended
    assert "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth" in truncated, "Link was lost during sentence truncation"
    
    # Text with 2 sentences should remain unchanged
    short_text = "Sentence one. Sentence two [Link](url)."
    assert validator.enforce_sentence_limit(short_text) == short_text
    
    print(">>> Sentence Enforcement Tests Passed!")

def test_link_validation():
    validator = OutputValidator()
    fallback = "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
    
    # Case 1: No link
    text_no_link = "The expense ratio is 0.73%."
    corrected_no_link = validator.validate_and_correct_link(text_no_link, fallback)
    assert fallback in corrected_no_link, "Failed to append fallback link"
    
    # Case 2: Invalid link
    text_invalid_link = "The exit load is 1% [Groww](https://google.com/invalid)."
    corrected_invalid_link = validator.validate_and_correct_link(text_invalid_link, fallback)
    assert "https://google.com/invalid" not in corrected_invalid_link, "Invalid link was not replaced"
    assert fallback in corrected_invalid_link, "Fallback link not substituted"
    
    # Case 3: Multiple links (one valid, one invalid)
    valid_url = "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth"
    text_mult_links = f"See [Defence Scheme]({valid_url}) and [Google](https://google.com)."
    corrected_mult = validator.validate_and_correct_link(text_mult_links, fallback)
    assert valid_url in corrected_mult, "Valid link was removed"
    assert "https://google.com" not in corrected_mult, "Invalid second link was not cleaned"
    assert "Google" in corrected_mult, "Link text of second link was lost"
    
    print(">>> Link Validation Tests Passed!")

def test_footer_injection():
    validator = OutputValidator()
    text = "The fund manager is Chirag Setalvad [Link](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth)."
    
    final_output = validator.validate_pipeline(text, retrieved_chunks=[], fallback_url="https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth")
    
    # Verify footer is appended
    assert "Last updated from sources" in final_output
    print(">>> Footer Injection Tests Passed!")

if __name__ == "__main__":
    try:
        test_pii_redaction()
        test_sentence_enforcement()
        test_link_validation()
        test_footer_injection()
        print("\nAll OutputValidator tests passed successfully!")
    except AssertionError as e:
        print(f"\nAssertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        sys.exit(1)
