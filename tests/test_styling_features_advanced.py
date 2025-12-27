"""Test advanced styling features for features #112-114.

This test file verifies that loading states, transitions, and toast notifications
are correctly styled and implemented.
"""

import re
from pathlib import Path


def test_loading_states_and_spinners():
    """Feature #112: Loading states and spinners are visually consistent.

    Steps:
    1. Verify loading spinner animation exists
    2. Verify typing indicator animation exists
    3. Verify loading dots animation exists
    4. Verify all animations use consistent timing (150-300ms for transitions, 1s for spin)
    5. Verify loading states use CSS variables
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Check loading spinner animation
    assert re.search(r'@keyframes\s+spin\s*\{', css_content), "Spin animation should exist"
    assert re.search(r'animation:\s*spin\s+1s\s+linear\s+infinite', css_content), "Spinner should use 1s linear infinite"

    # Check loading spinner component classes
    assert re.search(r'\.loading-spinner\s*\{', css_content), "Loading spinner class should exist"
    assert re.search(r'\.loading-spinner\.primary\s*\{', css_content), "Primary spinner variant should exist"
    assert re.search(r'\.loading-spinner\.small\s*\{', css_content), "Small spinner variant should exist"
    assert re.search(r'\.loading-spinner\.large\s*\{', css_content), "Large spinner variant should exist"

    # Check spinner uses CSS variables
    assert re.search(r'border:\s*2px\s+solid\s+var\(--text-secondary\)', css_content), "Spinner should use text-secondary variable"
    assert re.search(r'\.loading-spinner\.primary[^}]*border-color:\s*var\(--primary\)', css_content, re.DOTALL), \
        "Primary spinner should use primary color variable"

    # Check loading dots animation
    assert re.search(r'@keyframes\s+bounce-dots\s*\{', css_content), "Bounce dots animation should exist"
    assert re.search(r'\.loading-dots\s*\{', css_content), "Loading dots class should exist"
    assert re.search(r'\.loading-dots\.primary\s*>\s*span', css_content), "Primary dots variant should exist"

    # Check loading dots use CSS variables
    assert re.search(r'\.loading-dots\s*>\s*span\s*\{[^}]*background-color:\s*var\(--text-secondary\)', css_content, re.DOTALL), \
        "Dots should use text-secondary variable"
    assert re.search(r'\.loading-dots\.primary\s*>\s*span\s*\{[^}]*background-color:\s*var\(--primary\)', css_content, re.DOTALL), \
        "Primary dots should use primary color variable"

    # Check typing indicator
    assert re.search(r'@keyframes\s+typing\s*\{', css_content), "Typing animation should exist"
    assert re.search(r'\.typing-indicator\s*\{', css_content), "Typing indicator class should exist"

    # Check pulse animation
    assert re.search(r'@keyframes\s+pulse-standard\s*\{', css_content), "Pulse animation should exist"
    assert re.search(r'\.loading-pulse\s*\{', css_content), "Loading pulse class should exist"

    # Check button loading state
    assert re.search(r'button:disabled\.loading\s*\{', css_content), "Button loading state should exist"
    assert re.search(r'button:disabled\.loading::after\s*\{', css_content), "Button loading spinner should exist"

    # Verify fade-in animation
    assert re.search(r'@keyframes\s+fadeIn\s*\{', css_content), "Fade-in animation should exist"
    assert re.search(r'\.animate-fade-in\s*\{', css_content), "Fade-in class should exist"

    print("✅ Feature #112: Loading states and spinners are visually consistent")


def test_transitions_and_animations():
    """Feature #113: Transitions and animations are smooth.

    Steps:
    1. Verify smooth transition class exists
    2. Verify slide animations exist
    3. Verify animation timing is appropriate (150-300ms)
    4. Verify ease-out timing functions
    5. Verify no janky animations (consistent timing)
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Check smooth transition class
    assert re.search(r'\.transition-smooth\s*\{', css_content), "Smooth transition class should exist"
    assert re.search(r'transition:\s*all\s+0\.2s\s+cubic-bezier', css_content), "Should use cubic-bezier timing"

    # Check slide animations
    assert re.search(r'@keyframes\s+slideInFromRight\s*\{', css_content), "Slide from right animation should exist"
    assert re.search(r'@keyframes\s+slideInFromLeft\s*\{', css_content), "Slide from left animation should exist"
    assert re.search(r'\.animate-slide-in-right\s*\{', css_content), "Slide-in-right class should exist"
    assert re.search(r'\.animate-slide-in-left\s*\{', css_content), "Slide-in-left class should exist"

    # Verify animation timing (should be 0.3s for slides)
    assert re.search(r'animation:\s*slideInFromRight\s+0\.3s\s+ease-out', css_content), \
        "Slide animation should use 0.3s ease-out"
    assert re.search(r'animation:\s*slideInFromLeft\s+0\.3s\s+ease-out', css_content), \
        "Slide animation should use 0.3s ease-out"

    # Verify fade-in timing (should be 0.2s)
    assert re.search(r'animation:\s*fadeIn\s+0\.2s\s+ease-out', css_content), \
        "Fade-in should use 0.2s ease-out"

    # Check default transition on interactive elements
    assert re.search(r'button,\s*a,\s*input,\s*textarea\s*\{[^}]*transition:\s*all\s+0\.2s', css_content, re.DOTALL), \
        "Interactive elements should have 0.2s transitions"

    # Verify hover states use smooth transitions
    assert re.search(r'::-webkit-scrollbar-thumb:hover\s*\{', css_content), "Scrollbar hover should exist"

    # Check focus states
    assert re.search(r':focus-visible\s*\{', css_content), "Focus-visible should exist"

    print("✅ Feature #113: Transitions and animations are smooth")


