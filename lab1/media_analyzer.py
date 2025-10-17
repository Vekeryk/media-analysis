#!/usr/bin/env python3
"""
Media File Analyzer
Analyzes MP3 and WAV files to extract duration and metadata
using pydub and mutagen libraries.
"""

import os
import sys
from pathlib import Path
from pydub import AudioSegment
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.wave import WAVE


def is_media_file(filename):
    """Check if the file is a supported media file (mp3 or wav)"""
    if not os.path.exists(filename):
        return False, "File does not exist"

    ext = Path(filename).suffix.lower()
    if ext not in ['.mp3', '.wav']:
        return False, f"Unsupported format: {ext}. Only .mp3 and .wav are supported"

    return True, ext


def get_duration(filename, file_ext):
    """Get duration of media file in seconds using pydub"""
    try:
        if file_ext == '.mp3':
            audio = AudioSegment.from_mp3(filename)
        elif file_ext == '.wav':
            audio = AudioSegment.from_wav(filename)
        else:
            return None

        duration_seconds = len(audio) / 1000.0
        return duration_seconds
    except Exception as e:
        print(f"Error reading duration: {e}")
        return None


def get_metadata(filename):
    """Get metadata from media file using mutagen"""
    try:
        audio = MutagenFile(filename)

        if audio is None:
            return {}

        metadata = {}

        # Extract common metadata
        if hasattr(audio, 'tags') and audio.tags:
            for key, value in audio.tags.items():
                # Convert value to string, handling lists
                if isinstance(value, list):
                    metadata[key] = ', '.join(str(v) for v in value)
                else:
                    metadata[key] = str(value)

        # Add file info
        if hasattr(audio, 'info'):
            info = audio.info
            if hasattr(info, 'bitrate') and info.bitrate:
                metadata['bitrate'] = f"{info.bitrate} bps"
            if hasattr(info, 'sample_rate') and info.sample_rate:
                metadata['sample_rate'] = f"{info.sample_rate} Hz"
            if hasattr(info, 'channels') and info.channels:
                metadata['channels'] = str(info.channels)

        return metadata
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return {}


def analyze_media_file(filename):
    """Main function to analyze media file"""
    print(f"\n{'='*60}")
    print(f"Analyzing file: {filename}")
    print(f"{'='*60}\n")

    # Check if file is a supported media file
    is_valid, result = is_media_file(filename)

    if not is_valid:
        print(f"Error: {result}")
        return False

    file_ext = result
    print(f"File format: {file_ext.upper()}")

    # Get duration
    print("\n--- Duration ---")
    duration = get_duration(filename, file_ext)
    if duration is not None:
        print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    else:
        print("Could not determine duration")

    # Get metadata
    print("\n--- Metadata ---")
    metadata = get_metadata(filename)

    if metadata:
        for key, value in metadata.items():
            print(f"{key}: {value}")
    else:
        print("No metadata available")

    print(f"\n{'='*60}\n")
    return True


def main():
    """Entry point of the script"""
    if len(sys.argv) < 2:
        print("Usage: python media_analyzer.py <filename>")
        print("Example: python media_analyzer.py sample.mp3")
        sys.exit(1)

    filename = sys.argv[1]
    analyze_media_file(filename)


if __name__ == "__main__":
    main()
