"""
AWS Lambda Function for Audio Transcription API
Handles binary file upload and S3 URI references
"""

import json
import boto3
import base64
import uuid
import os
from urllib.request import urlopen

# Initialize AWS clients
s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

# Configuration
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'media-labs-audio-transcribe')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_LANGUAGES = ['en-US', 'uk-UA', 'pl-PL', 'de-DE', 'fr-FR']


def lambda_handler(event, context):
    """
    Main Lambda handler
    Routes to POST (start job) or GET (check status)
    """
    print(f"Event: {json.dumps(event)}")

    method = event.get('httpMethod', 'POST')

    if method == 'GET':
        return handle_status_check(event)
    elif method == 'POST':
        return handle_start_transcription(event)
    else:
        return response(405, {'error': 'Method not allowed'})


def handle_start_transcription(event):
    """
    Start transcription job and return immediately
    Accepts: binary upload or S3 URI
    """
    try:
        headers = event.get('headers', {})
        content_type = headers.get(
            'content-type', headers.get('Content-Type', ''))

        s3_uri = None

        # Option 1: Binary file upload
        if 'audio/' in content_type.lower():
            # Decode binary data
            body = event.get('body', '')
            if event.get('isBase64Encoded', False):
                audio_data = base64.b64decode(body)
            else:
                audio_data = body.encode(
                    'utf-8') if isinstance(body, str) else body

            # Validate file size
            if len(audio_data) > MAX_FILE_SIZE:
                return response(413, {
                    'error': 'File too large',
                    'message': f'Maximum file size is {MAX_FILE_SIZE / 1024 / 1024}MB. Use S3 URI for larger files.'
                })

            # Determine file extension from content-type
            ext = get_extension_from_content_type(content_type)
            filename = f'upload-{uuid.uuid4()}.{ext}'
            s3_key = f'api-uploads/{filename}'

            # Upload to S3
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=audio_data,
                ContentType=content_type
            )

            s3_uri = f's3://{BUCKET_NAME}/{s3_key}'
            print(f"Uploaded to: {s3_uri}")

        # Option 2: S3 URI provided
        elif 'application/json' in content_type.lower():
            body = json.loads(event.get('body', '{}'))
            s3_uri = body.get('s3_uri')

            if not s3_uri:
                return response(400, {
                    'error': 'Missing s3_uri',
                    'message': 'Provide s3_uri in JSON body'
                })

            # Validate S3 URI format
            if not s3_uri.startswith('s3://'):
                return response(400, {
                    'error': 'Invalid S3 URI',
                    'message': 'S3 URI must start with s3://'
                })

            print(f"Using S3 URI: {s3_uri}")

        else:
            return response(400, {
                'error': 'Invalid Content-Type',
                'message': 'Use Content-Type: audio/* for file upload or application/json for S3 URI'
            })

        # Determine media format from URI
        media_format = get_media_format(s3_uri)

        # Start transcription job (async - just start, don't wait)
        job_name = f'transcribe-{uuid.uuid4()}'

        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': s3_uri},
            MediaFormat=media_format,
            IdentifyLanguage=True,
            LanguageOptions=SUPPORTED_LANGUAGES
        )

        print(f"Started transcription job: {job_name}")

        # Return immediately (don't wait for completion)
        return response(202, {
            'status': 'processing',
            'job_name': job_name,
            's3_uri': s3_uri,
            'message': f'Transcription started. Check status at: GET /transcribe/{job_name}'
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })


def handle_status_check(event):
    """
    Check transcription job status
    GET /transcribe/{job_name}
    """
    try:
        # Extract job_name from path
        path_params = event.get('pathParameters', {})
        job_name = path_params.get('job_name')

        if not job_name:
            return response(400, {
                'error': 'Missing job_name',
                'message': 'Provide job_name in path'
            })

        # Get job status
        job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        job_data = job['TranscriptionJob']
        status = job_data['TranscriptionJobStatus']

        if status == 'COMPLETED':
            # Get transcript
            transcript_uri = job_data['Transcript']['TranscriptFileUri']

            with urlopen(transcript_uri) as response_data:
                result = json.loads(response_data.read())

            transcript = result['results']['transcripts'][0]['transcript']
            language = result['results'].get('language_code', 'unknown')

            return response(200, {
                'status': 'completed',
                'job_name': job_name,
                'transcript': transcript,
                'language': language
            })

        elif status == 'FAILED':
            failure_reason = job_data.get('FailureReason', 'Unknown error')
            return response(500, {
                'status': 'failed',
                'job_name': job_name,
                'error': failure_reason
            })

        else:  # IN_PROGRESS or QUEUED
            return response(202, {
                'status': 'processing',
                'job_name': job_name,
                'message': 'Transcription still in progress'
            })

    except transcribe.exceptions.BadRequestException:
        return response(404, {
            'error': 'Job not found',
            'message': f'No transcription job found with name: {job_name}'
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })


def get_extension_from_content_type(content_type):
    """Extract file extension from Content-Type header"""
    type_map = {
        'audio/wav': 'wav',
        'audio/wave': 'wav',
        'audio/x-wav': 'wav',
        'audio/mpeg': 'mp3',
        'audio/mp3': 'mp3',
        'audio/mp4': 'mp4',
        'audio/flac': 'flac',
        'audio/ogg': 'ogg',
        'audio/webm': 'webm'
    }
    return type_map.get(content_type.lower(), 'wav')


def get_media_format(s3_uri):
    """Determine media format from S3 URI"""
    ext = s3_uri.lower().split('.')[-1]
    format_map = {
        'mp3': 'mp3',
        'wav': 'wav',
        'mp4': 'mp4',
        'flac': 'flac',
        'ogg': 'ogg',
        'webm': 'webm'
    }
    return format_map.get(ext, 'wav')


def response(status_code, body):
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
        },
        'body': json.dumps(body)
    }
