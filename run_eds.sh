#!/bin/bash

for i in {1..10}
do
  python3 main.py "Ed$i" --pdf > /dev/null 2>&1
done