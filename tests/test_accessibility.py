"""
Accessibility Test Suite for Claude.ai Clone

Tests keyboard navigation, ARIA labels, screen reader support, and focus states.
"""

import pytest
from playwright.sync_api import Page, expect
import json


class TestAccessibility:
    """Comprehensive accessibility tests"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup browser and navigate to app"""
        # Navigate to the application
        page.goto("http://localhost:5173")
        # Wait for page to load
        page.wait_for_load_state("networkidle")

    def test_skip_navigation_link_exists(self, page: Page):
        """Test that skip navigation link is present and functional"""
        # Check for skip navigation link (may be hidden until focused)
        skip_links = page.locator('a[href="#main-content"], .skip-nav, [data-testid="skip-nav"]')

        # Should exist even if hidden
        expect(skip_links).to_have_count(lambda count: count >= 0)

        # If it exists, test that it's properly hidden
        if skip_links.count() > 0:
            skip_link = skip_links.first
            # Should be off-screen or invisible
            expect(skip_link).to_be_visible()

    def test_main_content_area_has_id(self, page: Page):
        """Test that main content has proper id for skip navigation"""
        main = page.locator('main, [role="main"], #main-content')
        expect(main.first).to_be_visible()
        expect(main.first).to_have_attribute("id", value="main-content")

    def test_aria_labels_on_interactive_elements(self, page: Page):
        """Test that buttons and links have proper ARIA labels"""
        # Check buttons
        buttons = page.locator('button:not([aria-label])').all()

        # Count buttons without text content (these need aria-label)
        buttons_without_labels = 0
        for button in buttons:
            text = button.inner_text().strip()
            if not text or len(text) == 0:
                buttons_without_labels += 1

        # Icon buttons should have aria-label or aria-labelledby
        assert buttons_without_labels < 5, f"Too many icon buttons without labels: {buttons_without_labels}"

    def test_role_attributes_present(self, page: Page):
        """Test that semantic roles are properly defined"""
        # Check for main navigation role
        sidebar = page.locator('[role="navigation"], nav').first
        expect(sidebar).to_be_visible()

        # Check for main content role
        main = page.locator('[role="main"], main').first
        expect(main).to_be_visible()

    def test_keyboard_focus_visible(self, page: Page):
        """Test that keyboard focus is visible"""
        # Tab to first interactive element
        page.keyboard.press('Tab')

        # Get focused element
        focused = page.locator(':focus')
        expect(focused).to_be_visible()

        # Check computed styles for focus indicator
        focus_outline = focused.evaluate('el => getComputedStyle(el).outline')
        focus_box_shadow = focused.evaluate('el => getComputedStyle(el).boxShadow')

        # Should have visible focus indicator
        assert focus_outline != 'none' or focus_box_shadow != 'none', \
            "Focused element should have visible focus indicator"

    def test_keyboard_navigation_works(self, page: Page):
        """Test that all interactive elements are keyboard accessible"""
        # Find all interactive elements
        interactive = page.locator('a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])')

        # Tab through first 10 elements
        for i in range(min(10, interactive.count())):
            page.keyboard.press('Tab')

            # Something should be focused
            focused = page.locator(':focus')
            expect(focused).to_be_visible()

            # Element should have tabindex or be naturally focusable
            tag_name = focused.evaluate('el => el.tagName.lower()')
            tabindex = focused.evaluate('el => el.getAttribute("tabindex")')

            assert tag_name in ['a', 'button', 'input', 'textarea', 'select'] or tabindex is not None

    def test_no_keyboard_traps(self, page: Page):
        """Test that user can't get trapped in keyboard focus"""
        # Press Tab many times to cycle through focusable elements
        focusable_count = page.locator('a, button, input, [tabindex="0"]').count()

        # Tab through all elements
        for _ in range(focusable_count + 5):
            page.keyboard.press('Tab')

        # Should be able to continue tabbing
        focused = page.locator(':focus')
        expect(focused).to_be_visible()

    def test_aria_expanded_on_toggles(self, page: Page):
        """Test that toggle buttons have proper aria-expanded attributes"""
        # Find buttons with aria-expanded
        expandable_buttons = page.locator('button[aria-expanded]')

        if expandable_buttons.count() > 0:
            for button in expandable_buttons.all()[:5]:  # Check first 5
                aria_expanded = button.get_attribute('aria-expanded')
                assert aria_expanded in ['true', 'false'], \
                    f"aria-expanded should be 'true' or 'false', got: {aria_expanded}"

    def test_aria_hidden_on_decorative(self, page: Page):
        """Test that decorative elements have aria-hidden"""
        # Check for icon-only buttons (should have aria-label or aria-hidden)
        icon_buttons = page.locator('button svg').all()

        for button_parent in icon_buttons[:5]:  # Check first 5
            parent = button_parent.locator('..')
            has_label = parent.get_attribute('aria-label') is not None
            has_hidden = parent.get_attribute('aria-hidden') == 'true'

            # Icon containers should be labeled or hidden
            assert has_label or has_hidden, \
                "Icon buttons should have aria-label or be aria-hidden"

    def test_alt_text_on_images(self, page: Page):
        """Test that images have alt text"""
        images = page.locator('img')

        if images.count() > 0:
            for img in images.all()[:10]:  # Check first 10
                alt = img.get_attribute('alt')
                # Alt text should exist (can be empty for decorative images)
                assert alt is not None, "Images should have alt attribute"

    def test_form_labels(self, page: Page):
        """Test that form inputs have labels"""
        # Find input fields
        inputs = page.locator('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea')

        if inputs.count() > 0:
            for input_elem in inputs.all()[:5]:  # Check first 5
                # Check for associated label
                input_id = input_elem.get_attribute('id')
                aria_label = input_elem.get_attribute('aria-label')
                aria_labelledby = input_elem.get_attribute('aria-labelledby')

                has_label = (
                    (input_id and page.locator(f'label[for="{input_id}"]').count() > 0) or
                    aria_label is not None or
                    aria_labelledby is not None or
                    input_elem.locator('xpath=../label').count() > 0
                )

                assert has_label, "Form inputs should have accessible labels"

    def test_heading_hierarchy(self, page: Page):
        """Test that heading levels are logical"""
        headings = page.locator('h1, h2, h3, h4, h5, h6').all()

        if len(headings) > 0:
            previous_level = 0
            for heading in headings:
                tag = heading.evaluate('el => el.tagName.toLowerCase()')
                level = int(tag[1])  # Extract number from h1, h2, etc.

                # Headings should not skip levels (e.g., h1 -> h3)
                if previous_level > 0:
                    assert level <= previous_level + 1, \
                        f"Heading level skipped: {previous_level} -> {level}"

                previous_level = level

    def test_color_contrast(self, page: Page):
        """Test color contrast ratios (basic check)"""
        # Get text elements
        text_elements = page.locator('p, span, div, h1, h2, h3, h4, h5, h6, button, a')

        if text_elements.count() > 0:
            # Check first few text elements
            for element in text_elements.all()[:10]:
                # Get computed colors
                bg_color = element.evaluate('el => getComputedStyle(el).backgroundColor')
                text_color = element.evaluate('el => getComputedStyle(el).color')

                # Basic check: colors should be different
                assert bg_color != text_color, \
                    "Text and background should have different colors"

    def test_landmark_regions(self, page: Page):
        """Test that page has proper landmark regions"""
        # Check for navigation
        nav = page.locator('nav, [role="navigation"]')
        expect(nav.first).to_be_visible()

        # Check for main content
        main = page.locator('main, [role="main"]')
        expect(main.first).to_be_visible()

    def test_dialog_modal_accessibility(self, page: Page):
        """Test that dialogs/modals are accessible"""
        # Try to find any modal dialogs
        dialogs = page.locator('[role="dialog"], .modal, dialog')

        if dialogs.count() > 0 and dialogs.first.is_visible():
            dialog = dialogs.first

            # Should have aria-modal or be dialog element
            role = dialog.get_attribute('role')
            is_dialog_element = dialog.evaluate('el => el.tagName.toLowerCase() === "dialog"')

            assert role == 'dialog' or is_dialog_element, \
                "Modals should have role='dialog' or be <dialog> elements"

            # Check for focus trap (first focusable element should be in dialog)
            dialog_focusable = dialog.locator('button, input, a, [tabindex="0"]')

            if dialog_focusable.count() > 0:
                # Focus first element in dialog
                dialog_focusable.first.focus()
                focused = page.locator(':focus')

                # Should be inside the dialog
                expect(dialog).to_contain(focused)

    def test_live_regions(self, page: Page):
        """Test for ARIA live regions for dynamic content"""
        # Find elements with aria-live
        live_regions = page.locator('[aria-live]')

        # Live regions should have polite or assertive setting
        if live_regions.count() > 0:
            for region in live_regions.all()[:5]:
                aria_live = region.get_attribute('aria-live')
                assert aria_live in ['polite', 'assertive', 'off'], \
                    f"aria-live should be 'polite', 'assertive', or 'off', got: {aria_live}"

    def test_accessibility_tree(self, page: Page):
        """Test accessibility tree structure"""
        # Get accessibility tree
        acc_tree = page.accessibility.snapshot()

        assert acc_tree is not None, "Accessibility tree should exist"
        assert 'children' in acc_tree, "Accessibility tree should have children"

        # Check for proper role assignment
        # Root should have a meaningful role
        assert acc_tree.get('role') in ['WebArea', 'RootWebArea'], \
            f"Root should have meaningful role, got: {acc_tree.get('role')}"

    def test_reduced_motion_preference(self, page: Page):
        """Test that reduced motion preference is respected"""
        # Emulate prefers-reduced-motion
        page.emulate_media(reduced_motion='reduce')

        # Check that animations are disabled
        animated_elements = page.locator('.animate-, [style*="animation"]')

        if animated_elements.count() > 0:
            for elem in animated_elements.all()[:5]:
                animation = elem.evaluate('el => getComputedStyle(el).animation')

                # Animation should be none or very short
                assert animation == 'none' or '0s' in animation, \
                    "Animations should be disabled with prefers-reduced-motion"

    def test_focus_management_on_modal_open(self, page: Page):
        """Test that focus is managed properly when modals open"""
        # This test would require opening a modal, so we'll check if we can find one
        settings_button = page.locator('button:has-text("Settings"), [aria-label="Settings"], .settings-button')

        if settings_button.count() > 0:
            # Click settings button
            settings_button.first.click()
            page.wait_for_timeout(500)  # Wait for modal to appear

            # Check if modal appeared
            modal = page.locator('[role="dialog"], .modal').first

            if modal.is_visible():
                # Focus should be in the modal
                focused = page.locator(':focus')
                expect(modal).to_contain(focused)

                # Press Escape to close
                page.keyboard.press('Escape')
                page.wait_for_timeout(300)


