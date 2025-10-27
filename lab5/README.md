# Lab 5: JPEG Image Analysis

Python script for JPEG file validation, EXIF metadata extraction, and face detection.

## Usage

Example:

```bash
python lab5.py new_york.jpeg
```

## Output

1. **`<filename>_faces.jpg`** - Image with red rectangles around detected faces
2. **`<filename>_metadata.json`** - JSON file with EXIF data and face coordinates
3. Console output with analysis summary

## How It Works

### 1. JPEG Validation

- Checks magic bytes (`FF D8 FF`)
- Verifies Pillow can open and read the file
- Reports image format, size, and color mode

### 2. EXIF Extraction

Extracts metadata tags:

- Camera make and model
- Date and time taken
- Exposure settings (ISO, shutter speed, aperture)
- GPS coordinates (if available)
- Image description

## Files

```
lab5/
├── lab5.py                    # Main script
├── new_york.jpeg              # Input image
├── new_york_faces.jpg         # Output with face rectangles
└── new_york_metadata.json     # EXIF + face data
```
