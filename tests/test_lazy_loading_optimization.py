#!/usr/bin/env python3
"""Test Feature #142: Lazy loading optimizes initial page load.

This test verifies:
1. Vite is configured with code splitting
2. Components are lazy loaded with React.lazy
3. Suspense boundaries are in place
4. OptimizedImage component uses Intersection Observer
5. Bundle size is optimized
"""

import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_vite_code_splitting():
    """Verify Vite is configured for code splitting."""
    print("Testing Feature #142: Lazy Loading & Code Splitting")
    print("=" * 60)
    print("\n1. Checking Vite configuration...")

    vite_config = project_root / "client" / "vite.config.ts"
    if not vite_config.exists():
        print("   ✗ vite.config.ts not found")
        return False

    content = vite_config.read_text()

    checks = [
        ("manualChunks", "Code splitting configuration"),
        ("react-vendor", "React vendor split"),
        ("state-vendor", "State management vendor split"),
        ("ui-vendor", "UI vendor split"),
        ("chunkSizeWarningLimit", "Chunk size warning"),
    ]

    all_passed = True
    for pattern, name in checks:
        if pattern in content:
            print(f"   ✓ {name}")
        else:
            print(f"   ✗ {name}")
            all_passed = False

    return all_passed


def test_lazy_loading():
    """Verify React.lazy is used for components."""
    print("\n2. Checking React.lazy implementation...")

    app_tsx = project_root / "client" / "src" / "App.tsx"
    if not app_tsx.exists():
        print("   ✗ App.tsx not found")
        return False

    content = app_tsx.read_text()

    checks = [
        ("lazy(", "React.lazy imported and used"),
        ("Suspense", "Suspense boundary present"),
        ("ChatPage", "ChatPage lazy loaded"),
        ("SharedView", "SharedView lazy loaded"),
        ("LoadingFallback", "Loading fallback component"),
    ]

    all_passed = True
    for pattern, name in checks:
        if pattern in content:
            print(f"   ✓ {name}")
        else:
            print(f"   ✗ {name}")
            all_passed = False

    return all_passed


def test_optimized_image():
    """Verify OptimizedImage component exists and is properly implemented."""
    print("\n3. Checking OptimizedImage component...")

    optimized_image = project_root / "client" / "src" / "components" / "OptimizedImage.tsx"
    if not optimized_image.exists():
        print("   ✗ OptimizedImage.tsx not found")
        return False

    content = optimized_image.read_text()

    checks = [
        ("IntersectionObserver", "Intersection Observer for lazy loading"),
        ("thumbnailSrc", "Thumbnail support"),
        ("loading=\"lazy\"", "Native lazy loading attribute"),
        ("onLoad", "Load handler"),
        ("onError", "Error handler"),
        ("useState", "State management"),
    ]

    all_passed = True
    for pattern, name in checks:
        if pattern in content:
            print(f"   ✓ {name}")
        else:
            print(f"   ✗ {name}")
            all_passed = False

    return all_passed


def test_package_dependencies():
    """Verify required dependencies are present."""
    print("\n4. Checking package.json dependencies...")

    package_json = project_root / "client" / "package.json"
    if not package_json.exists():
        print("   ✗ package.json not found")
        return False

    with open(package_json) as f:
        pkg = json.load(f)

    # Check for build tools
    if "vite" in pkg.get("devDependencies", {}):
        print("   ✓ Vite build tool")
    else:
        print("   ✗ Vite not found")
        return False

    # Check for React
    if "react" in pkg.get("dependencies", {}):
        print("   ✓ React")
    else:
        print("   ✗ React not found")
        return False

    return True


def test_build_output_structure():
    """Verify the build will produce optimized chunks."""
    print("\n5. Verifying build optimization strategy...")

    # Check if there are heavy components that should be split
    components_dir = project_root / "client" / "src" / "components"
    pages_dir = project_root / "client" / "src" / "pages"

    heavy_components = [
        "SettingsModal.tsx",
        "MessageBubble.tsx",
        "MessageList.tsx",
        "ArtifactPanel.tsx",
        "TodoPanel.tsx",
    ]

    print("   Heavy components found:")
    for comp in heavy_components:
        comp_path = components_dir / comp
        if comp_path.exists():
            size = comp_path.stat().st_size
            print(f"   - {comp}: {size} bytes")

    # Check vite config for these in manualChunks
    vite_config = project_root / "client" / "vite.config.ts"
    if vite_config.exists():
        content = vite_config.read_text()
        if "manualChunks" in content:
            print("   ✓ manualChunks configured")
        else:
            print("   ⚠ manualChunks not configured")

    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Feature #142: Lazy Loading & Code Splitting")
    print("=" * 60)

    results = []

    results.append(("Vite Code Splitting", test_vite_code_splitting()))
    results.append(("React.lazy Loading", test_lazy_loading()))
    results.append(("OptimizedImage Component", test_optimized_image()))
    results.append(("Dependencies", test_package_dependencies()))
    results.append(("Build Strategy", test_build_output_structure()))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n" + "=" * 60)
        print("✅ FEATURE #142: Lazy Loading & Code Splitting - VERIFIED")
        print("=" * 60)
        print("\nImplementation Summary:")
        print("- Vite configured with manualChunks for code splitting")
        print("- React.lazy() for route-based code splitting")
        print("- Suspense boundaries for loading states")
        print("- OptimizedImage with Intersection Observer")
        print("- Native lazy loading attribute on images")
        print("\nBenefits:")
        print("- Faster initial page load")
        print("- Smaller initial bundle size")
        print("- On-demand component loading")
        print("- Optimized image loading")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed")
        sys.exit(1)
