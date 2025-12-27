"""Test Voice Input Feature

This test verifies that the Voice Input feature is properly implemented
in the ChatInput component.
"""

import pytest
from pathlib import Path


def test_voice_input_component_exists():
    """Test that ChatInput component has voice input functionality."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    assert chat_input_path.exists(), "ChatInput.tsx should exist"

    content = chat_input_path.read_text()

    # Check for speech recognition initialization
    assert "SpeechRecognition" in content, "Should have SpeechRecognition API"
    assert "isListening" in content, "Should have isListening state"
    assert "handleVoiceInput" in content, "Should have handleVoiceInput function"

    # Check for voice input button
    assert 'Voice input' in content or 'title="Stop recording"' in content, "Should have voice input button"


def test_voice_input_button_ui():
    """Test that voice input button is rendered with proper states."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for recording state styling
    assert "isRecording" in content, "Should track recording state"
    assert "animate-pulse" in content or "bg-red-500" in content, "Should have visual feedback for recording"

    # Check for microphone icon
    assert '<svg' in content and 'M19 11a7 7 0 01-7 7' in content, "Should have microphone icon"


def test_speech_recognition_initialization():
    """Test that Speech Recognition API is properly initialized."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for browser support detection
    assert "window.SpeechRecognition" in content or "window.webkitSpeechRecognition" in content, \
        "Should check for browser support"

    # Check for recognition configuration
    assert "continuous" in content, "Should enable continuous recording"
    assert "interimResults" in content, "Should enable interim results"

    # Check for event handlers
    assert "onresult" in content, "Should handle recognition results"
    assert "onerror" in content, "Should handle recognition errors"
    assert "onend" in content, "Should handle recognition end"


def test_voice_input_transcription():
    """Test that transcribed text is added to input field."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for updating input value with transcription
    assert "setInputValue(currentText)" in content or "setInputValue(" in content, \
        "Should update input value with transcribed text"

    # Check for updating store
    assert "setInputMessage(" in content, "Should update conversation store"


def test_voice_input_error_handling():
    """Test that voice input errors are handled properly."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for error handling
    assert "onerror" in content, "Should have error handler"
    assert "console.error" in content or "alert(" in content, "Should display errors"


def test_voice_integration_with_chat():
    """Test that voice input integrates with chat functionality."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Voice button should be disabled during streaming
    assert "disabled={isLoading || isStreaming}" in content or "isStreaming" in content, \
        "Voice button should respect streaming state"

    # Transcribed text should be sendable
    assert "handleSend" in content, "Should have send functionality"


def test_voice_input_browser_support_check():
    """Test that browser support is checked before enabling voice input."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for support flag
    assert "isSpeechRecognitionSupported" in content, \
        "Should track browser support"

    # Check for alert when not supported
    assert "is not supported in this browser" in content, \
        "Should alert user when not supported"


def test_voice_input_visual_feedback():
    """Test that visual feedback is provided during recording."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for recording indicator
    assert "isRecording" in content, "Should show recording state"

    # Check for different button states
    assert "bg-red-500" in content or "text-white" in content, \
        "Should change button appearance when recording"


def test_voice_input_start_stop():
    """Test that voice input can be started and stopped."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for toggle functionality
    assert "setIsListening(true)" in content, "Should start listening"
    assert "setIsListening(false)" in content, "Should stop listening"

    # Check for recognition start/stop
    assert "recognitionRef.current.start()" in content, "Should start recognition"
    assert "recognitionRef.current.stop()" in content, "Should stop recognition"


def test_voice_input_continuous_mode():
    """Test that continuous mode is enabled for longer recordings."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for continuous mode (JavaScript object literal syntax)
    assert 'continuous = true' in content or 'continuous: true' in content, "Should enable continuous mode"


def test_voice_input_interim_results():
    """Test that interim results are displayed during recording."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    content = chat_input_path.read_text()

    # Check for interim results configuration (JavaScript object literal syntax)
    assert 'interimResults = true' in content or 'interimResults: true' in content, "Should enable interim results"

    # Check for handling both final and interim transcripts
    assert "finalTranscript" in content and "interimTranscript" in content, \
        "Should handle both transcript types"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
