import os
import numpy as np
from pydub import AudioSegment
from kokoro.pipeline import KPipeline

# ------------------------
# Global pipeline cache
# ------------------------
_pipeline_cache = {}

def get_pipeline(lang_code="a"):
    """Initialize Kokoro pipeline once per language code."""
    if lang_code not in _pipeline_cache:
        _pipeline_cache[lang_code] = KPipeline(
            lang_code=lang_code,
            repo_id="hexgrad/Kokoro-82M"
        )
    return _pipeline_cache[lang_code]

# ------------------------
# Batched speech generation
# ------------------------
def generate_batched_speech(voice: str, texts: list[str], lang_code="a", sample_rate=24000):
    """
    Generate clean MP3-ready audio segments for a batch of texts.

    Args:
        voice (str): Kokoro voice name.
        texts (list[str]): List of text strings to synthesize.
        lang_code (str): Language code.
        sample_rate (int): Output sample rate.

    Returns:
        list of tuples: [(text, AudioSegment), ...]
    """
    pipeline = get_pipeline(lang_code)
    results = []

    for text in texts:
        generator = pipeline(
            text,
            voice=voice,
            speed=1,
            split_pattern=r'\n+'
        )
        audio_chunks = []
        for gs, ps, audio in generator:
            audio_chunks.append(audio)

        if not audio_chunks:
            continue

        # Concatenate chunks
        audio_concat = np.concatenate(audio_chunks).astype(np.float32)

        # Normalize to [-1, 1] to avoid noise/clipping
        peak = np.max(np.abs(audio_concat))
        if peak > 0:
            audio_concat /= peak

        # Convert to int16 and wrap in AudioSegment
        audio_int16 = (audio_concat * 32767).astype(np.int16)
        seg = AudioSegment(
            audio_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        results.append((text, seg))

    return results
