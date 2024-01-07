#!/bin/bash

while read -r line; do
   if [[ $line =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
      export "$line"
   fi
done < .env

echo "Environment variables exported."