#!/usr/bin/env python3
"""
Lab 5: JPEG Image Analysis
- Validates JPEG file
- Extracts EXIF metadata
- Detects faces using Haar Cascade
- Outputs annotated image and metadata JSON
"""

import sys
import json
import os
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import cv2


def validate_jpeg(file_path):
    """
    Validate if file is a valid JPEG
    Checks magic bytes and Pillow can open it
    """
    print(f"Validating JPEG file: {file_path}")

    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check JPEG magic bytes (FF D8 FF)
    with open(file_path, 'rb') as f:
        header = f.read(3)
        if header[:2] != b'\xff\xd8':
            raise ValueError(
                "Not a valid JPEG file (missing FF D8 magic bytes)")
        if header[2] != 0xff:
            raise ValueError("Not a valid JPEG file (missing third FF byte)")

    # Try to open with Pillow
    try:
        img = Image.open(file_path)
        img.verify()
        print(
            f"✓ Valid JPEG: {img.format} {img.size[0]}x{img.size[1]} {img.mode}")
        return True
    except Exception as e:
        raise ValueError(f"Cannot open image with Pillow: {e}")


def extract_exif(file_path):
    """
    Extract EXIF metadata from JPEG
    Returns dict with human-readable tags
    """
    print("\nExtracting EXIF metadata...")

    img = Image.open(file_path)
    exif_data = {}

    # Get EXIF data
    try:
        exif_raw = img._getexif()

        if exif_raw is None:
            print("⚠ No EXIF data found in image")
            return exif_data

        # Convert numeric tags to names
        for tag_id, value in exif_raw.items():
            tag_name = TAGS.get(tag_id, tag_id)

            # Handle GPS data specially
            if tag_name == "GPSInfo":
                gps_data = {}
                for gps_tag_id, gps_value in value.items():
                    gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_data[gps_tag_name] = str(gps_value)
                exif_data[tag_name] = gps_data
            else:
                # Convert to string to handle bytes and other types
                try:
                    if isinstance(value, bytes):
                        exif_data[tag_name] = value.decode(
                            'utf-8', errors='ignore')
                    else:
                        exif_data[tag_name] = str(value)
                except:
                    exif_data[tag_name] = str(value)

        print(f"✓ Extracted {len(exif_data)} EXIF tags")

        # Print key metadata
        important_tags = ['Make', 'Model', 'DateTime',
                          'ExposureTime', 'FNumber', 'ISOSpeedRatings']
        for tag in important_tags:
            if tag in exif_data:
                print(f"  {tag}: {exif_data[tag]}")

    except AttributeError:
        print("⚠ No EXIF data found in image")
    except Exception as e:
        print(f"⚠ Error extracting EXIF: {e}")

    return exif_data


def detect_faces(file_path):
    """
    Detect faces using Haar Cascade
    Returns image with red rectangles around faces and face count
    """
    print("\nDetecting faces...")

    # Load image with OpenCV
    img = cv2.imread(file_path)
    if img is None:
        raise ValueError(f"Cannot load image with OpenCV: {file_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Load Haar Cascade classifier
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        raise ValueError("Failed to load Haar Cascade classifier")

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=6,
        minSize=(40, 40),
    )

    print(f"✓ Detected {len(faces)} face(s)")

    # Draw red rectangles around faces
    for i, (x, y, w, h) in enumerate(faces):
        # Red color in BGR format
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)
        print(f"  Face {i+1}: position=({x}, {y}), size={w}x{h}")

    return img, len(faces), faces


def save_metadata(exif_data, faces, output_path):
    """
    Save metadata to JSON file
    """
    metadata = {
        "exif": exif_data,
        "faces_detected": len(faces),
        "faces": [
            {
                "id": i + 1,
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h)
            }
            for i, (x, y, w, h) in enumerate(faces)
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Metadata saved to: {output_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python lab5.py <image.jpeg>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Prepare output filenames
    base_name = Path(input_file).stem
    output_image = f"{base_name}_faces.jpg"
    output_json = f"{base_name}_metadata.json"

    print("=" * 70)
    print("Lab 5: JPEG Image Analysis")
    print("=" * 70)
    print(f"Input: {input_file}")
    print(f"Output image: {output_image}")
    print(f"Output metadata: {output_json}")
    print("=" * 70)

    try:
        # Step 1: Validate JPEG
        validate_jpeg(input_file)

        # Step 2: Extract EXIF metadata
        exif_data = extract_exif(input_file)

        # Step 3: Detect faces
        img_with_faces, face_count, faces = detect_faces(input_file)

        # Step 4: Save annotated image
        cv2.imwrite(output_image, img_with_faces)
        print(f"\n✓ Annotated image saved to: {output_image}")

        # Step 5: Save metadata JSON
        save_metadata(exif_data, faces, output_json)

        print("\n" + "=" * 70)
        print("✓ Analysis Complete!")
        print("=" * 70)
        print(f"Faces detected: {face_count}")
        print(f"EXIF tags: {len(exif_data)}")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
