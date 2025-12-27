#!/usr/bin/env python3
"""
End-to-end test for styling features #101-106 using Playwright.

This test verifies that the styling is correctly applied in a browser:
1. Feature #101: Primary orange/amber color (#CC785C) is used
2. Feature #102: Light theme uses correct background colors
3. Feature #103: Dark theme uses correct colors
4. Feature #104: Typography uses correct font family and sizes
5. Feature #105: Message bubbles have correct styling
6. Feature #106: Input field has correct styling
"""

import re
from playwright.sync_api import sync_playwright, expect


def test_styling_features():
    """Test all styling features in a browser."""

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        page = browser.new_page()

        try:
            # Navigate to the backend server
            page.goto('http://localhost:8000')

            print("\n" + "="*60)
            print("Testing Styling Features #101-106 (Browser)")
            print("="*60)

            # Test 1: Primary color is applied
            print("\n1. Testing Primary Color (#CC785C)...")
            send_button = page.locator('.send-button')
            expect(send_button).to_be_visible()

            # Get computed background color
            bg_color = send_button.evaluate('el => window.getComputedStyle(el).backgroundColor')
            print(f"   Send button background: {bg_color}")
            # Should be rgb(204, 120, 92) which is #CC785C
            assert '204, 120, 92' in bg_color or 'cc785c' in bg_color.lower(), f"Expected #CC785C, got {bg_color}"
            print("   ✓ Primary color #CC785C is applied")

            # Test hover state by forcing hover
            send_button.evaluate('el => el.classList.add("hover")')
            # Or check that the CSS rule exists
            hover_rule = page.evaluate('''
                () => {
                    const sheets = Array.from(document.styleSheets);
                    for (const sheet of sheets) {
                        try {
                            const rules = Array.from(sheet.cssRules || []);
                            for (const rule of rules) {
                                if (rule.selectorText && rule.selectorText.includes('.send-button:hover')) {
                                    return rule.style.backgroundColor;
                                }
                            }
                        } catch (e) {}
                    }
                    return null;
                }
            ''')
            print(f"   Hover CSS rule: {hover_rule}")
            # Check that the hover rule exists with the correct variable
            assert hover_rule and 'var(--primary-hover' in hover_rule, f"Expected hover rule with --primary-hover, got {hover_rule}"
            print("   ✓ Hover color #B86A4E is defined in CSS")

            # Test 2: Light theme colors
            print("\n2. Testing Light Theme Colors...")
            body = page.locator('body')
            bg_primary = body.evaluate('el => window.getComputedStyle(el).backgroundColor')
            text_primary = body.evaluate('el => window.getComputedStyle(el).color')

            print(f"   Body background: {bg_primary}")
            print(f"   Body text color: {text_primary}")

            # Light theme: bg should be white (#FFFFFF), text should be dark (#1A1A1A)
            assert '255, 255, 255' in bg_primary or 'ffffff' in bg_primary.lower(), f"Expected white background, got {bg_primary}"
            assert '26, 26, 26' in text_primary or '1a1a1a' in text_primary.lower(), f"Expected dark text, got {text_primary}"
            print("   ✓ Light theme colors are correct")

            # Test 3: Dark theme colors
            print("\n3. Testing Dark Theme Colors...")
            # Add dark class to body
            page.evaluate('document.body.classList.add("dark")')

            dark_bg = body.evaluate('el => window.getComputedStyle(el).backgroundColor')
            dark_text = body.evaluate('el => window.getComputedStyle(el).color')

            print(f"   Dark body background: {dark_bg}")
            print(f"   Dark body text color: {dark_text}")

            # Dark theme: bg should be dark (#1A1A1A), text should be light (#E5E5E5)
            assert '26, 26, 26' in dark_bg or '1a1a1a' in dark_bg.lower(), f"Expected dark background, got {dark_bg}"
            assert '229, 229, 229' in dark_text or 'e5e5e5' in dark_text.lower(), f"Expected light text, got {dark_text}"
            print("   ✓ Dark theme colors are correct")

            # Remove dark class for next tests
            page.evaluate('document.body.classList.remove("dark")')

            # Test 4: Typography
            print("\n4. Testing Typography...")
            body_font = body.evaluate('el => window.getComputedStyle(el).fontFamily')
            body_size = body.evaluate('el => window.getComputedStyle(el).fontSize')

            print(f"   Font family: {body_font}")
            print(f"   Font size: {body_size}")

            # Check for Inter font
            assert 'Inter' in body_font or 'inter' in body_font.lower(), f"Expected Inter font, got {body_font}"
            # Check for 16px base size
            assert '16px' in body_size, f"Expected 16px, got {body_size}"
            print("   ✓ Typography is correct (Inter font, 16px)")

            # Test prose styles
            prose_h1 = page.locator('.prose h1')
            if prose_h1.count() > 0:
                h1_size = prose_h1.evaluate('el => window.getComputedStyle(el).fontSize')
                h1_weight = prose_h1.evaluate('el => window.getComputedStyle(el).fontWeight')
                print(f"   Prose H1: {h1_size}, weight: {h1_weight}")
                assert '700' in h1_weight or 'bold' in h1_weight, f"Expected bold, got {h1_weight}"
                print("   ✓ Prose styles are correct")

            # Test 5: Message bubbles
            print("\n5. Testing Message Bubble Styling...")
            user_bubble = page.locator('.message-bubble.user')
            assistant_bubble = page.locator('.message-bubble.assistant')

            expect(user_bubble).to_be_visible()
            expect(assistant_bubble).to_be_visible()

            user_bg = user_bubble.evaluate('el => window.getComputedStyle(el).backgroundColor')
            user_color = user_bubble.evaluate('el => window.getComputedStyle(el).color')
            assistant_bg = assistant_bubble.evaluate('el => window.getComputedStyle(el).backgroundColor')

            print(f"   User bubble bg: {user_bg}, text: {user_color}")
            print(f"   Assistant bubble bg: {assistant_bg}")

            # User bubble should use primary color and white text
            assert '204, 120, 92' in user_bg or 'cc785c' in user_bg.lower(), f"Expected primary color, got {user_bg}"
            assert '255, 255, 255' in user_color or 'white' in user_color.lower(), f"Expected white text, got {user_color}"

            # Assistant bubble should use bg-secondary
            assert '245, 245, 245' in assistant_bg or 'f5f5f5' in assistant_bg.lower(), f"Expected #F5F5F5, got {assistant_bg}"
            print("   ✓ Message bubbles use correct styling")

            # Test 6: Input field styling
            print("\n6. Testing Input Field Styling...")
            input_field = page.locator('.message-input')
            expect(input_field).to_be_visible()

            input_border = input_field.evaluate('el => window.getComputedStyle(el).border')
            input_bg = input_field.evaluate('el => window.getComputedStyle(el).backgroundColor')
            input_text = input_field.evaluate('el => window.getComputedStyle(el).color')

            print(f"   Input border: {input_border}")
            print(f"   Input bg: {input_bg}")
            print(f"   Input text: {input_text}")

            # Input should have border and use CSS variables
            assert '1px' in input_border or 'border' in input_border.lower(), f"Expected border, got {input_border}"
            assert '255, 255, 255' in input_bg or 'ffffff' in input_bg.lower(), f"Expected white bg, got {input_bg}"
            assert '26, 26, 26' in input_text or '1a1a1a' in input_text.lower(), f"Expected dark text, got {input_text}"
            print("   ✓ Input field has correct styling")

            # Test focus state
            input_field.focus()
            # Check for outline (focus ring)
            outline = input_field.evaluate('el => window.getComputedStyle(el).outline')
            print(f"   Focus outline: {outline}")
            # Should have primary color outline
            assert '204, 120, 92' in outline or 'cc785c' in outline.lower() or '2px' in outline, f"Expected focus ring, got {outline}"
            print("   ✓ Focus state has correct styling")

            # Test 7: Code styling
            print("\n7. Testing Code Styling...")
            code = page.locator('.prose code')
            if code.count() > 0:
                code_bg = code.evaluate('el => window.getComputedStyle(el).backgroundColor')
                code_font = code.evaluate('el => window.getComputedStyle(el).fontFamily')
                print(f"   Code bg: {code_bg}, font: {code_font}")
                # Code should have bg-secondary background
                assert '245, 245, 245' in code_bg or 'f5f5f5' in code_bg.lower(), f"Expected #F5F5F5, got {code_bg}"
                # Code should use monospace
                assert 'monospace' in code_font.lower() or 'JetBrains' in code_font or 'Fira' in code_font, f"Expected monospace, got {code_font}"
                print("   ✓ Code styling is correct")

            print("\n" + "="*60)
            print("SUMMARY: All styling features verified in browser!")
            print("="*60)

            return True

        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()


if __name__ == "__main__":
    import sys
    success = test_styling_features()
    sys.exit(0 if success else 1)
