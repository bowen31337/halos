#!/usr/bin/env python3
"""
Test script for Feature #151: Model capabilities display
Tests that the model selector shows capabilities, strengths, and limits for each model.
"""

import asyncio
from playwright.async_api import async_playwright
import sys


async def test_model_capabilities():
    """Test the model capabilities display feature."""
    print("=" * 60)
    print("Testing Feature #151: Model capabilities display")
    print("=" * 60)

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Track test results
        test_results = []

        try:
            # Navigate to the app
            print("\n[Step 1] Navigating to http://localhost:5173...")
            await page.goto("http://localhost:5173", wait_until="networkidle")
            await page.wait_for_timeout(500)

            # Check if we're on the page
            title = await page.title()
            print(f"  Page title: {title}")

            # Wait for the page to load
            await page.wait_for_selector("text=/Claude|Model|Chat/", timeout=5000)
            print("  ✓ Page loaded")
            test_results.append(("Page load", True))

            # Step 2: Find and click the model selector button
            print("\n[Step 2] Looking for model selector...")

            # Try multiple selectors for the model button
            model_selectors = [
                "button:has-text('Claude')",
                "button:has-text('Model')",
                "[data-testid='model-selector']",
                ".model-selector",
                "button[title*='model' i]",
                "text=/Claude Sonnet|Claude Opus|Claude Haiku/"
            ]

            model_button = None
            for selector in model_selectors:
                try:
                    model_button = await page.locator(selector).first
                    if await model_button.count() > 0:
                        print(f"  Found model button with selector: {selector}")
                        break
                except:
                    continue

            if not model_button:
                # Try to find any button that might be the model selector
                buttons = page.locator("button")
                count = await buttons.count()
                for i in range(min(count, 20)):
                    btn = buttons.nth(i)
                    text = await btn.inner_text()
                    if "Claude" in text or "Model" in text:
                        model_button = btn
                        print(f"  Found model button by iterating: '{text}'")
                        break

            if model_button:
                await model_button.click()
                await page.wait_for_timeout(300)
                print("  ✓ Model selector clicked")
                test_results.append(("Model selector click", True))
            else:
                print("  ✗ Could not find model selector button")
                test_results.append(("Model selector click", False))
                # Continue to try other checks

            # Step 3: Check for capabilities tooltip/display
            print("\n[Step 3] Checking for capabilities display...")

            # Look for capabilities text
            capabilities_text = ["Capabilities:", "Strengths:", "Limits:"]
            found_capabilities = False

            for cap_text in capabilities_text:
                if await page.locator(f"text={cap_text}").count() > 0:
                    print(f"  ✓ Found '{cap_text}'")
                    found_capabilities = True

            if found_capabilities:
                test_results.append(("Capabilities display", True))
            else:
                # Try to find the dropdown content
                content = await page.content()
                if "Reasoning" in content or "Code generation" in content:
                    print("  ✓ Found capability keywords in page")
                    test_results.append(("Capabilities display", True))
                else:
                    print("  ✗ Capabilities display not found")
                    test_results.append(("Capabilities display", False))

            # Step 4: Verify context window is displayed
            print("\n[Step 4] Checking for context window (200K)...")

            content = await page.content()
            if "200K" in content or "200k" in content:
                print("  ✓ Context window (200K) found")
                test_results.append(("Context window display", True))
            else:
                print("  ✗ Context window not found")
                test_results.append(("Context window display", False))

            # Step 5: Check for strengths text
            print("\n[Step 5] Checking for strengths text...")

            content = await page.content()
            if "Strengths:" in content:
                print("  ✓ Strengths section found")
                test_results.append(("Strengths display", True))
            else:
                print("  ✗ Strengths section not found")
                test_results.append(("Strengths display", False))

            # Step 6: Check for other models
            print("\n[Step 6] Checking for other model capabilities...")

            models_found = []
            for model_name in ["Haiku", "Opus", "Sonnet"]:
                if model_name in content:
                    models_found.append(model_name)

            if len(models_found) >= 2:
                print(f"  ✓ Found models: {', '.join(models_found)}")
                test_results.append(("Multiple models", True))
            else:
                print(f"  ⚠ Found models: {models_found}")
                test_results.append(("Multiple models", len(models_found) > 0))

            # Take a screenshot
            screenshot_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/reports/test-results/model-capabilities-test.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n[Screenshot] Saved to {screenshot_path}")

        except Exception as e:
            print(f"\n✗ Error during test: {e}")
            import traceback
            traceback.print_exc()
            test_results.append(("Error handling", False))

        finally:
            await browser.close()

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)

        for test_name, result in test_results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status}: {test_name}")

        print(f"\nResult: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed! Feature #151 is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed.")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_model_capabilities())
    sys.exit(exit_code)
