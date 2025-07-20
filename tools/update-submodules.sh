#!/bin/bash

# Update Submodules Script
# This script updates all submodules to their latest versions

set -e

echo "🔄 Updating submodules to latest versions..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if we have submodules
if [ ! -f .gitmodules ]; then
    echo "❌ Error: No .gitmodules file found"
    exit 1
fi

echo "📋 Current submodule status:"
git submodule status

echo ""
echo "🔄 Updating submodules..."
git submodule update --remote --recursive

echo ""
echo "📋 Updated submodule status:"
git submodule status

echo ""
echo "📊 Changes summary:"
if [[ -n "$(git status --porcelain)" ]]; then
    echo "✅ Changes detected:"
    git status --porcelain
    echo ""
    echo "💡 To commit these changes, run:"
    echo "   git add ."
    echo "   git commit -m 'chore: update submodules to latest versions'"
    echo "   git push"
else
    echo "✅ No changes detected - all submodules are up to date"
fi

echo ""
echo "🎉 Submodule update complete!" 