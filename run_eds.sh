#!/bin/bash

for i in {1..100}
do
  python3 main.py "Ed$i" > /dev/null 2>&1
done