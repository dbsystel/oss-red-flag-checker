#!/bin/bash

# You can choose different typed, e.g. pe or pei
TYPE=pe
# What to do with comments? : for doing nothing, $TYPE for doing the same as with code
COMM=":"

. ~/Git/github/demo-magic/demo-magic.sh

clear

$TYPE 'poetry run ossrfc -c -r https://github.com/hashicorp/terraform'
$TYPE 'poetry run ossrfc -c -r https://github.com/curl/curl'
$TYPE 'poetry run ossrfc -c -r https://github.com/azure/azure-dev --json | jq ".repositories[0] | {cla_files, cla_pulls}"'
wait
