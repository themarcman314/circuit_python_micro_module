#!/bin/sh
# deploy.sh
DEST=~/insa/5a/uc_python/board/ 
rsync -rv --checksum \
  --exclude '.git*' --exclude 'README.md' --exclude 'deploy.sh' \
  --exclude 'lib/' --exclude 'pyrightconfig.json' --exclude='requirements.txt' --exclude='.editor-lib' --exclude='Makefile' \
  ./ "$DEST"/
sync
