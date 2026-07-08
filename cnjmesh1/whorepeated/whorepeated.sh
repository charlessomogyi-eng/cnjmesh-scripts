#!/bin/bash
CONTACTS=/tmp/contacts.json
MAXAGE=300

if [ ! -f "$CONTACTS" ] || [ $(( $(date +%s) - $(stat -c %Y "$CONTACTS") )) -gt $MAXAGE ]; then
    meshcore-cli -s /dev/ttyACM0 -j contacts > "$CONTACTS"
fi

python3 /opt/whorepeated/merge_contacts.py

if [ -z "$1" ]; then
    echo "Usage: whorepeated <path_hex>   e.g. whorepeated 2521"
    exit 1
fi

python3 /opt/whorepeated/path_lookup.py "$1"
