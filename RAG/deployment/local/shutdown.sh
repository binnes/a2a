#!/bin/bash

# Local Shutdown Script for RAG Agents
# Stops and removes all containers deployed with Podman

set -e

echo '==========================================================='
echo 'RAG Agents - Local Shutdown'
echo '==========================================================='
echo ''

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed${NC}"
    exit 1
fi

# Check if podman-compose is installed
if ! command -v podman-compose &> /dev/null; then
    echo -e "${RED}Error: podman-compose is not installed${NC}"
    exit 1
fi

# Check what's currently running
echo "Checking running containers..."
RUNNING_CONTAINERS=$(podman ps --filter "name=milvus-" --filter "name=rag-" --format "{{.Names}}" 2>/dev/null || echo "")

if [ -z "$RUNNING_CONTAINERS" ]; then
    echo -e "${YELLOW}No RAG containers are currently running${NC}"
    echo ""
    read -p "Do you want to clean up any stopped containers and volumes? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Shutdown cancelled"
        exit 0
    fi
else
    echo -e "${GREEN}Found running containers:${NC}"
    echo "$RUNNING_CONTAINERS" | sed 's/^/  - /'
    echo ""
fi

# Ask about volume cleanup
echo -e "${YELLOW}⚠ Volume Cleanup Options:${NC}"
echo "  1. Stop containers only (preserve data)"
echo "  2. Stop containers and remove volumes (delete all data)"
echo ""
read -p "Choose option (1 or 2): " -n 1 -r
echo
echo ""

REMOVE_VOLUMES=false
if [[ $REPLY == "2" ]]; then
    REMOVE_VOLUMES=true
    echo -e "${RED}⚠ WARNING: This will delete all data in Milvus, MinIO, and etcd!${NC}"
    read -p "Are you sure? Type 'yes' to confirm: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Volume removal cancelled. Stopping containers only..."
        REMOVE_VOLUMES=false
    fi
fi

echo ''
echo '==========================================================='
echo 'Stopping Services'
echo '==========================================================='

# Stop all services
echo "Stopping all RAG services..."
podman-compose down

# Check if containers are stopped
STILL_RUNNING=$(podman ps --filter "name=milvus-" --filter "name=rag-" --format "{{.Names}}" 2>/dev/null || echo "")

if [ -z "$STILL_RUNNING" ]; then
    echo -e "${GREEN}✓ All containers stopped${NC}"
else
    echo -e "${YELLOW}⚠ Some containers are still running:${NC}"
    echo "$STILL_RUNNING" | sed 's/^/  - /'
    echo ""
    echo "Forcing stop..."
    echo "$STILL_RUNNING" | xargs -r podman stop
    echo -e "${GREEN}✓ All containers force-stopped${NC}"
fi

# Remove stopped containers
echo ""
echo "Removing stopped containers..."
STOPPED_CONTAINERS=$(podman ps -a --filter "name=milvus-" --filter "name=rag-" --format "{{.Names}}" 2>/dev/null || echo "")

if [ -n "$STOPPED_CONTAINERS" ]; then
    echo "$STOPPED_CONTAINERS" | xargs -r podman rm
    echo -e "${GREEN}✓ Stopped containers removed${NC}"
else
    echo -e "${GREEN}✓ No stopped containers to remove${NC}"
fi

# Remove volumes if requested
if [ "$REMOVE_VOLUMES" = true ]; then
    echo ""
    echo '==========================================================='
    echo 'Removing Volumes'
    echo '==========================================================='
    
    # Get volume names from compose file
    VOLUMES=$(podman volume ls --filter "name=local_" --format "{{.Name}}" 2>/dev/null || echo "")
    
    if [ -n "$VOLUMES" ]; then
        echo "Removing volumes:"
        echo "$VOLUMES" | sed 's/^/  - /'
        echo "$VOLUMES" | xargs -r podman volume rm
        echo -e "${GREEN}✓ Volumes removed${NC}"
    else
        echo -e "${GREEN}✓ No volumes to remove${NC}"
    fi
fi

# Clean up dangling images (optional)
echo ""
read -p "Do you want to remove unused container images? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Removing dangling images..."
    podman image prune -f
    echo -e "${GREEN}✓ Dangling images removed${NC}"
fi

echo ''
echo '==========================================================='
echo '✓ Shutdown Complete!'
echo '==========================================================='
echo ''

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${GREEN}All containers and volumes have been removed${NC}"
    echo "To redeploy, run: bash deploy.sh"
else
    echo -e "${GREEN}All containers have been stopped and removed${NC}"
    echo "Data volumes have been preserved"
    echo "To restart, run: bash deploy.sh"
fi

echo ''
echo 'Useful commands:'
echo '  - Check remaining containers: podman ps -a'
echo '  - Check remaining volumes: podman volume ls'
echo '  - Check remaining images: podman images'
echo '  - Clean everything: podman system prune -a --volumes'
echo ''

# Made with Bob