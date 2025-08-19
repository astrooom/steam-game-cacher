#!/bin/bash

# Build script for custom SteamCMD Docker image with TC bandwidth limiting

set -e

IMAGE_NAME="steamcmd-bandwidth"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building custom SteamCMD Docker image with bandwidth limiting..."
echo "Image name: ${FULL_IMAGE_NAME}"

# Build the Docker image
docker build -t "${FULL_IMAGE_NAME}" .

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "To use this image with your Steam game cacher:"
echo "1. Set the environment variable:"
echo "   export STEAMCMD_DOCKER_IMAGE=${FULL_IMAGE_NAME}"
echo ""
echo "2. Or create a .env file with:"
echo "   STEAMCMD_DOCKER_IMAGE=${FULL_IMAGE_NAME}"
echo ""
echo "3. Run with bandwidth limiting:"
echo "   python3 run.py --app_ids=376030 --install_path=/var/lib/steam_cache \\"
echo "                  --bandwidth_enabled=true --bandwidth_down_rate=1000"
echo ""
echo "Available bandwidth limiting options:"
echo "  --bandwidth_enabled=true       Enable bandwidth limiting"
echo "  --bandwidth_up_rate=500        Upload rate limit in KB/s"
echo "  --bandwidth_down_rate=1000     Download rate limit in KB/s"

