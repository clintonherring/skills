#!/bin/bash
# Search for message-based system configurations (Kafka, SNS, SQS)

echo "=== Searching for messaging configurations ==="
grep -r "kafka\|sns\|sqs\|messaging" --include="*.json" --include="*.yaml" --include="*.yml" 2>/dev/null | head -20
