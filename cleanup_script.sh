#!/bin/bash
echo "🧹 Starting directory cleanup and organization..."

# Remove unnecessary files
echo "Removing temporary and unnecessary files..."

# Remove HAR files and temporary JSON files
rm -f /app/chat.qwen.ai.har
rm -f /app/storage_state.json
rm -f /app/backend/storage_state.json

# Remove Python cache files and directories
find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /app -name "*.pyc" -delete 2>/dev/null || true

# Remove old/duplicate files
rm -f /app/backend_test.py
rm -f /app/model_analysis.py

# Remove unnecessary documentation files (keeping essential ones)
rm -f /app/UI_FIXED_STATUS.md
rm -f /app/START.md
rm -f /app/FIXED_STATUS.md
rm -f /app/QWEN_MODEL_ANALYSIS_REPORT.md
rm -f /app/model_config_summary.md
rm -f /app/MISSION_PROGRESS.md
rm -f /app/MISSION_ACCOMPLISHED.md
rm -f /app/READY_TO_USE.md

# Remove old server files that are no longer used
rm -f /app/backend/server_original.py
rm -f /app/backend/hybrid_server.py
rm -f /app/backend/utils.py

# Remove entire directories that are not needed
rm -rf /app/har_mimic 2>/dev/null || true
rm -rf /app/personalQwen 2>/dev/null || true
rm -rf /app/extension 2>/dev/null || true
rm -rf /app/ui_clone 2>/dev/null || true
rm -rf /app/backend/ui_clone 2>/dev/null || true

# Remove old requirements.txt at root (we have one in backend/)
rm -f /app/requirements.txt

echo "✅ Cleanup completed!"

# Show clean directory structure
echo "📁 Clean directory structure:"
tree /app -I 'node_modules|build|.git|__pycache__' -a -L 2 2>/dev/null || find /app -maxdepth 2 -type d | grep -v node_modules | sort