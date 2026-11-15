"""NASA Wind Data Sonification Engine — Member 4 Deliverable.

This module provides a UI-independent, deterministic audio sonification engine
that maps pre-extracted numerical windspeed values (in m/s) to musical pitches,
synthesizes 16-bit PCM WAV audio in memory, and generates screen-reader-friendly
textual descriptions.

NASA Project Context:
- Members 1-3: Responsible for visualization selection, color extraction, and
  calibrated numerical speed estimation.
- Member 4 (this module): Validates numeric inputs, maps windspeeds to tones,
  encodes clean WAV audio bytes, and generates accessible descriptions.
- Member 5: Imports `sonify()` and `describe()` into the team's combined app.
"""

from __future__ import annotations

import io
import json
import math
from pathlib import Path
from typing import Any, List, Tuple, Union

import numpy as np
import scipy.io.wavfile

# ============================================================================
# CONSTANTS & CONTRACT DEFINITIONS
# ============================================================================

SAMPLE_RATE: int = 44100  # 44.1 kHz standard audio CD sample rate
TONE_DURATION_SEC: float = 0.45  # Duration of each region tone in seconds
GAP_DURATION_SEC: float = 0.08  # Silence duration between consecutive tones
FADE_DURATION_SEC: float = 0.01  # 10 ms smooth fade in/out to avoid clicks/pops
TONE_AMPLITUDE: float = 0.20  # ~20% of full-scale 16-bit PCM (nominal ~6553)

MIN_REGIONS: int = 1
MAX_REGIONS: int = 100
MAX_REGION_NAME_LEN: int = 80
SUPPORTED_UNIT: str = "m/s"
MIN_SPEED_MPS: float = 0.0
MAX_SPEED_MPS: float = 25.0

# Illustrative sonification scale (5 categories from 0 to 25 m/s)
# Note: This is an illustrative demonstrative scale, not an official NASA wind classification.
SCALE_MAPPING = (
    # (min_inclusive, max_exclusive_or_inclusive, note, frequency_hz, category_label)
    (0.0, 5.0, "C4", 261.63, "Very low"),
    (5.0, 10.0, "D4", 293.66, "Low"),
    (10.0, 15.0, "E4", 329.63, "Moderate"),
    (15.0, 20.0, "G4", 392.00, "High"),
    (20.0, 25.0, "C5", 523.25, "Very high"),
)


# ============================================================================
# PUBLIC INTERFACE & MAPPING HELPERS
# ============================================================================

def map_speed_to_note(speed: float) -> Tuple[str, float, str]:
    """Map a validated windspeed value in m/s to its note, frequency, and category.

    Categories:
      - 0 <= speed < 5 m/s:   C4 (261.63 Hz), 'Very low'
      - 5 <= speed < 10 m/s:  D4 (293.66 Hz), 'Low'
      - 10 <= speed < 15 m/s: E4 (329.63 Hz), 'Moderate'
      - 15 <= speed < 20 m/s: G4 (392.00 Hz), 'High'
      - 20 <= speed <= 25 m/s: C5 (523.25 Hz), 'Very high'

    Args:
        speed: Finite float between 0.0 and 25.0 inclusive.

    Returns:
        Tuple of (note_name, frequency_hz, category_label).

    Raises:
        ValueError: If speed is outside [0.0, 25.0], NaN, or Infinite.
    """
    if isinstance(speed, bool) or not isinstance(speed, (int, float)):
        raise ValueError(f"Speed must be a numeric value, got {type(speed).__name__}.")
    if math.isnan(speed) or math.isinf(speed):
        raise ValueError("Speed must be a finite number; NaN and infinity are rejected.")
    if speed < MIN_SPEED_MPS:
        raise ValueError(
            f"Negative windspeed ({speed} m/s) is invalid. Speeds must be >= {MIN_SPEED_MPS} m/s."
        )
    if speed > MAX_SPEED_MPS:
        raise ValueError(
            f"Windspeed {speed} m/s exceeds maximum supported scale ({MAX_SPEED_MPS} m/s). "
            "To support higher hurricane/storm tiers, the sonification scale must be explicitly extended."
        )

    # 0 <= speed < 5
    if speed < 5.0:
        return "C4", 261.63, "Very low"
    # 5 <= speed < 10
    if speed < 10.0:
        return "D4", 293.66, "Low"
    # 10 <= speed < 15
    if speed < 15.0:
        return "E4", 329.63, "Moderate"
    # 15 <= speed < 20
    if speed < 20.0:
        return "G4", 392.00, "High"
    # 20 <= speed <= 25
    return "C5", 523.25, "Very high"


