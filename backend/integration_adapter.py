"""NASA Earth Information Center — Earth Jukebox.

Unified Integration Adapter: Member 2 (Image/Grid) + Member 3 (Windspeed Mapping) + Member 4 (Sonification).

This module bridges the team's components with minimal changes:
- Ingests NASA-style windspeed imagery, pre-extracted grid JSON, or scientific CSVs.
- Reuses Member 2's image loading and 5x5 grid color extraction.
- Reuses Member 3's Euclidean color distance matching against NASA legends.
- Preserves confidence scoring (High, Moderate, Low/Non-Data).
- Reuses Member 4's audio DSP engine with the extended 0-40 m/s scale.
- Generates 44.1 kHz 16-bit PCM WAV audio with embedded RIFF comment metadata.
- Exports structured, ordered per-record CSV and JSON datasets.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# PATH CONFIGURATION FOR CLEAN CROSS-MEMBER IMPORTS
# ---------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Ensure member2 and rgbout directories are available on path
M2_DIR = CURRENT_DIR / "member2"
if M2_DIR.exists() and str(M2_DIR) not in sys.path:
    sys.path.insert(0, str(M2_DIR))

M2_SPACE_DIR = CURRENT_DIR / "member 2"
if M2_SPACE_DIR.exists() and str(M2_SPACE_DIR) not in sys.path:
    sys.path.insert(0, str(M2_SPACE_DIR))

RGBOUT_DIR = CURRENT_DIR / "rgbout"
if RGBOUT_DIR.exists() and str(RGBOUT_DIR) not in sys.path:
    sys.path.insert(0, str(RGBOUT_DIR))

# ---------------------------------------------------------------------------
# MODULE IMPORTS
# ---------------------------------------------------------------------------
import sonification
import member4_adapter
import windspeed_mapper as m3

try:
    import nasa2py as m2
    HAS_MEMBER2 = True
except ImportError:
    try:
        from member2 import nasa2py as m2
        HAS_MEMBER2 = True
    except ImportError:
        HAS_MEMBER2 = False


# ============================================================================
# SCIENTIFIC PIPELINE EXECUTION
# ============================================================================

def load_scientific_legend(legend_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Load scientific legend from CSV or fall back to default NASA legend."""
    if legend_path and Path(legend_path).is_file():
        return m3.load_legend_from_csv(str(legend_path))

    default_csv = CURRENT_DIR / "nasa_legend.csv"
    if default_csv.is_file():
        return m3.load_legend_from_csv(str(default_csv))

    return m3.DEFAULT_NASA_LEGEND


