#!/bin/bash

# Deployment script for sd_image_processing_and_upload

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
APP_DIR="/opt/sd_image_processing_and_upload"
VENV_DIR="$APP_DIR/venv"
GITHUB_REPO="https://github.com/BitsofJeremy/sd_image_processing_and_upload.git"
BRANCH="main"
USER_NAME="jeremy"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
   log "This script must be run as root"
   exit 1
fi

# Function to install dependencies
install_dependencies() {
    log "Installing dependencies..."
    apt-get update
    apt-get install -y python3 python3-venv python3-pip nginx
}

# Function to create user and set up directories
setup_user_and_directories() {
    log "Setting up directories..."
    mkdir -p $APP_DIR
    chown $USER_NAME:$USER_NAME $APP_DIR
}

# Function to clone or update repository
clone_or_update_repo() {
    log "Cloning or updating repository..."
    if [ -d "$APP_DIR/.git" ]; then
        cd $APP_DIR
        sudo -u $USER_NAME git fetch origin $BRANCH
        sudo -u $USER_NAME git reset --hard origin/$BRANCH
    else
        sudo -u $USER_NAME git clone $GITHUB_REPO $APP_DIR
        cd $APP_DIR
        sudo -u $USER_NAME git checkout $BRANCH
    fi
}

# Function to set up virtual environment and install requirements
setup_venv() {
    log "Setting up virtual environment..."
    if [ ! -d "$VENV_DIR" ]; then
        sudo -u $USER_NAME python3 -m venv $VENV_DIR
    fi
    sudo -u $USER_NAME $VENV_DIR/bin/pip install -r $APP_DIR/requirements.txt
}

# Function to update application
update_app() {
    log "Updating application..."
    clone_or_update_repo
    setup_venv
    log "Update completed successfully."
}

# Main deployment function
deploy() {
    install_dependencies
    setup_user_and_directories
    clone_or_update_repo
    setup_venv
    log "Deployment completed successfully."
}

# Check for update flag
if [ "$1" == "--update" ]; then
    update_app
else
    deploy
fi

log "Script execution completed."