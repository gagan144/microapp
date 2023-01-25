#!/bin/bash
echo $(grep -o '"version": "[^"]*' version.json | grep -o '[^"]*$')