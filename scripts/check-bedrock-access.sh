#!/bin/bash
# Check Bedrock Model Access
# Verifies that required Bedrock models are accessible before deployment
# Usage: ./check-bedrock-access.sh [--dry-run] [--verbose]

set -e

# Parse arguments
DRY_RUN=false
VERBOSE=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
    esac
done

# Required models
declare -A REQUIRED_MODELS
REQUIRED_MODELS=(
    ["anthropic.claude-haiku-4-5-20251001-v1:0"]="Claude Haiku 4.5"
    ["anthropic.claude-sonnet-4-5-20250929-v1:0"]="Claude Sonnet 4.5"
    ["amazon.titan-embed-text-v2:0"]="Amazon Titan Embed v2"
)

echo -e "\033[0;36m🔍 Checking Bedrock Model Access\033[0m"
echo -e "\033[0;36m==================================\033[0m"
echo ""

# Get current region
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION=${AWS_DEFAULT_REGION:-us-east-1}
fi
echo -e "\033[0;90mRegion: $REGION\033[0m"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "\033[0;33m[DRY RUN MODE]\033[0m"
    echo -e "\033[0;33mWould check access to the following models:\033[0m"
    for model_id in "${!REQUIRED_MODELS[@]}"; do
        echo -e "\033[0;90m  - ${REQUIRED_MODELS[$model_id]} ($model_id)\033[0m"
    done
    echo ""
    echo -e "\033[0;33mCommands that would be executed:\033[0m"
    echo -e "\033[0;90m  aws bedrock list-foundation-models --region $REGION --by-provider anthropic\033[0m"
    echo -e "\033[0;90m  aws bedrock list-foundation-models --region $REGION --by-provider amazon\033[0m"
    echo ""
    echo -e "\033[0;32m✅ Dry run complete\033[0m"
    exit 0
fi

# Check Anthropic models
echo -e "\033[0;36mChecking Anthropic models...\033[0m"
ANTHROPIC_MODELS_JSON=$(aws bedrock list-foundation-models --region "$REGION" --by-provider anthropic 2>&1) || {
    echo -e "\033[0;31m❌ Failed to check Anthropic models\033[0m"
    echo -e "\033[0;31mError: $ANTHROPIC_MODELS_JSON\033[0m"
    echo ""
    echo -e "\033[0;33mPlease verify:\033[0m"
    echo -e "\033[0;33m  1. AWS credentials are configured\033[0m"
    echo -e "\033[0;33m  2. Region $REGION supports Bedrock\033[0m"
    echo -e "\033[0;33m  3. You have bedrock:ListFoundationModels permission\033[0m"
    exit 1
}

if [ "$VERBOSE" = true ]; then
    echo -e "\033[0;90mAnthropic models response:\033[0m"
    echo -e "\033[0;90m$ANTHROPIC_MODELS_JSON\033[0m"
    echo ""
fi

# Check Amazon models
echo -e "\033[0;36mChecking Amazon models...\033[0m"
AMAZON_MODELS_JSON=$(aws bedrock list-foundation-models --region "$REGION" --by-provider amazon 2>&1) || {
    echo -e "\033[0;31m❌ Failed to check Amazon models\033[0m"
    echo -e "\033[0;31mError: $AMAZON_MODELS_JSON\033[0m"
    exit 1
}

if [ "$VERBOSE" = true ]; then
    echo -e "\033[0;90mAmazon models response:\033[0m"
    echo -e "\033[0;90m$AMAZON_MODELS_JSON\033[0m"
    echo ""
fi

# Extract model IDs
ANTHROPIC_MODEL_IDS=$(echo "$ANTHROPIC_MODELS_JSON" | jq -r '.modelSummaries[]?.modelId' 2>/dev/null || echo "")
AMAZON_MODEL_IDS=$(echo "$AMAZON_MODELS_JSON" | jq -r '.modelSummaries[]?.modelId' 2>/dev/null || echo "")
ALL_AVAILABLE_MODELS="$ANTHROPIC_MODEL_IDS"$'\n'"$AMAZON_MODEL_IDS"

if [ "$VERBOSE" = true ]; then
    echo -e "\033[0;90mAll available models:\033[0m"
    echo "$ALL_AVAILABLE_MODELS" | while read -r model; do
        [ -n "$model" ] && echo -e "\033[0;90m  - $model\033[0m"
    done
    echo ""
fi

# Check each required model
MISSING_MODELS=()
for model_id in "${!REQUIRED_MODELS[@]}"; do
    model_name="${REQUIRED_MODELS[$model_id]}"
    
    if echo "$ALL_AVAILABLE_MODELS" | grep -q "^$model_id$"; then
        echo -e "\033[0;32m✅ $model_name\033[0m"
    else
        echo -e "\033[0;31m❌ $model_name ($model_id)\033[0m"
        MISSING_MODELS+=("$model_name|$model_id")
    fi
done

echo ""

if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo -e "\033[0;31m⚠️  Missing Model Access\033[0m"
    echo -e "\033[0;31m========================\033[0m"
    echo ""
    echo -e "\033[0;33mThe following models are not accessible in region $REGION:\033[0m"
    for model in "${MISSING_MODELS[@]}"; do
        IFS='|' read -r name id <<< "$model"
        echo -e "\033[0;33m  - $name ($id)\033[0m"
    done
    echo ""
    echo -e "\033[0;36mAction Required:\033[0m"
    echo -e "\033[0;37m  1. Open AWS Console: https://console.aws.amazon.com/bedrock\033[0m"
    echo -e "\033[0;37m  2. Navigate to: Bedrock > Model access\033[0m"
    echo -e "\033[0;37m  3. Click 'Manage model access'\033[0m"
    echo -e "\033[0;37m  4. Enable the missing models\033[0m"
    echo -e "\033[0;37m  5. Wait for access to be granted (usually instant)\033[0m"
    echo -e "\033[0;37m  6. Re-run this script to verify\033[0m"
    echo ""
    echo -e "\033[0;90mAlternative regions with Bedrock support:\033[0m"
    echo -e "\033[0;90m  - us-east-1, us-west-2, eu-west-1, ap-southeast-1\033[0m"
    echo ""
    exit 1
fi

echo -e "\033[0;32m✅ All required models are accessible!\033[0m"
echo ""
exit 0
