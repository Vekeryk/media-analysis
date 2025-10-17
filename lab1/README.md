### Run the Media Analyzer

```bash
source venv/bin/activate
python lab1/media_analyzer.py <filename>
```

### Examples with Lab2 and Lab3 Files

```bash
# Analyze MP3 file from Lab 2
python lab1/media_analyzer.py lab2/lab_2.mp3

# Analyze WAV file from Lab 3
python lab1/media_analyzer.py lab3/lab3.wav
```

## Test Files

The analyzer has been tested with:

- **lab2/lab_2.mp3** - MP3 file with ID3 metadata (artist: "test", title: "lab2", album: "lasb2")
- **lab3/lab3.wav** - WAV file (5.35 seconds, 24 kHz, mono)

## Results

See `results.txt` for detailed analysis output from the lab2 and lab3 audio files.
