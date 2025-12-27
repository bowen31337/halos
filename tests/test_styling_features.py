"""Test styling features for features #101-105.

This test file verifies that the CSS styling is correctly implemented
for the application's visual design.
"""

import re
from pathlib import Path


def test_primary_color_is_correct():
    """Feature #101: Application uses correct primary orange/amber color (#CC785C).

    Steps:
    1. Verify --primary is #CC785C
    2. Verify --primary-hover is #B86A4E
    3. Verify --primary-active is #A35D42
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Check primary color
    assert re.search(r'--primary:\s*#CC785C', css_content), "Primary color should be #CC785C"
    assert re.search(r'--primary-hover:\s*#B86A4E', css_content), "Primary hover should be #B86A4E"
    assert re.search(r'--primary-active:\s*#A35D42', css_content), "Primary active should be #A35D42"

    print("✅ Feature #101: Primary colors are correct")


def test_light_theme_colors():
    """Feature #102: Light theme uses correct background colors.

    Steps:
    1. Verify main background is white (#FFFFFF)
    2. Verify sidebar uses light gray (#F5F5F5)
    3. Verify elevated surfaces use (#FAFAFA)
    4. Verify text is near-black (#1A1A1A)
    5. Verify borders are light gray (#E5E5E5)
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Extract :root section (light theme)
    root_match = re.search(r':root\s*\{([^}]+)\}', css_content, re.DOTALL)
    assert root_match, "Could not find :root CSS block"
    root_content = root_match.group(1)

    assert re.search(r'--bg-primary:\s*#FFFFFF', root_content), "Light bg-primary should be #FFFFFF"
    assert re.search(r'--bg-secondary:\s*#F5F5F5', root_content), "Light bg-secondary should be #F5F5F5"
    assert re.search(r'--bg-elevated:\s*#FAFAFA', root_content), "Light bg-elevated should be #FAFAFA"
    assert re.search(r'--surface-elevated:\s*#FAFAFA', root_content), "Light surface-elevated should be #FAFAFA"
    assert re.search(r'--text-primary:\s*#1A1A1A', root_content), "Light text-primary should be #1A1A1A"
    assert re.search(r'--border-primary:\s*#E5E5E5', root_content), "Light border-primary should be #E5E5E5"

    print("✅ Feature #102: Light theme colors are correct")


def test_dark_theme_colors():
    """Feature #103: Dark theme uses correct colors.

    Steps:
    1. Verify main background is dark gray (#1A1A1A)
    2. Verify sidebar uses (#2A2A2A)
    3. Verify elevated surfaces use (#333333)
    4. Verify text is off-white (#E5E5E5)
    5. Verify borders are (#404040)
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Extract .dark section
    dark_match = re.search(r'\.dark\s*\{([^}]+)\}', css_content, re.DOTALL)
    assert dark_match, "Could not find .dark CSS block"
    dark_content = dark_match.group(1)

    assert re.search(r'--bg-primary:\s*#1A1A1A', dark_content), "Dark bg-primary should be #1A1A1A"
    assert re.search(r'--bg-secondary:\s*#2A2A2A', dark_content), "Dark bg-secondary should be #2A2A2A"
    assert re.search(r'--bg-elevated:\s*#333333', dark_content), "Dark bg-elevated should be #333333"
    assert re.search(r'--surface-elevated:\s*#333333', dark_content), "Dark surface-elevated should be #333333"
    assert re.search(r'--text-primary:\s*#E5E5E5', dark_content), "Dark text-primary should be #E5E5E5"
    assert re.search(r'--border-primary:\s*#404040', dark_content), "Dark border-primary should be #404040"

    print("✅ Feature #103: Dark theme colors are correct")


def test_typography_settings():
    """Feature #104: Typography uses correct font family and sizes.

    Steps:
    1. Verify body text font family
    2. Verify sans-serif stack (Inter, SF Pro, system-ui)
    3. Verify message text is 16px
    4. Verify small text is 14px
    5. Verify code uses monospace (JetBrains Mono, Fira Code)
    6. Verify headings use semibold weight
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Check body font family
    assert re.search(r"font-family:\s*'Inter'", css_content), "Body should use Inter font"
    assert re.search(r"-apple-system", css_content), "Should include system fonts"

    # Check base font size
    assert re.search(r'--base-font-size:\s*16px', css_content), "Base font size should be 16px"
    assert re.search(r'font-size:\s*var\(--base-font-size\)', css_content), "Body should use base font size variable"

    # Check code font family
    assert re.search(r"font-family:\s*'JetBrains Mono'", css_content), "Code should use JetBrains Mono"
    assert re.search(r"'Fira Code'", css_content), "Code should include Fira Code"
    assert re.search(r"monospace", css_content), "Code should fall back to monospace"

    # Check line-height
    assert re.search(r'line-height:\s*1\.6', css_content), "Body line-height should be 1.6"
    assert re.search(r'line-height:\s*1\.75', css_content), "Prose line-height should be 1.75"

    # Check prose headings have semibold weight
    assert re.search(r'\.prose\s+h[1-4]\s*\{[^}]*font-weight:\s*600', css_content), "Prose headings should be semibold"

    print("✅ Feature #104: Typography settings are correct")


def test_message_bubble_styling():
    """Feature #105: Message bubbles have correct styling.

    Steps:
    1. Verify user message has distinct styling
    2. Verify assistant message has different style
    3. Verify proper padding and margins
    4. Verify rounded corners on bubbles
    5. Verify line-height is 1.75 for readability
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Check message-bubble base class
    assert re.search(r'\.message-bubble\s*\{', css_content), "Should have .message-bubble class"
    assert re.search(r'max-width:\s*80%', css_content), "Bubbles should have max-width"
    assert re.search(r'border-radius:\s*1rem', css_content), "Bubbles should have rounded corners"
    assert re.search(r'padding:\s*0\.75rem\s+1rem', css_content), "Bubbles should have proper padding"

    # Check user message styling
    assert re.search(r'\.message-bubble\.user\s*\{', css_content), "Should have user bubble styling"
    assert re.search(r'\.message-bubble\.user[^}]*background-color:\s*var\(--primary\)', css_content, re.DOTALL), \
        "User bubbles should use primary color"
    assert re.search(r'\.message-bubble\.user[^}]*color:\s*white', css_content, re.DOTALL), \
        "User bubbles should have white text"

    # Check assistant message styling
    assert re.search(r'\.message-bubble\.assistant\s*\{', css_content), "Should have assistant bubble styling"
    assert re.search(r'\.message-bubble\.assistant[^}]*background-color:\s*var\(--bg-secondary\)', css_content, re.DOTALL), \
        "Assistant bubbles should use bg-secondary"

    # Check prose line-height for readability
    assert re.search(r'\.prose\s*\{[^}]*line-height:\s*1\.75', css_content, re.DOTALL), \
        "Prose should have line-height 1.75 for readability"

    print("✅ Feature #105: Message bubble styling is correct")


def test_all_styling_features():
    """Run all styling feature tests."""
    print("\n=== Testing Styling Features ===\n")

    test_primary_color_is_correct()
    test_light_theme_colors()
    test_dark_theme_colors()
    test_typography_settings()
    test_message_bubble_styling()

    print("\n=== All Styling Features Verified ===\n")


if __name__ == "__main__":
    test_all_styling_features()
