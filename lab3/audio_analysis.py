#!/usr/bin/env python3
"""
Lab 3: Audio Analysis with AWS Transcribe + NLP
Transcribes audio, detects language, analyzes sentiment, searches phrases, and extracts named entities.
"""

import os
import sys
import time
import json
import argparse
import requests
from dotenv import load_dotenv
import boto3
from langdetect import detect_langs
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'eu-west-1')
BUCKET_NAME = 'media-labs-audio-transcribe'


class AudioAnalyzer:
    """Analyzes audio files using AWS Transcribe and NLP tools"""

    def __init__(self):
        """Initialize AWS clients and NLP models"""
        # AWS clients
        self.s3 = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )
        self.transcribe = boto3.client(
            'transcribe',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )

        # Download NLTK data if needed
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            print("Downloading NLTK vader_lexicon...")
            nltk.download('vader_lexicon', quiet=True)

        # Initialize sentiment analyzer
        self.sia = SentimentIntensityAnalyzer()

        # Load spaCy model
        print("Loading spaCy model...")
        self.nlp = spacy.load('en_core_web_sm')

        # Ensure bucket exists
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3.head_bucket(Bucket=BUCKET_NAME)
            print(f"Using existing bucket: {BUCKET_NAME}")
        except:
            print(f"Creating bucket: {BUCKET_NAME}")
            if AWS_REGION == 'us-east-1':
                self.s3.create_bucket(Bucket=BUCKET_NAME)
            else:
                self.s3.create_bucket(
                    Bucket=BUCKET_NAME,
                    CreateBucketConfiguration={
                        'LocationConstraint': AWS_REGION}
                )

    def transcribe_audio(self, file_path):
        """Transcribe audio file using AWS Transcribe"""
        print(f"\n1) TRANSCRIPTION")
        print("=" * 60)

        # Upload to S3
        filename = os.path.basename(file_path)
        s3_key = f'audio/{filename}'
        s3_uri = f's3://{BUCKET_NAME}/{s3_key}'

        print(f"Uploading {filename} to S3...")
        self.s3.upload_file(file_path, BUCKET_NAME, s3_key)
        print(f"Uploaded to: {s3_uri}")

        # Start transcription job
        job_name = f'transcribe-{filename.split(".")[0]}-{int(time.time())}'
        print(f"Starting transcription job: {job_name}")

        self.transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': s3_uri},
            MediaFormat='wav',
            IdentifyLanguage=True,
            LanguageOptions=['en-US', 'uk-UA', 'pl-PL', 'de-DE', 'fr-FR']
        )

        # Wait for completion
        print("Waiting for transcription to complete", end='')
        while True:
            status = self.transcribe.get_transcription_job(
                TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']

            if job_status == 'COMPLETED':
                print(" Done!")
                break
            elif job_status == 'FAILED':
                print(" Failed!")
                raise Exception("Transcription job failed")

            print('.', end='', flush=True)
            time.sleep(5)

        # Get results
        result_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        response = requests.get(result_uri)
        result = response.json()

        transcript = result['results']['transcripts'][0]['transcript']
        detected_lang = result['results'].get('language_code', 'unknown')

        print(f"\nTranscription: {transcript}")
        print(f"AWS Detected Language: {detected_lang}")

        return transcript, result

    def detect_language(self, text):
        """Detect language using langdetect"""
        print(f"\n2) LANGUAGE DETECTION")
        print("=" * 60)

        # Get language with confidence
        langs = detect_langs(text)
        primary_lang = langs[0]

        print(f"Language: {primary_lang.lang}")
        print(f"Confidence: {primary_lang.prob:.2%}")

        # Show all detected languages
        if len(langs) > 1:
            print("\nAll detected languages:")
            for lang in langs:
                print(f"  {lang.lang}: {lang.prob:.2%}")

        return primary_lang.lang, primary_lang.prob

    def analyze_sentiment(self, text):
        """Analyze sentiment using NLTK VADER"""
        print(f"\n3) SENTIMENT ANALYSIS")
        print("=" * 60)

        scores = self.sia.polarity_scores(text)

        # Determine sentiment
        if scores['compound'] >= 0.05:
            sentiment = 'Positive'
        elif scores['compound'] <= -0.05:
            sentiment = 'Negative'
        else:
            sentiment = 'Neutral'

        print(f"Sentiment: {sentiment}")
        print(
            f"Scores: pos={scores['pos']:.3f}, neu={scores['neu']:.3f}, neg={scores['neg']:.3f}, compound={scores['compound']:.3f}")

        return sentiment, scores

    def search_phrase_and_ner(self, text, phrase):
        """Search for phrase and extract named entities"""
        print(f"\n4) PHRASE SEARCH & NAMED ENTITY RECOGNITION")
        print("=" * 60)

        # Search for phrase
        phrase_lower = phrase.lower()
        text_lower = text.lower()

        if phrase_lower in text_lower:
            position = text_lower.index(phrase_lower)
            print(f"Phrase Found at position: {position}")
            print(
                f"Context: ...{text[max(0, position-20):position+len(phrase)+20]}...")
        else:
            print(f"Phrase Not found: '{phrase}'")

        # Named Entity Recognition
        doc = self.nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        print(f"\nNamed entities:")
        if entities:
            for entity, label in entities:
                print(f"  - {entity} ({label})")
        else:
            print("  No named entities found")

        return entities

    def analyze(self, audio_file, phrase=None):
        """Full analysis pipeline"""
        print("\n" + "=" * 60)
        print("AUDIO ANALYSIS PIPELINE")
        print("=" * 60)
        print(f"Audio file: {audio_file}")
        if phrase:
            print(f"Search phrase: {phrase}")

        # 1. Transcription
        transcript, transcribe_result = self.transcribe_audio(audio_file)

        # 2. Language detection
        language, confidence = self.detect_language(transcript)

        # 3. Sentiment analysis
        sentiment, scores = self.analyze_sentiment(transcript)

        # 4. Phrase search and NER
        entities = self.search_phrase_and_ner(
            transcript, phrase) if phrase else []

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Transcription: {transcript}")
        print(f"Language: {language}")
        print(f"Sentiment: {sentiment}")
        if phrase:
            if phrase.lower() in transcript.lower():
                position = transcript.lower().index(phrase.lower())
                print(f"Phrase Found at position: {position}")
            else:
                print(f"Phrase Not found")
        print(
            f"Named entities: {', '.join([ent[0] for ent in entities]) if entities else 'None'}")

        return {
            'transcript': transcript,
            'language': language,
            'language_confidence': confidence,
            'sentiment': sentiment,
            'sentiment_scores': scores,
            'entities': entities,
            'transcribe_result': transcribe_result
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze audio file with transcription, language detection, sentiment analysis, and NER')
    parser.add_argument('--audio-source', required=True,
                        help='Path to WAV audio file')
    parser.add_argument(
        '--phrase', help='Phrase to search for in transcription')

    args = parser.parse_args()

    # Check if file exists
    if not os.path.exists(args.audio_source):
        print(f"Error: File not found: {args.audio_source}")
        sys.exit(1)

    # Run analysis
    analyzer = AudioAnalyzer()
    result = analyzer.analyze(args.audio_source, args.phrase)

    # Save results
    output_file = 'analysis_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        # Convert non-serializable objects
        save_result = result.copy()
        save_result['language_confidence'] = float(
            save_result['language_confidence'])
        json.dump(save_result, f, indent=2, ensure_ascii=False)

    print(f"\nFull results saved to: {output_file}")


if __name__ == '__main__':
    main()
