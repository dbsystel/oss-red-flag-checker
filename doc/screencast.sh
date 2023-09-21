#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

# Script to create the asciinema recording:
# asciinema rec ~/ossrfc.cast -c ./doc/screencast.sh

# You can choose different typed, e.g. pe or pei
TYPE=pei
# What to do with comments? : for doing nothing, $TYPE for doing the same as with code
COMM=":"

. ~/Git/github/demo-magic/demo-magic.sh

clear

$TYPE 'ossrfc -c -r https://github.com/hashicorp/terraform'
$TYPE 'ossrfc -c -r https://github.com/curl/curl'
$TYPE 'ossrfc -c -r https://github.com/azure/azure-dev --json | jq ".repositories[0] | {cla_files, cla_pulls}"'
wait