def process_image_to_records(
    image_input: Union[str, Path, bytes, io.BytesIO],
    legend: Optional[List[Dict[str, Any]]] = None,
    use_median: bool = False,
    output_dir: Optional[Union[str, Path]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Execute Member 2 image extraction and Member 3 windspeed mapping.

    Args:
        image_input: Path to image file, or raw bytes / BytesIO buffer.
        legend: NASA colormap legend.
        use_median: If True, uses median RGB instead of mean RGB.
        output_dir: Optional directory to save Member 2 visual artifacts.

    Returns:
        Tuple of (mapped_results, stats).
    """
    if not HAS_MEMBER2:
        raise RuntimeError("Member 2 module (nasa2py) is unavailable in this environment.")

    if legend is None:
        legend = load_scientific_legend()

    # Handle bytes or file path
    temp_file: Optional[Path] = None
    if isinstance(image_input, (bytes, io.BytesIO)):
        data_bytes = image_input.getvalue() if isinstance(image_input, io.BytesIO) else image_input
        temp_file = CURRENT_DIR / "outputs" / "_temp_upload_image.png"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_bytes(data_bytes)
        img_path_str = str(temp_file)
    else:
        img_path_str = str(image_input)

    try:
        # Member 2: Load RGB array and extract 5x5 grid cells
        rgb_array = m2.load_image_rgb(img_path_str)
        grid_cells = m2.extract_grid_colors(rgb_array, grid_rows=5, grid_cols=5)

        # Optional Member 2 visual artifact export
        if output_dir:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            m2.save_results(grid_cells, str(out_p / "wind_grid_data.json"))
            m2.create_grid_overlay(rgb_array, grid_cells, str(out_p / "wind_grid_overlay.png"))
            m2.create_color_palette(grid_cells, str(out_p / "wind_color_palette.png"))

        # Member 3: Map colors to scientific windspeeds
        mapped = m3.process_extracted_regions(grid_cells, legend=legend, use_median=use_median)
        stats = m3.calculate_windspeed_statistics(mapped)
        return mapped, stats

    finally:
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass


def run_full_pipeline(
    source_type: str = "demo_mapped",
    input_data: Optional[Any] = None,
    legend_path: Optional[Union[str, Path]] = None,
    include_low_confidence: bool = True,
    embed_metadata: bool = True,
    output_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Execute the end-to-end Earth Jukebox pipeline.

    Source types:
      - 'demo_mapped': Built-in 25-cell pre-mapped dataset (windspeed_grid_mapped.json / CSV).
      - 'demo_regions': Built-in 8-region extracted dataset (extracted_regions.csv).
      - 'image': User-uploaded or provided NASA-style image (PNG/JPG).
      - 'csv': Uploaded or provided CSV file (Member 3 output or Member 2 extracted).
      - 'json': Uploaded or provided JSON file (Member 3 mapped or Member 4 format).

    Returns:
        Comprehensive results dictionary including:
          'records': List of synchronized per-record dicts
          'wav_bytes': Playable 16-bit PCM WAV audio bytes
          'stats': Summary statistics
          'warnings': List of scientific warnings
          'legend': The 8-tier audio mapping legend
          'metadata_embedded': Whether RIFF comment was successfully embedded
    """
    legend = load_scientific_legend(legend_path)
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

    # 1. Acquire raw records based on source_type
    if source_type == "demo_mapped":
        # Load 25-cell pre-mapped fixture
        json_file = CURRENT_DIR / "windspeed_grid_mapped.json"
        csv_file = CURRENT_DIR / "windspeed_output_for_member4.csv"
        if json_file.exists():
            raw_records = member4_adapter.parse_windspeed_records(json_file)
        elif csv_file.exists():
            raw_records = member4_adapter.parse_windspeed_records(csv_file)
        else:
            raise FileNotFoundError("Demo mapped dataset files not found.")

    elif source_type == "demo_regions":
        # Load 8-region extracted CSV fixture and map with Member 3
        csv_file = CURRENT_DIR / "extracted_regions.csv"
        if not csv_file.exists():
            raise FileNotFoundError("extracted_regions.csv not found.")
        extracted = m3.load_extracted_regions_from_csv(str(csv_file))
        mapped = m3.process_extracted_regions(extracted, legend=legend)
        raw_records = member4_adapter.parse_windspeed_records(mapped)

    elif source_type == "image":
        if input_data is None:
            # Fall back to wind_grid_overlay.png in member2 if available for image demo
            cand_img = CURRENT_DIR / "member2" / "wind_grid_overlay.png"
            if cand_img.exists():
                input_data = cand_img
            else:
                raise ValueError("No image file supplied for image analysis.")

        mapped, img_stats = process_image_to_records(
            image_input=input_data,
            legend=legend,
            use_median=False,
            output_dir=output_dir,
        )
        raw_records = member4_adapter.parse_windspeed_records(mapped)
        stats.update(img_stats)

    elif source_type in ("csv", "json"):
        if input_data is None:
            raise ValueError(f"No file data supplied for {source_type} processing.")

        # Check if CSV is raw RGB (Member 2 extracted_regions style)
        is_raw_rgb_csv = False
        if source_type == "csv":
            sample_text = ""
            if isinstance(input_data, (str, Path)) and Path(input_data).is_file():
                sample_text = Path(input_data).read_text(encoding="utf-8")[:500]
            elif isinstance(input_data, bytes):
                sample_text = input_data[:500].decode("utf-8", errors="ignore")
            elif isinstance(input_data, str):
                sample_text = input_data[:500]

            if "windspeed" not in sample_text.lower() and "speed" not in sample_text.lower():
                if "r," in sample_text or "extracted_r" in sample_text:
                    is_raw_rgb_csv = True

        if is_raw_rgb_csv:
            # Ingest through Member 3 mapper
            if isinstance(input_data, (str, Path)) and Path(input_data).is_file():
                extracted = m3.load_extracted_regions_from_csv(str(input_data))
            else:
                # Parse in-memory CSV
                text_stream = io.StringIO(sample_text if isinstance(input_data, str) else input_data.decode("utf-8"))
                reader = csv.DictReader(text_stream)
                extracted = [row for row in reader]
            mapped = m3.process_extracted_regions(extracted, legend=legend)
            raw_records = member4_adapter.parse_windspeed_records(mapped)
        else:
            raw_records = member4_adapter.parse_windspeed_records(input_data)

    else:
        raise ValueError(f"Unknown source_type '{source_type}'.")

    # 2. Check for low-confidence / non-data records
    low_conf_count = sum(
        1
        for r in raw_records
        if "low" in str(r.get("confidence", "")).lower()
        or "non-data" in str(r.get("confidence", "")).lower()
    )
    if low_conf_count > 0:
        warnings.append(
            f"Scientific Warning: {low_conf_count} of {len(raw_records)} cells have low confidence "
            "(color distance > 75). These may represent continental land, cloud cover, or non-data pixels. "
            + ("Audio includes them with estimated pitch." if include_low_confidence else "Audio excluded them by default.")
        )

    # 3. Synthesize audio and establish exact record synchronization
    wav_bytes, synced_records = member4_adapter.sonify_records(
        raw_records,
        include_low_confidence=include_low_confidence,
        embed_metadata=embed_metadata,
    )

    # 4. Compute overall statistics
    speeds = [r["windspeed_mps"] for r in synced_records if isinstance(r.get("windspeed_mps"), (int, float))]
    audio_records_count = sum(1 for r in synced_records if r["audio_included"])
    total_audio_duration = 0.0
    if audio_records_count > 0:
        total_audio_duration = round(
            audio_records_count * sonification.TONE_DURATION_SEC
            + (audio_records_count - 1) * sonification.GAP_DURATION_SEC,
            3,
        )

    stats.update(
        {
            "total_records": len(synced_records),
            "audio_records": audio_records_count,
            "min_windspeed_mps": min(speeds) if speeds else 0.0,
            "max_windspeed_mps": max(speeds) if speeds else 0.0,
            "avg_windspeed_mps": round(sum(speeds) / len(speeds), 2) if speeds else 0.0,
            "low_confidence_count": low_conf_count,
            "audio_duration_seconds": total_audio_duration,
        }
    )

    # 5. Verify embedded metadata
    embedded_comment = member4_adapter.extract_riff_comment(wav_bytes)
    meta_embedded = embedded_comment is not None

    # 6. Optional file export
    exported_paths = {}
    if output_dir:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)
        wav_path = out_p / "sonified_wind_audio.wav"
        csv_path = out_p / "sonified_windspeed_records.csv"
        json_path = out_p / "sonified_windspeed_records.json"

        wav_path.write_bytes(wav_bytes)
        member4_adapter.export_records_csv(synced_records, csv_path)
        member4_adapter.export_records_json(synced_records, json_path, metadata=stats)

        exported_paths = {
            "wav": str(wav_path),
            "csv": str(csv_path),
            "json": str(json_path),
        }

    return {
        "records": synced_records,
        "wav_bytes": wav_bytes,
        "stats": stats,
        "warnings": warnings,
        "legend": member4_adapter.get_extended_audio_legend(),
        "metadata_embedded": meta_embedded,
        "embedded_comment": embedded_comment,
        "exported_files": exported_paths,
    }
