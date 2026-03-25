#!/bin/bash
# One-time migration: ~/.niuma/ → ~/.jbot/
# Safe to run multiple times — skips if already migrated.
set -euo pipefail

OLD_DIR="$HOME/.niuma"
NEW_DIR="$HOME/.jbot"

if [ ! -d "$OLD_DIR" ]; then
    echo "✅ No ~/.niuma/ found — nothing to migrate."
    exit 0
fi

if [ -d "$NEW_DIR" ] && [ -f "$NEW_DIR/config.yaml" ]; then
    echo "✅ ~/.jbot/ already exists with config. Skipping migration."
    echo "   (Delete ~/.niuma/ manually if no longer needed)"
    exit 0
fi

echo "🔄 Migrating ~/.niuma/ → ~/.jbot/..."
mkdir -p "$NEW_DIR"

# Copy all files
for f in "$OLD_DIR"/*; do
    [ ! -e "$f" ] && continue
    base=$(basename "$f")
    # Rename niuma.db → jbot.db, niuma.log → jbot.log
    case "$base" in
        niuma.db)   dest="$NEW_DIR/jbot.db" ;;
        niuma.log)  dest="$NEW_DIR/jbot.log" ;;
        *)          dest="$NEW_DIR/$base" ;;
    esac
    cp -a "$f" "$dest"
    echo "  Copied: $base → $(basename "$dest")"
done

# Fix paths inside config.yaml
if [ -f "$NEW_DIR/config.yaml" ]; then
    sed -i '' 's|~/.niuma/niuma.db|~/.jbot/jbot.db|g' "$NEW_DIR/config.yaml"
    sed -i '' 's|~/.niuma/niuma.log|~/.jbot/jbot.log|g' "$NEW_DIR/config.yaml"
    sed -i '' 's|~/.niuma/|~/.jbot/|g' "$NEW_DIR/config.yaml"
    sed -i '' 's|name: "niuma"|name: "jbot"|g' "$NEW_DIR/config.yaml"
    sed -i '' 's|trigger: "@niuma"|trigger: "@jbot"|g' "$NEW_DIR/config.yaml"
    sed -i '' 's|emoji: "🐴"|emoji: "🤖"|g' "$NEW_DIR/config.yaml"
    echo "  Updated paths and bot identity in config.yaml"
fi

echo ""
echo "✅ Migration complete!"
echo "   Old: $OLD_DIR (kept as backup — delete when ready)"
echo "   New: $NEW_DIR"
echo ""
echo "   Start J-Bot: bash scripts/start.sh"
