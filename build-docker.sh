#!/bin/bash

# Build script for custom SteamCMD Docker image with TC bandwidth limiting

set -e

# Configuration
GITHUB_USERNAME="astrooom"
IMAGE_NAME="steamcmd-bandwidth"
IMAGE_TAG="latest"
LOCAL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
GHCR_IMAGE_NAME="ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building custom SteamCMD Docker image with bandwidth limiting..."
echo "Local image: ${LOCAL_IMAGE_NAME}"
echo "GHCR image: ${GHCR_IMAGE_NAME}"

# Build the Docker image
docker build -t "${LOCAL_IMAGE_NAME}" -t "${GHCR_IMAGE_NAME}" .

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "📦 To push to GitHub Container Registry:"
echo "   docker push ${GHCR_IMAGE_NAME}"
echo ""
echo "🚀 To use this image with your Steam game cacher:"
echo "1. Set the environment variable:"
echo "   export STEAMCMD_DOCKER_IMAGE=${GHCR_IMAGE_NAME}"
echo ""
echo "2. Or create a .env file with:"
echo "   STEAMCMD_DOCKER_IMAGE=${GHCR_IMAGE_NAME}"
echo ""
echo "3. Run with bandwidth limiting:"
echo "   python3 run.py --app_ids=376030 --install_path=/var/lib/steam_cache \\"
echo "                  --bandwidth_enabled=true --bandwidth_down_rate=1000"
echo ""
echo "Available bandwidth limiting options:"
echo "  --bandwidth_enabled=true       Enable bandwidth limiting"
echo "  --bandwidth_up_rate=500        Upload rate limit in KB/s"
echo "  --bandwidth_down_rate=1000     Download rate limit in KB/s"
echo ""
echo "💡 Note: You must be logged in to GHCR to push:"
echo "   echo \$GITHUB_TOKEN | docker login ghcr.io -u ${GITHUB_USERNAME} --password-stdin"