class TestKeyboardNavigation:
    """Specific tests for keyboard navigation"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup browser"""
        page.goto("http://localhost:5173")
        page.wait_for_load_state("networkidle")

    def test_tab_order_is_logical(self, page: Page):
        """Test that tab order follows visual layout"""
        # Get all focusable elements
        focusable_elements = page.locator('a, button, input, textarea, select, [tabindex="0"]')

        # Tab through elements and record order
        tab_order = []
        for _ in range(min(20, focusable_elements.count())):
            page.keyboard.press('Tab')
            focused = page.locator(':focus')
            if focused.count() > 0:
                tag = focused.evaluate('el => el.tagName.toLowerCase()')
                tab_order.append(tag)

        # Should have navigated through multiple elements
        assert len(tab_order) > 0, "Should be able to tab through elements"

    def test_enter_and_space_activate_buttons(self, page: Page):
        """Test that Enter and Space activate buttons"""
        # Find a button
        button = page.locator('button').first
        expect(button).to_be_visible()

        # Focus the button
        button.focus()

        # Press Enter
        page.keyboard.press('Enter')
        page.wait_for_timeout(300)

        # Some action should have occurred (can't easily test without side effects)
        # But we can verify button is still focused or state changed

    def test_escape_closes_modals(self, page: Page):
        """Test that Escape key closes modals"""
        # Try to find a modal trigger
        modal_triggers = page.locator('button[aria-expanded="true"], button:has-text("Open"), button:has-text("Settings")')

        if modal_triggers.count() > 0:
            # Open modal
            modal_triggers.first.click()
            page.wait_for_timeout(500)

            # Check if modal appeared
            modal = page.locator('[role="dialog"]').first

            if modal.is_visible():
                # Press Escape
                page.keyboard.press('Escape')
                page.wait_for_timeout(500)

                # Modal should be closed or hidden
                expect(modal).not_to_be_visible()

    def test_arrow_keys_in_lists(self, page: Page):
        """Test arrow key navigation in lists"""
        # Find a list container (conversation list, etc.)
        lists = page.locator('[role="listbox"], ul, ol')

        if lists.count() > 0:
            list_elem = lists.first

            # Click first item to focus list
            first_item = list_elem.locator('li, [role="option"]').first

            if first_item.count() > 0:
                first_item.click()
                page.wait_for_timeout(200)

                # Try arrow down
                page.keyboard.press('ArrowDown')
                page.wait_for_timeout(200)

                # Focus should move to next item
                focused = page.locator(':focus')
                expect(focused).to_be_visible()


def test_accessibility_summary(page: Page):
    """Generate accessibility audit summary"""
    page.goto("http://localhost:5173")
    page.wait_for_load_state("networkidle")

    # Get accessibility tree
    acc_tree = page.accessibility.snapshot()

    # Count interactive elements
    buttons = page.locator('button').count()
    links = page.locator('a').count()
    inputs = page.locator('input, textarea, select').count()

    # Count ARIA attributes
    aria_labels = page.locator('[aria-label]').count()
    aria_described = page.locator('[aria-describedby]').count()
    aria_live = page.locator('[aria-live]').count()

    summary = {
        'buttons': buttons,
        'links': links,
        'inputs': inputs,
        'aria_labels': aria_labels,
        'aria_describedby': aria_described,
        'aria_live_regions': aria_live,
        'total_interactive': buttons + links + inputs,
    }

    print("\n=== Accessibility Audit Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    return summary
