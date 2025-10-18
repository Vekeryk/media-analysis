#!/usr/bin/env python3
"""
Lab 2: AWS Transcribe Audio Transcription
Uploads audio file to S3 and transcribes it using AWS Transcribe with automatic language detection
"""

import os
import sys
import time
import json
import urllib.request
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# AWS Configuration from environment
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'eu-west-1')
BUCKET_NAME = 'media-labs-audio-transcribe'


class AudioTranscriber:
    """Handles audio transcription using AWS S3 and Transcribe services"""

    def __init__(self):
        """Initialize AWS clients with credentials"""
        self.region = AWS_REGION
        self.bucket_name = BUCKET_NAME

        # Initialize S3 client
        self.s3 = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )

        # Initialize Transcribe client
        self.transcribe = boto3.client(
            'transcribe',
            region_name=self.region,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )

        print(f"✓ Initialized AWS clients in region: {self.region}")

    def create_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            print(f"✓ Using existing S3 bucket: {self.bucket_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    if self.region == 'us-east-1':
                        self.s3.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': self.region}
                        )
                    print(f"✓ Created S3 bucket: {self.bucket_name}")
                except ClientError as create_error:
                    print(f"✗ Error creating bucket: {create_error}")
                    raise
            else:
                print(f"✗ Error checking bucket: {e}")
                raise

    def upload_file(self, file_path):
        """Upload audio file to S3"""
        file_name = Path(file_path).name
        s3_key = f"audio/{file_name}"
        s3_uri = f"s3://{self.bucket_name}/{s3_key}"

        try:
            print(f"→ Uploading {file_name} to S3...")
            self.s3.upload_file(file_path, self.bucket_name, s3_key)
            print(f"✓ Uploaded to: {s3_uri}")
            return s3_uri
        except ClientError as e:
            print(f"✗ Error uploading file: {e}")
            raise

    def start_transcription(self, s3_uri, job_name):
        """Start AWS Transcribe job with automatic language detection"""
        try:
            # Delete existing job if it exists
            try:
                self.transcribe.get_transcription_job(
                    TranscriptionJobName=job_name)
                print(f"→ Deleting existing job: {job_name}")
                self.transcribe.delete_transcription_job(
                    TranscriptionJobName=job_name)
                time.sleep(2)
            except ClientError:
                pass

            print(f"→ Starting transcription with auto language detection...")

            # Start transcription with automatic language identification
            self.transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': s3_uri},
                MediaFormat='mp3',
                IdentifyLanguage=True,  # Auto-detect language
                LanguageOptions=['en-US', 'uk-UA', 'pl-PL', 'de-DE', 'fr-FR']
            )

            print(f"✓ Transcription job started: {job_name}")
            return job_name

        except ClientError as e:
            print(f"✗ Error starting transcription: {e}")
            raise

    def wait_for_completion(self, job_name, max_wait=300):
        """Wait for transcription job to complete"""
        print(f"→ Waiting for completion (max {max_wait}s)...")

        start_time = time.time()
        while True:
            try:
                response = self.transcribe.get_transcription_job(
                    TranscriptionJobName=job_name)
                job = response['TranscriptionJob']
                status = job['TranscriptionJobStatus']

                if status == 'COMPLETED':
                    elapsed = int(time.time() - start_time)
                    detected_language = job.get('LanguageCode', 'Unknown')
                    print(
                        f"\n✓ Completed in {elapsed}s | Detected language: {detected_language}")
                    return job

                elif status == 'FAILED':
                    reason = job.get('FailureReason', 'Unknown')
                    print(f"\n✗ Transcription failed: {reason}")
                    raise Exception(f"Transcription failed: {reason}")

                elif status in ['IN_PROGRESS', 'QUEUED']:
                    elapsed = int(time.time() - start_time)
                    if elapsed > max_wait:
                        print(f"\n✗ Timeout after {elapsed}s")
                        raise Exception("Transcription timeout")

                    print(f"  Status: {status} ({elapsed}s)...", end='\r')
                    time.sleep(5)

            except ClientError as e:
                print(f"\n✗ Error checking status: {e}")
                raise

    def download_result(self, transcript_uri):
        """Download transcription result"""
        try:
            print(f"→ Downloading result...")
            with urllib.request.urlopen(transcript_uri) as response:
                result = json.loads(response.read().decode('utf-8'))
            print(f"✓ Result downloaded")
            return result
        except Exception as e:
            print(f"✗ Error downloading result: {e}")
            raise

    def save_result(self, result, output_file):
        """Save transcription to files"""
        try:
            transcript_text = result['results']['transcripts'][0]['transcript']
            language_code = result['results'].get('language_code', 'Unknown')

            # Save full JSON
            json_file = output_file.replace('.txt', '_full.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved JSON: {json_file}")

            # Save clean transcript
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("AWS TRANSCRIBE RESULT\n")
                f.write("=" * 60 + "\n\n")
                f.write("Transcript:\n")
                f.write("-" * 60 + "\n")
                f.write(transcript_text + "\n")
                f.write("-" * 60 + "\n\n")
                f.write("Metadata:\n")
                f.write(f"Job Name: {result.get('jobName', 'N/A')}\n")
                f.write(f"Status: {result.get('status', 'N/A')}\n")
                f.write(f"Detected Language: {language_code}\n")

            print(f"✓ Saved transcript: {output_file}")
            return transcript_text, language_code

        except Exception as e:
            print(f"✗ Error saving result: {e}")
            raise

    def transcribe_file(self, audio_file, output_file='transcription.txt'):
        """Main workflow: upload, transcribe, save"""
        print("\n" + "=" * 60)
        print("AWS TRANSCRIBE - Audio Transcription")
        print("=" * 60 + "\n")

        try:
            # Create bucket
            self.create_bucket()

            # Upload file
            s3_uri = self.upload_file(audio_file)

            # Start transcription
            job_name = f"transcribe-{Path(audio_file).stem}-{int(time.time())}"
            self.start_transcription(s3_uri, job_name)

            # Wait for completion
            job_result = self.wait_for_completion(job_name)

            # Download result
            transcript_uri = job_result['Transcript']['TranscriptFileUri']
            result = self.download_result(transcript_uri)

            # Save result
            transcript, language = self.save_result(result, output_file)

            # Show result
            print("\n" + "=" * 60)
            print("TRANSCRIPTION COMPLETE")
            print("=" * 60)
            print(f"\nDetected Language: {language}")
            print(f"Transcript:")
            print("-" * 60)
            print(transcript[:500] + ("..." if len(transcript) > 500 else ""))
            print("-" * 60)

            return True

        except Exception as e:
            print(f"\n✗ Failed: {e}")
            return False


def main():
    """Entry point"""
    if len(sys.argv) < 2:
        print("Usage: python transcribe_audio.py <audio_file> [output_file]")
        print("Example: python transcribe_audio.py lab_2.mp3")
        sys.exit(1)

    audio_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'transcription.txt'

    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}")
        sys.exit(1)

    transcriber = AudioTranscriber()
    success = transcriber.transcribe_file(audio_file, output_file)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
