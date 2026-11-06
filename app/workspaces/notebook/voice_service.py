"""Single integration boundary for local voice recording and transcription.

The notebook UI depends on this facade rather than individual voice backends.
"""
from __future__ import annotations

from app.workspaces.notebook.controller import NOTEBOOK_CATEGORIES, EngineeringNotebookController
from app.workspaces.notebook.microphone import MicrophoneRecorder
from app.workspaces.notebook.offline_speech import OfflineSpeechRecognizer, default_model_dir

__all__ = ["NOTEBOOK_CATEGORIES", "EngineeringNotebookController", "MicrophoneRecorder", "OfflineSpeechRecognizer", "default_model_dir"]