def get_audio_legend() -> List[dict]:
    """Return the reference mapping table for documentation and UI legends."""
    return [
        {
            "range": "0 to <5 m/s",
            "note": "C4",
            "frequency_hz": 261.63,
            "category": "Very low",
        },
        {
            "range": "5 to <10 m/s",
            "note": "D4",
            "frequency_hz": 293.66,
            "category": "Low",
        },
        {
            "range": "10 to <15 m/s",
            "note": "E4",
            "frequency_hz": 329.63,
            "category": "Moderate",
        },
        {
            "range": "15 to <20 m/s",
            "note": "G4",
            "frequency_hz": 392.00,
            "category": "High",
        },
        {
            "range": "20 to 25 m/s",
            "note": "C5",
            "frequency_hz": 523.25,
            "category": "Very high",
        },
    ]


# ============================================================================
# VALIDATION & PARSING FUNCTIONS
# ============================================================================

def validate_regions(regions: Any) -> List[dict]:
    """Validate a list of region entries according to the Member 3 contract.

    Rules:
      - Must be a non-empty list of 1 to 100 items.
      - Preserves ordering strictly.
      - Each item must be a dictionary with 'region' (nonempty str <= 80 chars)
        and 'speed' (finite numeric between 0 and 25 m/s).
      - Rejects booleans, strings posing as numbers, NaN, infinity, negative values,
        and values > 25 m/s.
      - Does NOT mutate the input list or input dictionaries.

    Returns:
        A new list of validated dictionaries with normalized float speeds.

    Raises:
        ValueError: If any validation rule is violated.
    """
    if not isinstance(regions, list):
        raise ValueError(f"'regions' must be a JSON array (list), got {type(regions).__name__}.")
    if len(regions) < MIN_REGIONS:
        raise ValueError("The 'regions' list is empty. At least one region is required.")
    if len(regions) > MAX_REGIONS:
        raise ValueError(
            f"The 'regions' list contains {len(regions)} entries, exceeding the maximum of {MAX_REGIONS}."
        )

    validated_regions: List[dict] = []
    for idx, entry in enumerate(regions, start=1):
        if not isinstance(entry, dict):
            raise ValueError(
                f"Region entry #{idx} is not an object/dictionary (got {type(entry).__name__})."
            )

        if "region" not in entry:
            raise ValueError(f"Region entry #{idx} is missing the required 'region' key.")
        if "speed" not in entry:
            raise ValueError(f"Region entry #{idx} is missing the required 'speed' key.")

        region_name = entry["region"]
        if not isinstance(region_name, str):
            raise ValueError(
                f"Region entry #{idx}: 'region' must be a string, got {type(region_name).__name__}."
            )
        cleaned_region = region_name.strip()
        if not cleaned_region:
            raise ValueError(f"Region entry #{idx}: 'region' name cannot be empty or whitespace.")
        if len(region_name) > MAX_REGION_NAME_LEN:
            raise ValueError(
                f"Region entry #{idx}: 'region' name exceeds maximum length of {MAX_REGION_NAME_LEN} characters."
            )

        speed_val = entry["speed"]
        if isinstance(speed_val, bool) or not isinstance(speed_val, (int, float)):
            raise ValueError(
                f"Region entry #{idx} ('{region_name}'): 'speed' must be a numeric value, got {type(speed_val).__name__}."
            )
        if math.isnan(speed_val) or math.isinf(speed_val):
            raise ValueError(
                f"Region entry #{idx} ('{region_name}'): 'speed' must be a finite number."
            )
        if speed_val < MIN_SPEED_MPS:
            raise ValueError(
                f"Region entry #{idx} ('{region_name}'): speed {speed_val} m/s is negative. Values must be >= 0."
            )
        if speed_val > MAX_SPEED_MPS:
            raise ValueError(
                f"Region entry #{idx} ('{region_name}'): speed {speed_val} m/s exceeds max scale of {MAX_SPEED_MPS} m/s."
            )

        validated_regions.append(
            {
                "region": region_name,
                "speed": float(speed_val),
            }
        )

    return validated_regions


