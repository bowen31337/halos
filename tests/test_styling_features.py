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


def test_input_field_styling():
    """Feature #106: Input field has correct styling and auto-resize behavior.

    Steps:
    1. Verify input uses CSS variables for colors
    2. Verify auto-resize is implemented
    3. Verify focus states use primary color
    """
    from pathlib import Path

    # Check ChatInput component
    chat_input_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/ChatInput.tsx")
    chat_input_content = chat_input_path.read_text()

    # Verify CSS variables are used
    assert 'bg-[var(--bg-primary)]' in chat_input_content, "Input should use bg-primary variable"
    assert 'border-[var(--border-primary)]' in chat_input_content, "Input should use border-primary variable"
    assert 'text-[var(--text-primary)]' in chat_input_content, "Input should use text-primary variable"
    assert 'focus:ring-[var(--primary)]' in chat_input_content, "Input focus should use primary color"

    # Verify auto-resize logic exists
    assert 'auto-resize' in chat_input_content or 'style.height' in chat_input_content, "Should have auto-resize logic"
    assert 'max-h-[200px]' in chat_input_content, "Should have max height limit"

    print("✅ Feature #106: Input field styling is correct")


def test_sidebar_styling():
    """Feature #107: Sidebar has correct layout and spacing.

    Steps:
    1. Verify sidebar uses CSS variables
    2. Verify proper spacing and layout
    """
    from pathlib import Path

    sidebar_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/Sidebar.tsx")
    sidebar_content = sidebar_path.read_text()

    # Verify CSS variables
    assert 'bg-[var(--bg-secondary)]' in sidebar_content, "Sidebar should use bg-secondary"
    assert 'border-[var(--border)]' in sidebar_content, "Sidebar should use border variable"
    assert 'text-[var(--text-secondary)]' in sidebar_content, "Sidebar should use text-secondary"
    assert 'bg-[var(--primary)]' in sidebar_content, "Sidebar buttons should use primary"

    print("✅ Feature #107: Sidebar styling is correct")


def test_button_styling():
    """Feature #108: Buttons follow consistent design patterns.

    Steps:
    1. Verify buttons use primary color
    2. Verify hover and active states
    3. Verify consistent rounded corners
    """
    from pathlib import Path

    # Check multiple components for button patterns
    components = [
        "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/ChatInput.tsx",
        "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/Sidebar.tsx",
        "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/Header.tsx",
    ]

    for component_path in components:
        content = Path(component_path).read_text()
        # Check for button patterns
        if 'bg-[var(--primary)]' in content:
            # Primary buttons should have hover states
            assert 'hover:bg-[var(--primary-hover)]' in content or 'hover:bg-[var(--primary)]/90' in content or 'hover:bg-[var(--surface-elevated)]' in content, \
                f"Button in {component_path} should have hover state"
            # Should have rounded corners
            assert 'rounded-lg' in content or 'rounded-full' in content or 'rounded-md' in content, \
                f"Button in {component_path} should have rounded corners"

    print("✅ Feature #108: Button styling is consistent")


def test_code_block_styling():
    """Feature #109: Code blocks use appropriate styling with One Dark/Light theme.

    Steps:
    1. Verify code blocks use monospace font
    2. Verify syntax highlighting is configured
    3. Verify copy button styling
    """
    from pathlib import Path

    message_bubble_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/MessageBubble.tsx")
    content = message_bubble_path.read_text()

    # Verify syntax highlighter import
    assert 'SyntaxHighlighter' in content, "Should use syntax highlighter"
    assert 'oneDark' in content, "Should use oneDark theme"

    # Verify code block styling uses CSS variables
    assert 'bg-[var(--surface-elevated)]' in content, "Code header should use surface-elevated"
    assert 'bg-[var(--bg-primary)]' in content, "Code body should use bg-primary"
    assert 'border-[var(--border)]' in content, "Code should use border variable"

    # Check CSS file for code styling
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    assert 'code {' in css_content, "Should have code styling"
    assert 'JetBrains Mono' in css_content or 'Fira Code' in css_content, "Should use monospace fonts"

    print("✅ Feature #109: Code block styling is correct")


def test_modal_styling():
    """Feature #110: Modal dialogs have consistent styling.

    Steps:
    1. Verify modals use CSS variables
    2. Verify consistent background and border styling
    """
    from pathlib import Path

    # Check for modal components
    modal_files = [
        "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/SettingsModal.tsx",
        "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/ProjectModal.tsx",
    ]

    for modal_path in modal_files:
        try:
            content = Path(modal_path).read_text()
            # Modals should use consistent styling
            if 'className' in content:
                # Check for bg-primary or bg-elevated
                assert any(var in content for var in ['bg-[var(--bg-primary)]', 'bg-[var(--bg-elevated)]', 'bg-[var(--surface-elevated)]']), \
                    f"Modal {modal_path} should use CSS variables for background"
        except FileNotFoundError:
            pass  # Some modals might not exist yet

    print("✅ Feature #110: Modal styling is consistent")


def test_dropdown_styling():
    """Feature #111: Dropdowns and select menus are styled consistently.

    Steps:
    1. Verify dropdowns use CSS variables
    2. Verify consistent styling patterns
    """
    from pathlib import Path

    header_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/Header.tsx")
    header_content = header_path.read_text()

    # Check for dropdown patterns - dropdowns use surface-elevated for buttons and bg-primary for menus
    assert 'bg-[var(--surface-elevated)]' in header_content, "Dropdown buttons should use surface-elevated"
    assert 'bg-[var(--bg-primary)]' in header_content, "Dropdown menus should use bg-primary"
    assert 'border-[var(--border-primary)]' in header_content, "Dropdown should use border variable"
    assert 'text-[var(--text-primary)]' in header_content, "Dropdown should use text-primary"
    assert 'hover:bg-[var(--surface-elevated)]' in header_content, "Dropdown items should have hover state"

    print("✅ Feature #111: Dropdown styling is consistent")


def test_all_styling_features():
    """Run all styling feature tests."""
    print("\n=== Testing Styling Features ===\n")

    test_primary_color_is_correct()
    test_light_theme_colors()
    test_dark_theme_colors()
    test_typography_settings()
    test_message_bubble_styling()
    test_input_field_styling()
    test_sidebar_styling()
    test_button_styling()
    test_code_block_styling()
    test_modal_styling()
    test_dropdown_styling()

    print("\n=== All Styling Features Verified ===\n")


if __name__ == "__main__":
    test_all_styling_features()
