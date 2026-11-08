#!/bin/bash
set -e

REPO_DIR="/Users/nikhilbhaskar/Desktop/KUKU Deck/kuku-promo_finder-g"
cd "$REPO_DIR"

echo "============================================================"
echo "🚀 Pushing KUKU PromoFinder Studio to GitHub"
echo "============================================================"

# Ensure gh is in PATH
export PATH="/opt/homebrew/bin:$PATH"

# Check if gh is authenticated
if ! gh auth status &>/dev/null; then
    echo ""
    echo "🔑 GitHub CLI authentication required."
    echo "Running 'gh auth login' with web browser..."
    echo ""
    gh auth login -w -p https
fi

echo ""
echo "Creating / linking repository on your GitHub account..."
if ! gh repo view kuku-promo-finder &>/dev/null; then
    gh repo create kuku-promo-finder --public --source=. --remote=origin --push
    echo ""
    echo "🎉 Repository created and pushed successfully!"
else
    echo "Repository already exists. Pushing latest commits..."
    git branch -M main
    git push -u origin main
    echo ""
    echo "🎉 Latest changes pushed successfully!"
fi

REPO_URL=$(gh repo view --json url -q ".url" 2>/dev/null || echo "https://github.com/$(gh api user -q .login)/kuku-promo-finder")
echo "============================================================"
echo "🌟 Your submission link is ready:"
echo "   $REPO_URL"
echo "============================================================"