def validate_payload(payload: Any) -> List[dict]:
    """Validate a parsed JSON payload object against the Member 3 schema.

    The payload must have:
      - "unit": "m/s"
      - "regions": list of region dictionaries

    Returns:
        A new list of validated region dictionaries.
    """
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload must be an object, got {type(payload).__name__}.")

    if "unit" not in payload:
        raise ValueError("Missing required key 'unit' in JSON payload.")
    unit = payload["unit"]
    if unit != SUPPORTED_UNIT:
        raise ValueError(
            f"Unsupported unit '{unit}'. Only '{SUPPORTED_UNIT}' is supported in this release."
        )

    if "regions" not in payload:
        raise ValueError("Missing required key 'regions' in JSON payload.")

    return validate_regions(payload["regions"])


def parse_payload(payload: Union[dict, str, bytes]) -> List[dict]:
    """Parse and validate a raw JSON string, bytes buffer, or dictionary.

    Args:
        payload: Dict, JSON string, or UTF-8 encoded bytes.

    Returns:
        A list of validated region dictionaries with 'region' (str) and 'speed' (float).

    Raises:
        ValueError: If JSON is malformed or violates the schema.
    """
    if isinstance(payload, (str, bytes)):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON syntax: {exc.msg} (line {exc.lineno}, column {exc.colno})") from exc
    elif isinstance(payload, dict):
        parsed = payload
    else:
        raise ValueError(
            f"Payload must be a dictionary, string, or bytes, got {type(payload).__name__}."
        )

    return validate_payload(parsed)


# ============================================================================
# AUDIO SYNTHESIS ENGINE
# ============================================================================

def generate_tone(
    frequency_hz: float,
    duration_sec: float = TONE_DURATION_SEC,
    sample_rate: int = SAMPLE_RATE,
    amplitude: float = TONE_AMPLITUDE,
    fade_duration_sec: float = FADE_DURATION_SEC,
) -> np.ndarray:
    """Generate a clean mono sine-wave tone with linear fade-in and fade-out ramps.

    Args:
        frequency_hz: Tone frequency in Hertz.
        duration_sec: Tone duration in seconds.
        sample_rate: Audio sampling rate in Hz (default 44100).
        amplitude: Peak amplitude fraction (0.0 to 1.0, nominal 0.20).
        fade_duration_sec: Duration of fade ramp in seconds (default 10 ms).

    Returns:
        1D NumPy array of float32 samples.
    """
    total_samples = int(round(duration_sec * sample_rate))
    if total_samples <= 0:
        return np.zeros(0, dtype=np.float32)

    # Time array: t = [0, 1/fs, 2/fs, ... (N-1)/fs]
    t = np.arange(total_samples, dtype=np.float64) / float(sample_rate)
    tone = amplitude * np.sin(2.0 * np.pi * frequency_hz * t)

    # Apply 10 ms smooth fade-in and fade-out to prevent clicks and pops
    fade_samples = int(round(fade_duration_sec * sample_rate))
    if fade_samples > 0 and 2 * fade_samples <= total_samples:
        fade_in = np.linspace(0.0, 1.0, fade_samples, endpoint=True)
        fade_out = np.linspace(1.0, 0.0, fade_samples, endpoint=True)
        tone[:fade_samples] *= fade_in
        tone[-fade_samples:] *= fade_out

    return tone.astype(np.float32)