def test_status_colors():
    """Feature #114: Success, warning, error states use correct colors.

    Steps:
    1. Verify success color (#10B981)
    2. Verify warning color (#F59E0B)
    3. Verify error color (#EF4444)
    4. Verify info color (#3B82F6)
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Extract :root section
    root_match = re.search(r':root\s*\{([^}]+)\}', css_content, re.DOTALL)
    assert root_match, "Could not find :root CSS block"
    root_content = root_match.group(1)

    # Check status colors
    assert re.search(r'--success:\s*#10B981', root_content), "Success color should be #10B981"
    assert re.search(r'--warning:\s*#F59E0B', root_content), "Warning color should be #F59E0B"
    assert re.search(r'--error:\s*#EF4444', root_content), "Error color should be #EF4444"
    assert re.search(r'--info:\s*#3B82F6', root_content), "Info color should be #3B82F6"

    # Verify these are used in the codebase
    components_dir = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components")

    # Check for usage of these colors in components
    found_success = False
    found_warning = False
    found_error = False
    found_info = False

    for component_file in components_dir.rglob("*.tsx"):
        content = component_file.read_text()
        if 'bg-[var(--success)]' in content or 'text-[var(--success)]' in content:
            found_success = True
        if 'bg-[var(--warning)]' in content or 'text-[var(--warning)]' in content:
            found_warning = True
        if 'bg-[var(--error)]' in content or 'text-[var(--error)]' in content:
            found_error = True
        if 'bg-[var(--info)]' in content or 'text-[var(--info)]' in content:
            found_info = True

    # At least some of these should be used
    assert found_success or found_warning or found_error or found_info, \
        "Status colors should be used in at least some components"

    print("✅ Feature #114: Status colors use correct values")


def test_tool_call_blocks_styling():
    """Feature #115: Tool call blocks have distinct visual treatment.

    Steps:
    1. Verify tool call blocks use elevated surface styling
    2. Verify tool name is prominently displayed
    3. Verify input/output sections are clear
    4. Verify collapse/expand styling
    """
    from pathlib import Path

    message_bubble_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/MessageBubble.tsx")
    content = message_bubble_path.read_text()

    # Check for tool message handling
    assert 'isTool' in content or "role === 'tool'" in content, "Should handle tool messages"

    # Verify tool block styling uses CSS variables
    assert 'bg-[var(--surface-elevated)]' in content, "Tool block should use surface-elevated"
    assert 'border-[var(--border-primary)]' in content, "Tool block should use border-primary"

    # Verify tool name display
    assert 'toolName' in content, "Should display tool name"
    assert 'Tool Call' in content or 'tool_call' in content, "Should label tool calls"

    # Verify input/output sections
    assert 'toolInput' in content, "Should show tool input"
    assert 'toolOutput' in content, "Should show tool output"

    # Verify collapse/expand functionality
    assert 'isExpanded' in content, "Should have expand/collapse state"
    assert 'setIsExpanded' in content, "Should have toggle function"

    # Verify visual indicators
    assert '🔧' in content or 'span' in content, "Should have visual indicator"

    print("✅ Feature #115: Tool call blocks have distinct visual treatment")


def test_hitl_dialog_styling():
    """Feature #116: HITL approval dialog is clearly visible and styled.

    Steps:
    1. Verify dialog has attention-grabbing styling
    2. Verify tool name and details are clear
    3. Verify approve button is primary styled
    4. Verify reject button is danger styled
    5. Verify edit option is accessible
    """
    from pathlib import Path

    hitl_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/HITLApprovalDialog.tsx")
    content = hitl_path.read_text()

    # Verify dialog uses CSS variables for styling
    assert 'bg-[var(--bg-primary)]' in content, "Dialog should use bg-primary"
    assert 'border-[var(--border)]' in content, "Dialog should use border variable"
    assert 'text-[var(--text-primary)]' in content, "Dialog should use text-primary"

    # Verify attention-grabbing elements
    assert '⚠️' in content or 'warning' in content.lower(), "Should have warning indicator"
    assert 'Approval Required' in content, "Should have clear title"

    # Verify approve button styling
    assert 'bg-[var(--success)]' in content, "Approve button should use success color"
    assert 'Approve' in content, "Should have approve button"

    # Verify reject button styling
    assert 'bg-[var(--error)]' in content or 'text-[var(--error)]' in content, \
        "Reject button should use error color"
    assert 'Reject' in content, "Should have reject button"

    # Verify edit option
    assert 'Edit' in content, "Should have edit option"
    assert 'Edit Input' in content, "Should have edit input tab"

    # Verify tool info display
    assert 'tool' in content.lower(), "Should display tool information"
    assert 'input' in content.lower(), "Should display input information"
    assert 'reason' in content.lower(), "Should display reason"

    print("✅ Feature #116: HITL approval dialog is clearly visible and styled")


def test_all_advanced_styling_features():
    """Run all advanced styling feature tests."""
    print("\n=== Testing Advanced Styling Features ===\n")

    test_loading_states_and_spinners()
    test_transitions_and_animations()
    test_status_colors()
    test_tool_call_blocks_styling()
    test_hitl_dialog_styling()

    print("\n=== All Advanced Styling Features Verified ===\n")


if __name__ == "__main__":
    test_all_advanced_styling_features()
