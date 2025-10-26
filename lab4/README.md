# Lab 4: Audio Transcription API

Serverless API for transcribing audio files using AWS Lambda, API Gateway, and Transcribe.

**API Endpoint:** https://h1saekc0nk.execute-api.eu-west-1.amazonaws.com/prod/transcribe

**Architecture:** API Gateway → Lambda → S3 + Transcribe

## Deployment

```bash
./deploy.sh
```

This script:
- Installs SAM CLI (if needed)
- Builds Lambda package
- Deploys infrastructure via CloudFormation
- Outputs API endpoint

## API Usage

### Method 1: Upload Audio File Directly

**Postman:**
1. Method: **POST**
2. URL: `https://h1saekc0nk.execute-api.eu-west-1.amazonaws.com/prod/transcribe`
3. Body → **binary** → Select audio file
4. Headers: `Content-Type: audio/wav`
5. Click **Send**

**curl:**
```bash
curl -X POST https://h1saekc0nk.execute-api.eu-west-1.amazonaws.com/prod/transcribe \
  -H "Content-Type: audio/wav" \
  --data-binary "@audio.wav"
```

**Response (202 Accepted):**
```json
{
  "status": "processing",
  "job_name": "transcribe-a1b2c3d4-...",
  "s3_uri": "s3://media-labs-audio-transcribe/api-uploads/...",
  "message": "Transcription started. Check status at: GET /transcribe/transcribe-a1b2c3d4-..."
}
```

### Method 2: Use S3 URI

If file already uploaded to S3:

```bash
curl -X POST https://h1saekc0nk.execute-api.eu-west-1.amazonaws.com/prod/transcribe \
  -H "Content-Type: application/json" \
  -d '{"s3_uri": "s3://media-labs-audio-transcribe/audio/lab3.wav"}'
```

### Check Transcription Status

Use job_name from previous response:

**curl:**
```bash
curl https://h1saekc0nk.execute-api.eu-west-1.amazonaws.com/prod/transcribe/transcribe-a1b2c3d4-...
```

**Response (still processing - 202):**
```json
{
  "status": "processing",
  "job_name": "transcribe-a1b2c3d4-...",
  "message": "Transcription still in progress"
}
```

**Response (completed - 200):**
```json
{
  "status": "completed",
  "job_name": "transcribe-a1b2c3d4-...",
  "transcript": "NASA has launched a new rocket. It was fantastic.",
  "language": "en-US"
}
```

## Testing

```bash
python test_api.py
```

Tests:
1. Binary file upload
2. S3 URI reference
3. Error handling

## Configuration

- **Max file size:** 10MB (direct upload)
- **Supported formats:** WAV, MP3, MP4, FLAC, OGG, WebM
- **Languages:** en-US, uk-UA, pl-PL, de-DE, fr-FR (auto-detected)
- **Timeout:** Lambda 60s, API Gateway 30s

## Files

```
lab4/
├── lambda_function.py    # Lambda handler
├── template.yaml         # SAM/CloudFormation template
├── deploy.sh             # Deployment automation
├── test_api.py           # Test suite
└── README.md             # This file
```

## AWS Resources

Created by deployment:
- Lambda function: `media-labs-transcribe-api`
- API Gateway: `media-labs-transcribe-api`
- S3 bucket: `media-labs-audio-transcribe`
- IAM role: Auto-created by SAM
- CloudWatch log group: `/aws/lambda/media-labs-transcribe-api`

## Cleanup

```bash
aws cloudformation delete-stack --stack-name media-labs-transcribe-stack
```
