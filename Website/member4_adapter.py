"""NASA Wind Data Sonification Engine — Member 4 Extended Adapter.

Minimal-change adapter that connects Member 2/3 scientific windspeed exports
(CSV / JSON) to Member 4's audio sonification engine.

Key Capabilities:
1. Reuses original `sonification.py` DSP, tone generation, and 0-25 m/s scale.
2. Extends musical pitch mapping for speeds >25 m/s up to 40 m/s:
   - 25 < speed < 30 m/s   -> D5 (587.33 Hz), 'Storm (Extended)'
   - 30 <= speed < 35 m/s  -> E5 (659.25 Hz), 'Violent Storm (Extended)'
   - 35 <= speed <= 40 m/s -> G5 (783.99 Hz), 'Hurricane / Extreme (Extended)'
3. Ingests Member 2/3 scientific CSV (`windspeed_output_for_member4.csv`),
   mapped JSON (`windspeed_grid_mapped.json`), or legacy Member 4 payloads.
4. Generates synchronized per-record datasets with exact note names, frequencies,
   confidence flags, tone start times, and durations.
5. Synthesizes 44.1 kHz 16-bit PCM WAV audio with safe, verified RIFF LIST/INFO
   ICMT metadata embedding.
"""

from __future__ import annotations

import csv
import io
import json
import math
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import scipy.io.wavfile

# Re-use existing Member 4 core module
import sonification

# ============================================================================
# EXTENDED SCALE CONSTANTS
# ============================================================================

MAX_SPEED_MPS_BASE: float = sonification.MAX_SPEED_MPS  # 25.0 m/s
MAX_SPEED_MPS_EXTENDED: float = 40.0  # 40.0 m/s upper boundary for extended scale
MIN_SPEED_MPS: float = sonification.MIN_SPEED_MPS  # 0.0 m/s

# Extended scale mapping tuples: (min_exclusive_or_inclusive, max_inclusive, note, freq_hz, category, tier_type)
EXTENDED_TIERS = (
    (25.0, 30.0, "D5", 587.33, "Storm (Extended)", "Extended Prototype"),
    (30.0, 35.0, "E5", 659.25, "Violent Storm (Extended)", "Extended Prototype"),
    (35.0, 40.0, "G5", 783.99, "Hurricane / Extreme (Extended)", "Extended Prototype"),
)


# ============================================================================
# PITCH MAPPING WITH EXTENDED RANGE
# ============================================================================

def map_speed_to_note_extended(speed: float) -> Tuple[str, float, str]:
    """Map a windspeed value in m/s to its note name, frequency, and category.

    Preserves 100% of original Member 4 mappings for 0.0 to 25.0 m/s:
      0.0 <= speed < 5.0   -> C4 (261.63 Hz), 'Very low'
      5.0 <= speed < 10.0  -> D4 (293.66 Hz), 'Low'
      10.0 <= speed < 15.0 -> E4 (329.63 Hz), 'Moderate'
      15.0 <= speed < 20.0 -> G4 (392.00 Hz), 'High'
      20.0 <= speed <= 25.0 -> C5 (523.25 Hz), 'Very high'

    Extended tiers for scientific measurements above 25.0 m/s up to 40.0 m/s:
      25.0 < speed < 30.0  -> D5 (587.33 Hz), 'Storm (Extended)'
      30.0 <= speed < 35.0 -> E5 (659.25 Hz), 'Violent Storm (Extended)'
      35.0 <= speed <= 40.0 -> G5 (783.99 Hz), 'Hurricane / Extreme (Extended)'

    Boundary convention:
      - At 25.0 m/s: returns C5 (523.25 Hz), matching original specification exactly.
      - Speeds > 25.0 and < 30.0: D5 (587.33 Hz).
      - Speeds >= 30.0 and < 35.0: E5 (659.25 Hz).
      - Speeds >= 35.0 and <= 40.0: G5 (783.99 Hz).

    Raises:
        ValueError: If speed is non-numeric, NaN, infinite, negative, or > 40.0 m/s.
    """
    if isinstance(speed, bool) or not isinstance(speed, (int, float)):
        raise ValueError(f"Speed must be a numeric value, got {type(speed).__name__}.")
    if math.isnan(speed) or math.isinf(speed):
        raise ValueError("Speed must be a finite number; NaN and infinity are rejected.")
    if speed < MIN_SPEED_MPS:
        raise ValueError(
            f"Negative windspeed ({speed} m/s) is invalid. Speeds must be >= {MIN_SPEED_MPS} m/s."
        )
    if speed > MAX_SPEED_MPS_EXTENDED:
        raise ValueError(
            f"Windspeed {speed:.2f} m/s exceeds maximum supported extended scale ({MAX_SPEED_MPS_EXTENDED} m/s). "
            "Speeds above 40 m/s are rejected to avoid falsifying pitch classifications."
        )

    # For 0.0 <= speed <= 25.0, reuse original sonification mapping unchanged
    if speed <= MAX_SPEED_MPS_BASE:
        return sonification.map_speed_to_note(speed)

    # Extended tiers for 25.0 < speed <= 40.0
    if speed < 30.0:
        return "D5", 587.33, "Storm (Extended)"
    if speed < 35.0:
        return "E5", 659.25, "Violent Storm (Extended)"
    return "G5", 783.99, "Hurricane / Extreme (Extended)"


