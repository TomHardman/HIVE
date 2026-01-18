#!/bin/bash
DOWNLOAD_DIR=plays/downloads
PLAY_DIR=plays/all

# List of files to download from the server
base_url="http://www.boardspace.net/hive/hivegames"
files=(")  # You would need the actual filenames

# Download all files using curl
for file in "${files[@]}"; do
  curl -o $DOWNLOAD_DIR/$file $base_url/$file
done

# Unzip all game files
find $DOWNLOAD_DIR -name '*.zip' | xargs -n1 -I % unzip % -d $PLAY_DIR

# Copy remaining .sgf files
find $DOWNLOAD_DIR -name "*.sgf" -type f | xargs -n1 -I % cp % $PLAY_DIR
