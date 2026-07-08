import json, os, time

LIVE = "/tmp/contacts.json"
ARCHIVE = "/opt/whorepeated/contacts_archive.json"

def load_archive():
    if os.path.exists(ARCHIVE):
        with open(ARCHIVE) as f:
            return json.load(f)
    return {}

def main():
    with open(LIVE) as f:
        data = json.load(f)
    contacts = data if isinstance(data, list) else data.get('contacts', data)
    contacts = contacts.values() if isinstance(contacts, dict) else contacts

    archive = load_archive()
    now = int(time.time())
    live_prefixes = set()

    for c in contacts:
        pk = c.get('public_key', '')
        if not pk:
            continue
        prefix = pk[:2].lower()
        name = c.get('adv_name') or c.get('name', '?')
        ctype = c.get('type', '?')
        live_prefixes.add(prefix)

        entry = archive.setdefault(prefix, {})
        name_entry = entry.setdefault(name, {"first_seen": now, "type": ctype})
        name_entry["last_seen"] = now
        name_entry["type"] = ctype
        name_entry["full_pubkey"] = pk

    archive["_meta"] = {"last_refresh": now, "live_prefixes": sorted(live_prefixes)}

    with open(ARCHIVE, "w") as f:
        json.dump(archive, f, indent=2)

    print(f"Archive updated: {len(archive)-1} known prefixes, {len(live_prefixes)} currently live")

if __name__ == "__main__":
    main()
