#!/bin/bash
# Search for HTTP client configurations and timeout settings in the codebase

echo "=== Searching for HTTP clients ==="
grep -r "HttpClient\|RestTemplate\|fetch\|axios" --include="*.cs" --include="*.java" --include="*.ts" --include="*.js" 2>/dev/null | head -20

echo ""
echo "=== Searching for timeout configurations ==="
grep -r "timeout\|Timeout" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.cs" --include="*.java" 2>/dev/null | head -20