def generate_silence(
    duration_sec: float = GAP_DURATION_SEC,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Generate a segment of mono silence (zeros)."""
    samples = int(round(duration_sec * sample_rate))
    return np.zeros(samples, dtype=np.float32)


def sonify(regions: List[dict]) -> bytes:
    """Synthesize 16-bit PCM mono WAV bytes from a sequence of region dictionaries.

    Public API for Member 5 and the demonstration application.
    Independent of Streamlit or any graphical user interface.

    Sequence generation:
      - Iterates through `regions` in exact input order.
      - Synthesizes a 0.45 s sine wave tone at the assigned frequency.
      - Inserts 0.08 s silence between consecutive tones (no trailing silence).
      - Converts samples to standard 16-bit signed PCM format.
      - Packs into a valid RIFF/WAVE container in memory.

    Args:
        regions: List of dicts, each containing 'region' and 'speed' (m/s).

    Returns:
        Standard 16-bit PCM WAV file content as in-memory bytes.

    Raises:
        ValueError: If input fails validation rules.
    """
    valid_regions = validate_regions(regions)

    audio_chunks: List[np.ndarray] = []
    num_regions = len(valid_regions)

    for idx, item in enumerate(valid_regions):
        speed = item["speed"]
        _note, freq_hz, _label = map_speed_to_note(speed)
        tone = generate_tone(freq_hz)
        audio_chunks.append(tone)

        # Append silence gap only between tones, not after the final tone
        if idx < num_regions - 1:
            audio_chunks.append(generate_silence())

    # Concatenate all audio segments
    full_audio = np.concatenate(audio_chunks)

    # Scale to 16-bit signed integer PCM (-32768 to 32767)
    # TONE_AMPLITUDE (0.20) keeps peak amplitude well within full scale (~6553)
    pcm16_data = np.clip(full_audio * 32767.0, -32768.0, 32767.0).astype(np.int16)

    # Encode to in-memory WAV using scipy.io.wavfile
    buffer = io.BytesIO()
    scipy.io.wavfile.write(buffer, SAMPLE_RATE, pcm16_data)
    return buffer.getvalue()


def describe(regions: List[dict]) -> List[str]:
    """Generate screen-reader-friendly textual descriptions for each region.

    Public API for Member 5 and accessible UI rendering.

    Args:
        regions: List of dicts with 'region' and 'speed'.

    Returns:
        List of human-readable description strings, one per region in order.

    Raises:
        ValueError: If input validation fails.
    """
    valid_regions = validate_regions(regions)
    descriptions: List[str] = []

    for item in valid_regions:
        name = item["region"]
        speed = item["speed"]
        note, freq, category = map_speed_to_note(speed)
        descriptions.append(
            f"Region '{name}': {speed:.1f} m/s — Category: {category} (Note {note}, {freq:.2f} Hz)"
        )

    return descriptions


# ============================================================================
# COMMAND-LINE ENTRY POINT
# ============================================================================

def main() -> None:
    """Run a standalone demonstration from the command line.

    Reads examples/sample_regions.json, validates it, synthesizes audio,
    writes outputs/sample_wind_audio.wav, and prints the descriptive mapping.
    """
    base_dir = Path(__file__).resolve().parent
    sample_file = base_dir / "examples" / "sample_regions.json"
    output_dir = base_dir / "outputs"
    output_file = output_dir / "sample_wind_audio.wav"

    print("=" * 70)
    print("NASA Wind Data Sonification — Member 4 Command-Line Demo")
    print("=" * 70)

    if not sample_file.exists():
        print(f"Error: Sample file not found at {sample_file}")
        return

    with open(sample_file, "r", encoding="utf-8") as f:
        raw_content = f.read()

    print(f"Reading sample input: {sample_file}")
    regions = parse_payload(raw_content)
    print(f"Validated {len(regions)} regions successfully.")

    print("\nDescriptive Mapping (Sequential Playback):")
    for line in describe(regions):
        print(f"  • {line}")

    print("\nSynthesizing 16-bit PCM WAV audio...")
    wav_bytes = sonify(regions)

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file, "wb") as f:
        f.write(wav_bytes)

    duration_sec = len(wav_bytes)  # approximate check
    print(f"Successfully generated audio file ({len(wav_bytes)} bytes):")
    print(f"  -> {output_file}")
    print("\nYou can open and play this WAV file in any standard media player.")
    print("=" * 70)


if __name__ == "__main__":
    main()