def get_extended_audio_legend() -> List[Dict[str, Any]]:
    """Return the complete 8-tier reference legend table (5 standard + 3 extended)."""
    legend: List[Dict[str, Any]] = []
    # Standard tiers
    for item in sonification.get_audio_legend():
        legend.append(
            {
                "range": item["range"],
                "note": item["note"],
                "frequency_hz": item["frequency_hz"],
                "category": item["category"],
                "tier_type": "Standard",
            }
        )
    # Extended tiers
    legend.extend(
        [
            {
                "range": ">25 to <30 m/s",
                "note": "D5",
                "frequency_hz": 587.33,
                "category": "Storm (Extended)",
                "tier_type": "Extended Prototype",
            },
            {
                "range": "30 to <35 m/s",
                "note": "E5",
                "frequency_hz": 659.25,
                "category": "Violent Storm (Extended)",
                "tier_type": "Extended Prototype",
            },
            {
                "range": "35 to 40 m/s",
                "note": "G5",
                "frequency_hz": 783.99,
                "category": "Hurricane / Extreme (Extended)",
                "tier_type": "Extended Prototype",
            },
        ]
    )
    return legend


# ============================================================================
# MULTI-FORMAT INPUT PARSER
# ============================================================================

def parse_windspeed_records(
    data_source: Union[str, Path, bytes, List[Dict[str, Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Parse windspeed records from Member 2/3 CSV, Member 2/3 JSON, or Member 4 JSON.

    Supports:
      1. Member 2/3 CSV (`windspeed_output_for_member4.csv`):
         Columns: region_id, region_name, windspeed_mps, confidence, grid_row, grid_col, ...
      2. Member 2/3 mapped JSON (`windspeed_grid_mapped.json`):
         Dictionary containing 'cells' list.
      3. Member 4 legacy JSON (`{"unit": "m/s", "regions": [...]}`).
      4. In-memory list of dicts.

    Preserves row order strictly. Rejects NaN, Inf, and speeds outside [0, 40] m/s.

    Returns:
        List of normalized record dictionaries ready for table display and audio synthesis.
    """
    raw_records: List[Dict[str, Any]] = []

    # If Path or string path pointing to existing file
    if isinstance(data_source, (str, Path)) and not isinstance(data_source, bytes):
        path_obj = Path(data_source)
        if path_obj.is_file():
            content_bytes = path_obj.read_bytes()
            return parse_windspeed_records(content_bytes)
        # If it's a raw string containing CSV or JSON
        data_str = str(data_source).strip()
        if data_str.startswith("{") or data_str.startswith("["):
            try:
                parsed_json = json.loads(data_str)
                return parse_windspeed_records(parsed_json)
            except json.JSONDecodeError:
                pass
        # Fall back to parsing as CSV text
        return _parse_csv_text(data_str)

    elif isinstance(data_source, bytes):
        # Try JSON first, then CSV
        try:
            text = data_source.decode("utf-8")
        except UnicodeDecodeError:
            text = data_source.decode("latin-1")
        text_strip = text.strip()
        if text_strip.startswith("{") or text_strip.startswith("["):
            try:
                parsed_json = json.loads(text)
                return parse_windspeed_records(parsed_json)
            except json.JSONDecodeError:
                pass
        return _parse_csv_text(text)

    elif isinstance(data_source, dict):
        if "cells" in data_source and isinstance(data_source["cells"], list):
            raw_records = data_source["cells"]
        elif "regions" in data_source and isinstance(data_source["regions"], list):
            raw_records = data_source["regions"]
        elif "grid_cells" in data_source and isinstance(data_source["grid_cells"], list):
            raw_records = data_source["grid_cells"]
        else:
            raise ValueError(
                "JSON dictionary must contain 'cells' (Member 3) or 'regions' (Member 4) array."
            )

    elif isinstance(data_source, list):
        raw_records = data_source
    else:
        raise ValueError(f"Unsupported data source type: {type(data_source).__name__}")

    if not raw_records:
        raise ValueError("Input dataset contains zero records.")

    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw_records):
        if not isinstance(item, dict):
            raise ValueError(f"Record index #{idx} is not an object/dictionary.")

        # Extract windspeed
        speed_raw = None
        for key in ("windspeed_mps", "speed", "windspeed", "speed_mps"):
            if key in item and item[key] is not None:
                speed_raw = item[key]
                break
        if speed_raw is None:
            raise ValueError(f"Record index #{idx} is missing a windspeed value.")

        if isinstance(speed_raw, bool) or not isinstance(speed_raw, (int, float, str)):
            raise ValueError(f"Record index #{idx}: invalid speed type {type(speed_raw).__name__}.")
        try:
            speed_val = float(speed_raw)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Record index #{idx}: cannot convert speed '{speed_raw}' to float.") from exc

        # Extract identifier & name
        region_id = item.get("region_id") or item.get("id") or f"REG_{idx + 1:03d}"
        region_name = item.get("region_name") or item.get("region") or item.get("name") or str(region_id)

        # Extract grid coordinates
        grid_row = item.get("grid_row")
        if grid_row is None:
            grid_row = item.get("row")
        grid_col = item.get("grid_col")
        if grid_col is None:
            grid_col = item.get("col")

        if grid_row is not None:
            try:
                grid_row = int(grid_row)
            except (ValueError, TypeError):
                grid_row = None
        if grid_col is not None:
            try:
                grid_col = int(grid_col)
            except (ValueError, TypeError):
                grid_col = None

        confidence = str(item.get("confidence", "Specified")).strip()
        if not confidence:
            confidence = "Specified"

        # Map to note & frequency
        note, freq_hz, category = map_speed_to_note_extended(speed_val)

        rec = {
            "record_index": idx,
            "region_id": str(region_id),
            "region_name": str(region_name),
            "grid_row": grid_row,
            "grid_col": grid_col,
            "windspeed_mps": speed_val,
            "note": note,
            "frequency_hz": freq_hz,
            "category": category,
            "confidence": confidence,
            "tone_start_seconds": 0.0,  # Will be populated during audio sequencing
            "tone_duration_seconds": sonification.TONE_DURATION_SEC,
            "audio_included": True,
        }
        normalized.append(rec)

    return normalized


def _parse_csv_text(text: str) -> List[Dict[str, Any]]:
    """Parse CSV text lines into dictionaries."""
    stream = io.StringIO(text)
    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        raise ValueError("CSV data is empty or missing headers.")
    records: List[Dict[str, Any]] = [row for row in reader]
    return parse_windspeed_records(records)


# ============================================================================
# RIFF/WAVE METADATA EMBEDDING & EXTRACTION
# ============================================================================

def embed_riff_comment(wav_bytes: bytes, comment: str) -> bytes:
    """Safely embed an informational text comment into a WAV file via RIFF LIST/INFO ICMT chunk.

    Guarantees:
      - Valid RIFF/WAVE container structure preserved.
      - Maintains 2-byte word alignment padding required by the RIFF specification.
      - Output remains 100% playable and readable by scipy.io.wavfile and standard media players.
    """
    if len(wav_bytes) < 12 or wav_bytes[:4] != b"RIFF" or wav_bytes[8:12] != b"WAVE":
        raise ValueError("Input bytes do not represent a valid RIFF/WAVE file.")

    # UTF-8 comment null-terminated
    comment_payload = comment.encode("utf-8") + b"\x00"
    if len(comment_payload) % 2 != 0:
        comment_payload += b"\x00"

    # ICMT subchunk: ID (4 bytes) + size (4 bytes little-endian) + data
    icmt_chunk = b"ICMT" + struct.pack("<I", len(comment_payload)) + comment_payload

    # LIST chunk: ID (4 bytes) + size (4 bytes) + 'INFO' (4 bytes) + subchunks
    list_payload = b"INFO" + icmt_chunk
    list_chunk = b"LIST" + struct.pack("<I", len(list_payload)) + list_payload

    # Append LIST chunk and update outer RIFF size header
    new_data = wav_bytes + list_chunk
    new_riff_size = len(new_data) - 8
    updated_wav = new_data[:4] + struct.pack("<I", new_riff_size) + new_data[8:]
    return updated_wav


def extract_riff_comment(wav_bytes: bytes) -> Optional[str]:
    """Extract embedded RIFF LIST/INFO ICMT text comment from WAV bytes if present."""
    if len(wav_bytes) < 12 or wav_bytes[:4] != b"RIFF" or wav_bytes[8:12] != b"WAVE":
        return None

    offset = 12
    total_len = len(wav_bytes)

    while offset + 8 <= total_len:
        chunk_id = wav_bytes[offset : offset + 4]
        chunk_size = struct.unpack("<I", wav_bytes[offset + 4 : offset + 8])[0]
        offset += 8

        if chunk_id == b"LIST" and offset + chunk_size <= total_len:
            list_type = wav_bytes[offset : offset + 4]
            if list_type == b"INFO":
                sub_offset = offset + 4
                sub_end = offset + chunk_size
                while sub_offset + 8 <= sub_end:
                    sub_id = wav_bytes[sub_offset : sub_offset + 4]
                    sub_size = struct.unpack("<I", wav_bytes[sub_offset + 4 : sub_offset + 8])[0]
                    sub_offset += 8
                    if sub_id == b"ICMT":
                        raw_comment = wav_bytes[sub_offset : sub_offset + sub_size]
                        return raw_comment.rstrip(b"\x00").decode("utf-8", errors="replace")
                    sub_offset += sub_size + (sub_size % 2)
        offset += chunk_size + (chunk_size % 2)

    return None


# ============================================================================
# AUDIO SYNTHESIS & TIMING SYNCHRONIZATION
# ============================================================================

def sonify_records(
    records: List[Dict[str, Any]],
    include_low_confidence: bool = True,
    embed_metadata: bool = True,
) -> Tuple[bytes, List[Dict[str, Any]]]:
    """Synthesize 16-bit PCM WAV audio from ordered records and calculate exact timing.

    Args:
        records: List of normalized record dicts from parse_windspeed_records().
        include_low_confidence: If False, skips tone generation for rows flagged as
                                'Low / Potential Non-Data', keeping them in table.
        embed_metadata: If True, embeds compact mapping into RIFF LIST/INFO ICMT.

    Returns:
        Tuple of (wav_bytes, synchronized_records_with_exact_timing).
    """
    if not records:
        raise ValueError("Cannot sonify empty records list.")

    # Create shallow copies of records to ensure immutability of inputs
    synced_records: List[Dict[str, Any]] = [dict(r) for r in records]

    # Determine which records produce audio
    for rec in synced_records:
        conf_lower = str(rec.get("confidence", "")).lower()
        is_low_conf = "low" in conf_lower or "non-data" in conf_lower or "land/cloud" in conf_lower
        if not include_low_confidence and is_low_conf:
            rec["audio_included"] = False
        else:
            rec["audio_included"] = True

    audio_chunks: List[np.ndarray] = []
    current_time_sec = 0.0

    included_indices = [i for i, r in enumerate(synced_records) if r["audio_included"]]

    for rank, idx in enumerate(included_indices):
        rec = synced_records[idx]
        freq_hz = rec["frequency_hz"]
        tone = sonification.generate_tone(freq_hz)
        audio_chunks.append(tone)

        rec["tone_start_seconds"] = round(current_time_sec, 4)
        rec["tone_duration_seconds"] = sonification.TONE_DURATION_SEC

        current_time_sec += sonification.TONE_DURATION_SEC

        # Gap between tones (no trailing silence)
        if rank < len(included_indices) - 1:
            audio_chunks.append(sonification.generate_silence())
            current_time_sec += sonification.GAP_DURATION_SEC

    # Records that were excluded from audio
    for rec in synced_records:
        if not rec["audio_included"]:
            rec["tone_start_seconds"] = None
            rec["tone_duration_seconds"] = 0.0

    if not audio_chunks:
        # Edge case: all records excluded; produce 0.5s silence
        full_audio = sonification.generate_silence(0.5)
    else:
        full_audio = np.concatenate(audio_chunks)

    # 16-bit signed PCM conversion
    pcm16 = np.clip(full_audio * 32767.0, -32768.0, 32767.0).astype(np.int16)

    wav_buf = io.BytesIO()
    scipy.io.wavfile.write(wav_buf, sonification.SAMPLE_RATE, pcm16)
    wav_bytes = wav_buf.getvalue()

    if embed_metadata:
        # Compact summary for RIFF comment chunk
        summary_entries = [
            f"{r['region_id']}={r['note']}({r['frequency_hz']:.1f}Hz)@{r['tone_start_seconds']}s"
            for r in synced_records
            if r["audio_included"]
        ]
        compact_comment = (
            f"NASA Earth Jukebox Sonification | Records={len(synced_records)} | "
            + "; ".join(summary_entries)
        )
        try:
            wav_bytes = embed_riff_comment(wav_bytes, compact_comment)
        except Exception:
            # Fall back to unadorned WAV without breaking pipeline
            pass

    return wav_bytes, synced_records


# ============================================================================
# EXPORT HELPERS (CSV & JSON)
# ============================================================================

CSV_FIELDNAMES = [
    "record_index",
    "region_id",
    "region_name",
    "grid_row",
    "grid_col",
    "windspeed_mps",
    "note",
    "frequency_hz",
    "category",
    "confidence",
    "tone_start_seconds",
    "tone_duration_seconds",
    "audio_included",
]


def export_records_csv(records: List[Dict[str, Any]], filepath: Union[str, Path, io.StringIO]) -> str:
    """Export synchronized records to CSV meeting exact per-record contract."""
    if hasattr(filepath, "write"):
        writer = csv.DictWriter(filepath, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for rec in records:
            row = {}
            for col in CSV_FIELDNAMES:
                val = rec.get(col)
                row[col] = "" if val is None else val
            writer.writerow(row)
        return ""

    target_path = Path(filepath)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for rec in records:
            row = {}
            for col in CSV_FIELDNAMES:
                val = rec.get(col)
                row[col] = "" if val is None else val
            writer.writerow(row)

    return str(target_path)


def export_records_json(
    records: List[Dict[str, Any]],
    filepath: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Export synchronized records to structured JSON."""
    target_path = Path(filepath)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    speeds = [r["windspeed_mps"] for r in records if isinstance(r.get("windspeed_mps"), (int, float))]
    stats = {
        "record_count": len(records),
        "audio_records_count": sum(1 for r in records if r.get("audio_included")),
        "min_windspeed_mps": min(speeds) if speeds else 0.0,
        "max_windspeed_mps": max(speeds) if speeds else 0.0,
        "avg_windspeed_mps": round(sum(speeds) / len(speeds), 2) if speeds else 0.0,
    }

    doc = {
        "metadata": {
            "title": "NASA Earth Information Jukebox - Sonified Windspeed Records",
            "module": "Member 4 Extended Adapter",
            "audio_format": "44.1 kHz 16-bit Mono PCM WAV",
            "tone_duration_sec": sonification.TONE_DURATION_SEC,
            "gap_duration_sec": sonification.GAP_DURATION_SEC,
            **(metadata or {}),
            "statistics": stats,
        },
        "records": records,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)

    return str(target_path)


# ============================================================================
# STANDALONE CLI DEMONSTRATION
# ============================================================================

def run_cli_demo(
    input_file: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> None:
    """Run standalone demonstration from command line."""
    base_dir = Path(__file__).resolve().parent
    if input_file is None:
        candidate_inputs = [
            base_dir / "examples" / "sample_member3_export.csv",
            base_dir / "examples" / "sample_regions.json",
        ]
        input_file = next((p for p in candidate_inputs if p.exists()), None)

    if output_dir is None:
        out_dir = base_dir / "outputs"
    else:
        out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("NASA EARTH JUKEBOX — MEMBER 4 EXTENDED SONIFICATION ADAPTER")
    print("=" * 75)

    if input_file and Path(input_file).exists():
        print(f"Reading input records from: {input_file}")
        records = parse_windspeed_records(input_file)
    else:
        print("Using built-in illustrative test records (demonstrating 0-38 m/s range)...")
        demo_data = [
            {"region_id": "CELL_01", "region_name": "Calm Tropical Zone", "speed": 2.5, "confidence": "High Confidence"},
            {"region_id": "CELL_02", "region_name": "Mid-Atlantic Breeze", "speed": 7.0, "confidence": "High Confidence"},
            {"region_id": "CELL_03", "region_name": "Trade Wind Corridor", "speed": 12.0, "confidence": "High Confidence"},
            {"region_id": "CELL_04", "region_name": "Developing Depression", "speed": 21.0, "confidence": "High Confidence"},
            {"region_id": "CELL_05", "region_name": "Cyclone Outer Bands", "speed": 26.5, "confidence": "High Confidence"},
            {"region_id": "CELL_06", "region_name": "Severe Hurricane Eye Wall", "speed": 32.0, "confidence": "High Confidence"},
            {"region_id": "CELL_07", "region_name": "Extreme Gust Core", "speed": 38.0, "confidence": "High Confidence"},
            {"region_id": "CELL_08", "region_name": "Continental Cloud / Land", "speed": 38.0, "confidence": "Low / Potential Non-Data (Land/Cloud)"},
        ]
        records = parse_windspeed_records(demo_data)

    print(f"Successfully validated {len(records)} records.")

    print("\nSynthesizing 44.1 kHz 16-bit PCM WAV audio with embedded RIFF metadata...")
    wav_bytes, synced_records = sonify_records(records, include_low_confidence=True, embed_metadata=True)

    wav_out = out_dir / "sonified_wind_audio.wav"
    csv_out = out_dir / "sonified_windspeed_records.csv"
    json_out = out_dir / "sonified_windspeed_records.json"

    with open(wav_out, "wb") as f:
        f.write(wav_bytes)

    export_records_csv(synced_records, csv_out)
    export_records_json(synced_records, json_out)

    print("\n" + "-" * 75)
    print(f"{'Region':<28} | {'Speed':<8} | {'Note':<5} | {'Freq (Hz)':<10} | {'Confidence'}")
    print("-" * 75)
    for r in synced_records:
        print(
            f"{r['region_name'][:28]:<28} | {r['windspeed_mps']:<6.1f}   | {r['note']:<5} | {r['frequency_hz']:<10.2f} | {r['confidence']}"
        )
    print("-" * 75)

    # Verify embedded RIFF metadata
    parsed_meta = extract_riff_comment(wav_bytes)
    meta_status = "VERIFIED (Embedded and recovered successfully)" if parsed_meta else "NOT FOUND"

    print("\nOUTPUT FILES GENERATED:")
    print(f"  -> Playable WAV: {wav_out} ({len(wav_bytes):,} bytes)")
    print(f"  -> Records CSV : {csv_out} ({len(synced_records)} rows)")
    print(f"  -> Records JSON: {json_out}")
    print(f"  -> WAV Metadata: {meta_status}")
    if parsed_meta:
        print(f"     Preview     : {parsed_meta[:100]}...")
    print("=" * 75)


if __name__ == "__main__":
    import sys
    arg_input = sys.argv[1] if len(sys.argv) > 1 else None
    run_cli_demo(input_file=arg_input)
