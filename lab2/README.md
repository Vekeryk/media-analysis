## Usage

```bash
python transcribe_audio.py <audio_file> [output_file]
```

### Example

```bash
python transcribe_audio.py lab_2.mp3
```

### Workflow Steps

#### 1. Initialize AWS Clients

```python
self.s3 = boto3.client('s3', region_name=AWS_REGION, ...)
self.transcribe = boto3.client('transcribe', region_name=AWS_REGION, ...)
```

#### 2. Create S3 Bucket

```python
bucket_name = 'media-labs-audio-transcribe'
```

Checks if bucket exists, creates if needed.

#### 3. Upload to S3

```python
s3_uri = f"s3://{bucket_name}/audio/lab_2.mp3"
self.s3.upload_file(file_path, bucket_name, s3_key)
```

#### 4. Start Transcription with Auto Language Detection

```python
self.transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={'MediaFileUri': s3_uri},
    MediaFormat='mp3',
    IdentifyLanguage=True,  # Auto-detect!
    LanguageOptions=['en-US', 'uk-UA', 'pl-PL', 'de-DE', 'fr-FR']
)
```

AWS Transcribe automatically detects the language with confidence scores.

#### 5. Wait for Completion

Polls every 5 seconds until status is `COMPLETED`.

#### 6. Download and Save Results

Downloads JSON result and saves:

- `transcription.txt` - Clean transcript
- `transcription_full.json` - Full API response with confidence scores

## Results

### Test Run

**Input**: lab_2.mp3
**Detected Language**: Ukrainian (uk-UA)
**Transcript**: "Привіт, як справи?"
**Processing Time**: 10 seconds

## Generated Files

```
transcription.txt           # Clean transcript
transcription_full.json     # Full JSON with:
                           # - Word-level timing
                           # - Confidence scores
                           # - Language detection scores
```
