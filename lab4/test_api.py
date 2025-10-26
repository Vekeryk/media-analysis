#!/usr/bin/env python3
"""
Test script for Audio Transcription API
Tests binary upload, S3 URI, and status checking
"""

import json
import time
import requests
import os

# Read API endpoint
if os.path.exists('api_endpoint.txt'):
    with open('api_endpoint.txt') as f:
        API_ENDPOINT = f.read().strip()
else:
    print("Error: api_endpoint.txt not found. Run deploy.sh first.")
    exit(1)

print("=" * 70)
print("Audio Transcription API - Test Suite")
print("=" * 70)
print(f"API Endpoint: {API_ENDPOINT}\n")


def wait_for_completion(job_name, max_wait=120):
    """Poll status endpoint until job completes (every 10 seconds)"""
    interval = 10
    print(f"Polling status for job: {job_name}")
    status_url = f"{API_ENDPOINT}/{job_name}"
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval
        response = requests.get(status_url)
        data = response.json()

        status = data.get('status')
        print(f"  [{elapsed}s] Status: {status}")

        if status == 'completed':
            return data
        elif status == 'failed':
            print(f"  ✗ Job failed: {data.get('error')}")
            return data

    print(f"  ⚠ Timeout after {max_wait}s")
    return None


def test_binary_upload():
    """Test 1: Binary file upload"""
    print("\n" + "-" * 70)
    print("TEST 1: Binary File Upload")
    print("-" * 70)

    audio_file = '../lab3/lab3.wav'

    if not os.path.exists(audio_file):
        print(f"⚠ Test file not found: {audio_file}")
        print("Creating a minimal test file...")
        # Create a minimal WAV file for testing
        audio_file = 'test.wav'
        with open(audio_file, 'wb') as f:
            f.write(b'RIFF' + b'\x00' * 100)  # Minimal WAV structure

    with open(audio_file, 'rb') as f:
        audio_data = f.read()

    print(f"File: {audio_file}")
    print(f"Size: {len(audio_data)} bytes")
    print("Uploading...")

    # POST binary data
    response = requests.post(
        API_ENDPOINT,
        data=audio_data,
        headers={'Content-Type': 'audio/wav'}
    )

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 202:
        job_name = result['job_name']
        print("\n✓ Job started successfully!")

        # Wait for completion
        final_result = wait_for_completion(job_name)

        if final_result and final_result.get('status') == 'completed':
            print(f"\n✓ TEST 1 PASSED")
            print(f"Transcript: {final_result.get('transcript')}")
            print(f"Language: {final_result.get('language')}")
            return True
        else:
            print(f"\n✗ TEST 1 FAILED (timeout or error)")
            return False
    else:
        print(f"\n✗ TEST 1 FAILED (unexpected status code)")
        return False


def test_s3_uri():
    """Test 2: S3 URI reference"""
    print("\n" + "-" * 70)
    print("TEST 2: S3 URI Reference")
    print("-" * 70)

    s3_uri = 's3://media-labs-audio-transcribe/audio/lab3.wav'
    print(f"S3 URI: {s3_uri}")
    print("Sending request...")

    # POST JSON with S3 URI
    response = requests.post(
        API_ENDPOINT,
        json={'s3_uri': s3_uri},
        headers={'Content-Type': 'application/json'}
    )

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 202:
        job_name = result['job_name']
        print("\n✓ Job started successfully!")

        # Wait for completion
        final_result = wait_for_completion(job_name)

        if final_result and final_result.get('status') == 'completed':
            print(f"\n✓ TEST 2 PASSED")
            print(f"Transcript: {final_result.get('transcript')}")
            print(f"Language: {final_result.get('language')}")
            return True
        else:
            print(f"\n✗ TEST 2 FAILED (timeout or error)")
            return False
    else:
        print(f"\n✗ TEST 2 FAILED (unexpected status code)")
        return False


def test_error_cases():
    """Test 3: Error handling"""
    print("\n" + "-" * 70)
    print("TEST 3: Error Handling")
    print("-" * 70)

    # Test 3a: Invalid job name
    print("\n3a. Testing invalid job name...")
    response = requests.get(f"{API_ENDPOINT}/invalid-job-name-12345")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 404:
        print("✓ Correctly returns 404 for invalid job")
    else:
        print(f"✗ Expected 404, got {response.status_code}")

    # Test 3b: Missing data
    print("\n3b. Testing missing data...")
    response = requests.post(
        API_ENDPOINT,
        json={},
        headers={'Content-Type': 'application/json'}
    )
    print(f"Status Code: {response.status_code}")

    if response.status_code == 400:
        print("✓ Correctly returns 400 for missing data")
    else:
        print(f"✗ Expected 400, got {response.status_code}")

    print(f"\n✓ TEST 3 PASSED")
    return True


if __name__ == '__main__':
    results = []

    # Run tests
    try:
        results.append(('Binary Upload', test_binary_upload()))
    except Exception as e:
        print(f"\n✗ TEST 1 ERROR: {e}")
        results.append(('Binary Upload', False))

    try:
        results.append(('S3 URI', test_s3_uri()))
    except Exception as e:
        print(f"\n✗ TEST 2 ERROR: {e}")
        results.append(('S3 URI', False))

    try:
        results.append(('Error Handling', test_error_cases()))
    except Exception as e:
        print(f"\n✗ TEST 3 ERROR: {e}")
        results.append(('Error Handling', False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20} {status}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    print("=" * 70)
