import json, sys, time

ARCHIVE = "/opt/whorepeated/contacts_archive.json"

def human_age(seconds):
    days = seconds // 86400
    if days > 0:
        return f"{days}d ago"
    hours = seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    return f"{seconds // 60}m ago"

def resolve(path_hex):
    with open(ARCHIVE) as f:
        archive = json.load(f)

    live_prefixes = set(archive.get("_meta", {}).get("live_prefixes", []))
    now = int(time.time())

    hops = [path_hex[i:i+2].lower() for i in range(0, len(path_hex), 2)]
    for h in hops:
        entry = archive.get(h)
        if not entry:
            print(f"  {h} -> UNKNOWN (never seen)")
            continue

        names = {k: v for k, v in entry.items() if k != "_meta"}
        status = "LIVE" if h in live_prefixes else "ARCHIVED (evicted from device cache)"

        if len(names) == 1:
            name, meta = next(iter(names.items()))
            age = human_age(now - meta["last_seen"])
            print(f"  {h} -> {name} [{status}, last seen {age}]")
        else:
            print(f"  {h} -> ambiguous, {len(names)} names share this prefix [{status}]:")
            for name, meta in names.items():
                age = human_age(now - meta["last_seen"])
                print(f"      - {name} (last seen {age})")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else input("Path hex (e.g. 2521): ")
    resolve(path)
