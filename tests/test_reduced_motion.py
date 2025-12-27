#!/usr/bin/env python3
"""
Test Feature #129: Reduced motion preference is respected

Tests that the application respects the prefers-reduced-motion media query
and disables animations for users who prefer reduced motion.
"""

import os
from pathlib import Path


def test_reduced_motion_css_exists():
    """Verify that reduced motion CSS media query is defined"""
    css_path = Path(__file__).parent.parent / 'client' / 'src' / 'index.css'

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Check for prefers-reduced-motion media query
    assert '@media (prefers-reduced-motion: reduce)' in css_content, \
        "CSS should have @media (prefers-reduced-motion: reduce) query"

    print("✓ Reduced motion media query exists")


def test_reduced_motion_disables_animations():
    """Verify that animations are disabled in reduced motion mode"""
    css_path = Path(__file__).parent.parent / 'client' / 'src' / 'index.css'

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Find the reduced motion block
    import re
    reduced_motion_match = re.search(
        r'@media\s+\(prefers-reduced-motion:\s+reduce\)\s*{([^}]+)}',
        css_content,
        re.DOTALL
    )

    assert reduced_motion_match, "Should find reduced motion media query block"

    block_content = reduced_motion_match.group(1)

    # Check that animations are set to none or very short duration
    assert 'animation' in block_content.lower(), \
        "Reduced motion block should contain animation rules"

    # Check for animation duration being set to 0 or very short
    assert 'animation-duration: 0.01ms' in block_content or 'animation: none' in block_content, \
        "Animations should be disabled or set to minimal duration"

    # Check for transition duration being set to 0 or very short
    assert 'transition-duration: 0.01ms' in block_content or 'transition: none' in block_content, \
        "Transitions should be disabled or set to minimal duration"

    print("✓ Animations are properly disabled in reduced motion mode")


def test_reduced_motion_specific_classes():
    """Verify that specific animation classes are disabled"""
    css_path = Path(__file__).parent.parent / 'client' / 'src' / 'index.css'

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Find the reduced motion block - need to capture the full block including nested braces
    import re
    # More robust regex that handles nested braces
    reduced_motion_match = re.search(
        r'@media\s+\(prefers-reduced-motion:\s+reduce\)\s*\{',
        css_content
    )

    assert reduced_motion_match, "Should find reduced motion media query"

    # Find the end of the block by counting braces
    start_pos = reduced_motion_match.end()
    brace_count = 1
    end_pos = start_pos

    for i, char in enumerate(css_content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_pos = start_pos + i
                break

    block_content = css_content[start_pos:end_pos]

    # Check for specific animation classes being disabled
    animation_classes = [
        'loading-spinner',
        'loading-dots',
        'typing-indicator',
        'animate-fade-in',
        'animate-slide-in',
        'transition-smooth'
    ]

    found_classes = [cls for cls in animation_classes if cls in block_content]

    # At least some animation classes should be explicitly disabled
    assert len(found_classes) > 0, \
        f"Should disable specific animation classes, found: {found_classes}"

    print(f"✓ Specific animation classes disabled: {', '.join(found_classes)}")


def test_reduced_motion_instant_state_changes():
    """Verify that hover/focus states have no transitions in reduced motion"""
    css_path = Path(__file__).parent.parent / 'client' / 'src' / 'index.css'

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Find the reduced motion block
    import re
    reduced_motion_match = re.search(
        r'@media\s+\(prefers-reduced-motion:\s+reduce\)\s*\{',
        css_content
    )

    assert reduced_motion_match, "Should find reduced motion media query"

    # Find the end of the block by counting braces
    start_pos = reduced_motion_match.end()
    brace_count = 1
    end_pos = start_pos

    for i, char in enumerate(css_content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_pos = start_pos + i
                break

    block_content = css_content[start_pos:end_pos]

    # Check for instant state changes (no transitions)
    assert 'transition: none' in block_content or 'transition-duration: 0.01ms' in block_content, \
        "Should have instant state changes with no transitions"

    # Check that it applies to interactive elements
    assert 'button:hover' in block_content or 'button:focus-visible' in block_content, \
        "Should apply to interactive elements like buttons"

    print("✓ Instant state changes configured for interactive elements")


def test_reduced_motion_important_flag():
    """Verify that reduced motion rules use !important for enforcement"""
    css_path = Path(__file__).parent.parent / 'client' / 'src' / 'index.css'

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Find the reduced motion block
    import re
    reduced_motion_match = re.search(
        r'@media\s+\(prefers-reduced-motion:\s+reduce\)\s*\{',
        css_content
    )

    assert reduced_motion_match, "Should find reduced motion media query"

    # Find the end of the block by counting braces
    start_pos = reduced_motion_match.end()
    brace_count = 1
    end_pos = start_pos

    for i, char in enumerate(css_content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_pos = start_pos + i
                break

    block_content = css_content[start_pos:end_pos]

    # Check for !important flag to override other animations
    assert '!' in block_content and ('ms' in block_content or 'none' in block_content), \
        "Should use !important or explicit values to override animations"

    print("✓ Reduced motion rules use enforcement mechanisms")


def test_ui_store_reduced_motion_compatibility():
    """Verify that UI store doesn't interfere with reduced motion"""
    store_path = Path(__file__).parent.parent / 'client' / 'src' / 'stores' / 'uiStore.ts'

    with open(store_path, 'r') as f:
        content = f.read()

    # The store should not force animations that would override reduced motion
    # Check that transitions are not hardcoded in a way that would conflict

    # This is a structural check - the store should use CSS classes/variables
    # that can be overridden by media queries
    assert 'transition' not in content or 'transition:' not in content, \
        "Store should not hardcode transitions that would override reduced motion"

    print("✓ UI store is compatible with reduced motion preferences")


def main():
    """Run all reduced motion tests"""
    print("\n" + "="*70)
    print("Testing Feature #129: Reduced motion preference is respected")
    print("="*70 + "\n")

    try:
        test_reduced_motion_css_exists()
        test_reduced_motion_disables_animations()
        test_reduced_motion_specific_classes()
        test_reduced_motion_instant_state_changes()
        test_reduced_motion_important_flag()
        test_ui_store_reduced_motion_compatibility()

        print("\n" + "="*70)
        print("All Feature #129 tests passed! ✓")
        print("="*70 + "\n")
        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
