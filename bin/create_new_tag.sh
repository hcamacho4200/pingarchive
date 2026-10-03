#!/bin/bash
set -e

last_tag=$(git tag | sort -V | tail -1)
new_tag=$(echo $last_tag | awk -F. -v OFS=. '{$NF++; print}')

read -p "Enter tag message: " TAG_MESSAGE

if [[ -z "$TAG_MESSAGE" ]]; then
  echo "❌ Tag message is required"
  exit 1
fi

git tag $new_tag -m "$TAG_MESSAGE"
git push prod $new_tag 
echo "New tag $new_tag created"
