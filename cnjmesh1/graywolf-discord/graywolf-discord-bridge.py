#!/usr/bin/env python3
import asyncio, logging, os, re, signal, sqlite3, sys, time
from datetime import datetime, timezone
import aiohttp

DISCORD_WEBHOOK_RF       = os.environ.get("DISCORD_WEBHOOK_RF", "")
DISCORD_WEBHOOK_INTERNET = os.environ.get("DISCORD_WEBHOOK_INTERNET", "")
DISCORD_WEBHOOK_RF_MESHCORE       = os.environ.get("DISCORD_WEBHOOK_RF_MESHCORE", "")
DISCORD_WEBHOOK_INTERNET_MESHCORE = os.environ.get("DISCORD_WEBHOOK_INTERNET_MESHCORE", "")
GRAYWOLF_DB          = "/var/lib/graywolf/graywolf.db"
MAX_POSTS_PER_MINUTE = 20
DEDUP_WINDOW         = 120
DB_POLL_INTERVAL     = 10
BLOCKLIST = {
    "ANSRVR", "9W2KEY-12", "CT7AQH-5",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
log = logging.getLogger("gw-discord")

LOG_RE = re.compile(r'msg="aprs packet".*?type=(\S+).*?source=(\S+).*?dest=(\S+).*?path="\[([^\]]*)\]"(?:.*?lat=([\d.\-]+))?(?:.*?lon=([\d.\-]+))?(?:.*?comment=(.*))?')
TEXT_RE  = re.compile(r'text="([^"]*)"')
TO_RE    = re.compile(r'\bto=(\S+)')
INNER_RE = re.compile(r'::[^\s:]+\s*:(.+?)(?:\{[A-Z0-9]+\})?$')

def is_aprs_message(comment):
    return bool(re.search(r"::[A-Z0-9\-]+\s*:", comment)) if comment else False

def extract_inner(comment):
    if not comment: return None, None
    comment = comment.strip().strip('"')
    sender_match = re.match(r'^([A-Z0-9\-]+)>', comment)
    sender = sender_match.group(1) if sender_match else None
    msg_match = INNER_RE.search(comment)
    message = msg_match.group(1).strip() if msg_match else comment
    if message and re.match(r'^(ack|rej)[A-Za-z0-9]*', message.strip(), re.IGNORECASE):
        return sender, None
    return sender, message

def classify_path(path_str):
    if not path_str: return "rf"
    return "internet" if "TCPIP" in path_str.upper() else "rf"

def is_direct_rf(path_str): return "*" not in path_str

def format_path_human(path_str):
    if not path_str: return "APRS-IS"
    parts = [p.strip().rstrip('*') for p in path_str.split(',') if p.strip()]
    filtered = [p for p in parts if p not in ('TCPIP','RFONLY','NOGATE','qAC','qAR','qAO','qAS','WIDE1-1','WIDE2-1','WIDE2')]
    return " -> ".join(filtered) if filtered else "APRS-IS"

def format_message(fields, channel_type):
    icon  = "\U0001f4e1" if channel_type == "rf" else "\U0001f310"
    path  = fields.get("path", "") or ""
    ptype = fields.get("type", "")
    comment = fields.get("comment") or ""
    ts = datetime.now(timezone.utc).strftime("%B %-d, %Y %-I:%M %p UTC")
    label = ("RF Direct" if is_direct_rf(path) else "RF Message") if channel_type == "rf" else "Internet Message"
    if ptype == "third-party":
        pass  # K2GIA> packets handled by extract_inner below
        if not is_aprs_message(comment): return None
        inner_sender, message = extract_inner(comment)
        if not message: return None
        if re.match(r'^(ack|rej)[A-Za-z0-9]*', message.strip(), re.IGNORECASE): return None
        display_from = inner_sender if inner_sender else fields.get("source","Unknown")
    elif ptype == "message":
        display_from = fields.get("source","Unknown")
        message = comment.strip() if comment else None
        if message and re.match(r'^(ack|rej)[A-Za-z0-9]*', message, re.IGNORECASE): return None
    else:
        display_from = fields.get("source","Unknown")
        message = comment.strip() if comment else None
    if not message: return None
    message = re.sub(r'\{[A-Za-z0-9]{1,5}\}?"*$', '', message).rstrip('"').strip()
    if not message or len(message.strip()) < 3: return None
    if any(ord(c) < 32 for c in message.strip()): return None
    printable = sum(1 for c in message.strip() if c.isprintable())
    if printable / len(message.strip()) < 0.7: return None
    addressee_match = re.search(r'::([A-Z0-9\-]+)\s*:', comment)
    addressee = addressee_match.group(1).strip() if addressee_match else fields.get("dest","")
    via = format_path_human(path)
    return {"content": f"{icon} **{label}** - {ts}\n**From:** {display_from}\n**To:** {addressee}\n**Message:** {message[:200]}\n**Via:** {via}"}

def format_db_message(row):
    from_call = row[4]; to_call = row[5]; message = row[6] or ""; source = row[14] or ""; path = row[16] or ""
    if not message.strip() or len(message.strip()) < 2: return None, None
    ts = datetime.now(timezone.utc).strftime("%B %-d, %Y %-I:%M %p UTC")
    if source == "is":
        icon = "\U0001f310"; label = "Internet Message"; channel_type = "internet"
    else:
        icon = "\U0001f4e1"; label = "RF Message"; channel_type = "rf"
    via = format_path_human(path) if path else ("APRS-IS" if source == "is" else "RF")
    return {"content": f"{icon} **{label}** - {ts}\n**From:** {from_call}\n**To:** {to_call}\n**Message:** {message.strip()[:200]}\n**Via:** {via}"}, channel_type

class WebhookPoster:
    def __init__(self, url, name): self.url=url; self.name=name; self._post_times=[]
    def _prune(self): cutoff=time.monotonic()-60; self._post_times=[t for t in self._post_times if t>cutoff]
    def _rate_limited(self): self._prune(); return len(self._post_times)>=MAX_POSTS_PER_MINUTE
    async def post(self, session, payload):
        if self._rate_limited(): log.warning("[%s] rate limit", self.name); return False
        try:
            async with session.post(self.url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status in (200,204): self._post_times.append(time.monotonic()); return True
                elif resp.status==429: await asyncio.sleep((await resp.json()).get("retry_after",5)); return False
                else: log.error("[%s] HTTP %d", self.name, resp.status); return False
        except Exception as exc: log.error("[%s] error: %s", self.name, exc); return False

class DedupeCache:
    def __init__(self): self._cache={}
    def is_duplicate(self, key):
        now=time.monotonic(); last=self._cache.get(key)
        if last and (now-last)<DEDUP_WINDOW: return True
        self._cache[key]=now
        if len(self._cache)>2000:
            cutoff=now-DEDUP_WINDOW; self._cache={k:v for k,v in self._cache.items() if v>cutoff}
        return False

async def tail_journal(queue):
    proc = await asyncio.create_subprocess_exec("journalctl","-u","graywolf","-f","-n","0","--no-pager",stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL)
    log.info("Tailing graywolf journal...")
    while True:
        line = await proc.stdout.readline()
        if not line: await asyncio.sleep(1); continue
        decoded = line.decode("utf-8", errors="replace").strip()
        if 'msg="aprs packet"' in decoded or 'msg="message sent on rf"' in decoded:
            await queue.put(decoded)

async def poll_db(db_queue):
    last_id = 0
    try:
        conn = sqlite3.connect(f"file:{GRAYWOLF_DB}?mode=ro", uri=True)
        row = conn.execute("SELECT MAX(id) FROM messages WHERE direction IN ('in','out') AND is_ack=0 AND is_rej=0").fetchone()
        if row and row[0]: last_id = row[0]
        conn.close()
        log.info("DB poller starting after id=%d", last_id)
    except Exception as e: log.error("DB init error: %s", e)
    while True:
        await asyncio.sleep(DB_POLL_INTERVAL)
        try:
            conn = sqlite3.connect(f"file:{GRAYWOLF_DB}?mode=ro", uri=True)
            conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
            rows = conn.execute("SELECT * FROM messages WHERE direction IN ('in','out') AND is_ack=0 AND is_rej=0 AND id>? ORDER BY id ASC",(last_id,)).fetchall()
            conn.close()
            for row in rows: last_id=row[0]; await db_queue.put(row)
        except Exception as e: log.error("DB poll error: %s", e)

async def run_bridge():
    if not DISCORD_WEBHOOK_RF or not DISCORD_WEBHOOK_INTERNET: log.error("Webhooks not set"); sys.exit(1)
    poster_rf=WebhookPoster(DISCORD_WEBHOOK_RF,"aprs-rf-nj"); poster_is=WebhookPoster(DISCORD_WEBHOOK_INTERNET,"aprs-internet-nj")
    poster_rf_mc=WebhookPoster(DISCORD_WEBHOOK_RF_MESHCORE,"aprs-rf-nj-mc"); poster_is_mc=WebhookPoster(DISCORD_WEBHOOK_INTERNET_MESHCORE,"aprs-internet-nj-mc")
    dedupe=DedupeCache(); queue=asyncio.Queue(); db_queue=asyncio.Queue()
    log.info("CNJ Mesh APRS -> Discord bridge starting")
    asyncio.create_task(tail_journal(queue)); asyncio.create_task(poll_db(db_queue))
    async with aiohttp.ClientSession() as http_session:
        async def process_journal():
            while True:
                line = await queue.get()
                if 'msg="message sent on rf"' in line: continue
                m=LOG_RE.search(line)
                if not m: continue
                fields={"type":m.group(1),"source":m.group(2),"dest":m.group(3),"path":m.group(4),"lat":m.group(5),"lon":m.group(6),"comment":m.group(7)}
                if fields["type"]=="message":
                    tm=TEXT_RE.search(line); tom=TO_RE.search(line)
                    if tm and tm.group(1).strip(): fields["comment"]=tm.group(1).strip()
                    if tom: fields["dest"]=tom.group(1).strip()
                if fields["type"] not in ("message","third-party"): continue
                if fields["source"] in BLOCKLIST: continue
                if fields["dest"] in BLOCKLIST: continue
                if fields["type"] == "third-party":
                    _inner_s, _inner_m = extract_inner(fields.get("comment",""))
                    dedup_key = f"{_inner_s or fields['source']}:{_inner_m or fields.get('comment','')}"
                else:
                    dedup_key=f"{fields['source']}{fields.get('comment','')}"
                if dedupe.is_duplicate(dedup_key): continue
                channel_type=classify_path(fields["path"])
                payload=format_message(fields,channel_type)
                if payload is None: continue
                if channel_type=="rf":
                    if await poster_rf.post(http_session,payload): log.info("RF -> Discord: %s",fields["source"])
                    if DISCORD_WEBHOOK_RF_MESHCORE: await poster_rf_mc.post(http_session,payload)
                else:
                    if await poster_is.post(http_session,payload): log.info("IS -> Discord: %s",fields["source"])
                    if DISCORD_WEBHOOK_INTERNET_MESHCORE: await poster_is_mc.post(http_session,payload)

        async def process_db():
            while True:
                row = await db_queue.get()
                from_call=row[4]; message=row[6] or ""
                dedup_key=f"DB:{from_call}:{message}"
                if dedupe.is_duplicate(dedup_key): continue
                if from_call in BLOCKLIST: continue
                payload,channel_type=format_db_message(row)
                if payload is None: continue
                if channel_type=="rf":
                    if await poster_rf.post(http_session,payload): log.info("DB-RF -> Discord: %s",from_call)
                    if DISCORD_WEBHOOK_RF_MESHCORE: await poster_rf_mc.post(http_session,payload)
                else:
                    if await poster_is.post(http_session,payload): log.info("DB-IS -> Discord: %s",from_call)
                    if DISCORD_WEBHOOK_INTERNET_MESHCORE: await poster_is_mc.post(http_session,payload)

        asyncio.create_task(process_journal())
        asyncio.create_task(process_db())
        while True:
            await asyncio.sleep(3600)

def main():
    loop=asyncio.new_event_loop()
    def _shutdown(): log.info("Shutdown signal received.");[t.cancel() for t in asyncio.all_tasks(loop)]
    for sig in (signal.SIGTERM,signal.SIGINT): loop.add_signal_handler(sig,_shutdown)
    try: loop.run_until_complete(run_bridge())
    except asyncio.CancelledError: pass
    finally: loop.close(); log.info("Bridge stopped.")

if __name__=="__main__": main()
