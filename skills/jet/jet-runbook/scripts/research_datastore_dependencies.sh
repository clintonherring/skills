#!/bin/bash
# Search for database and data store configurations

echo "=== Searching for data store configurations ==="
grep -r "ConnectionString\|Database\|MongoDb\|DynamoDB\|Redis" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.cs" --include="*.java" 2>/dev/null | head -20
