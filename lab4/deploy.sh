#!/bin/bash
# Automated deployment script for Lab 4
# Installs SAM CLI if needed and deploys infrastructure

set -e  # Exit on error

# Load AWS credentials from .env file
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✓ Loaded AWS credentials from .env"
else
    echo "⚠ Warning: .env file not found. Make sure AWS credentials are set."
fi

echo "================================================"
echo "Lab 4 - SAM Deployment Script"
echo "================================================"

# Check if SAM CLI is installed
echo ""
echo "Checking SAM CLI installation..."
if command -v sam &> /dev/null; then
    SAM_VERSION=$(sam --version)
    echo "✓ SAM CLI installed: $SAM_VERSION"
else
    echo "⚠ SAM CLI not found. Installing..."

    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "Detected macOS. Installing via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install aws-sam-cli
        else
            echo "Homebrew not found. Installing via pip..."
            pip install aws-sam-cli
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Detected Linux. Installing via pip..."
        pip install aws-sam-cli
    else
        # Fallback
        echo "Installing via pip..."
        pip install aws-sam-cli
    fi

    echo "✓ SAM CLI installed"
fi

# If you want a fresh start, run: aws cloudformation delete-stack --stack-name media-labs-transcribe-stack

# Build Lambda package
echo ""
echo "Building Lambda package..."
sam build

# Deploy via SAM
echo ""
echo "Deploying infrastructure..."
sam deploy --resolve-s3

# Get API endpoint
echo ""
echo "Retrieving API endpoint..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name media-labs-transcribe-stack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

echo "$API_ENDPOINT" > api_endpoint.txt

echo ""
echo "================================================"
echo "✓ Deployment Complete!"
echo "================================================"
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo "Saved to: api_endpoint.txt"
echo ""
echo "Test with:"
echo "  curl -X POST $API_ENDPOINT \\"
echo "    -H \"Content-Type: audio/wav\" \\"
echo "    --data-binary \"@../lab3/lab3.wav\""
echo ""
echo "Or run: python test_api.py"
echo ""
