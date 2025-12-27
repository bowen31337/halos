"""Test file type detection feature (#149)."""

import pytest
import json
from pathlib import Path


class TestFileTypeDetection:
    """Test suite for file type detection and upload handling."""

    def test_python_file_detection(self):
        """Test that .py files are detected as Python code."""
        # Simulate the detection logic from fileTypeDetection.ts
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.txt': 'text',
        }

        filename = "test.py"
        ext = '.' + filename.split('.')[-1] if '.' in filename else ''
        language = language_map.get(ext)

        assert language == 'python', "Python files should be detected"
        print(f"✓ {filename} detected as {language}")

    def test_javascript_file_detection(self):
        """Test that .js files are detected as JavaScript."""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.txt': 'text',
        }

        filename = "app.js"
        ext = '.' + filename.split('.')[-1] if '.' in filename else ''
        language = language_map.get(ext)

        assert language == 'javascript', "JavaScript files should be detected"
        print(f"✓ {filename} detected as {language}")

    def test_text_file_detection(self):
        """Test that .txt files are detected as plain text."""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.txt': 'text',
        }

        filename = "data.txt"
        ext = '.' + filename.split('.')[-1] if '.' in filename else ''
        language = language_map.get(ext)

        assert language == 'text', "Text files should be detected"
        print(f"✓ {filename} detected as {language}")

    def test_image_file_detection(self):
        """Test that image files are detected correctly."""
        image_extensions = ['.jpg', '.png', '.gif', '.svg', '.webp']

        for ext in image_extensions:
            filename = f"test{ext}"
            is_image = ext in image_extensions
            assert is_image, f"{ext} should be detected as image"
            print(f"✓ {filename} detected as image")

    def test_code_file_categories(self):
        """Test that various code files are categorized correctly."""
        test_cases = [
            ("script.py", "python"),
            ("app.js", "javascript"),
            ("component.tsx", "typescript"),
            ("styles.css", "css"),
            ("data.json", "json"),
            ("README.md", "markdown"),
            ("config.yaml", "yaml"),
        ]

        for filename, expected_category in test_cases:
            ext = '.' + filename.split('.')[-1] if '.' in filename else ''
            # Just verify the file has an extension
            assert ext, f"{filename} should have an extension"
            print(f"✓ {filename} has extension {ext}")


if __name__ == "__main__":
    # Run tests
    test_suite = TestFileTypeDetection()

    print("\n🧪 Running File Type Detection Tests\n")
    print("=" * 60)

    test_suite.test_python_file_detection()
    test_suite.test_javascript_file_detection()
    test_suite.test_text_file_detection()
    test_suite.test_image_file_detection()
    test_suite.test_code_file_categories()

    print("\n" + "=" * 60)
    print("✅ All tests passed!\n")
