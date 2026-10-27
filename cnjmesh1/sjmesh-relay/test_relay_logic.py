#!/usr/bin/env python3
"""Offline checks for relay.py routing and loop safety. No network needed.
Run: OUTBOUND_ENABLED=1 python3 test_relay_logic.py   (needs paho-mqtt installed)
"""
import os
os.environ["OUTBOUND_ENABLED"] = "1"
import relay


class Msg:
    def __init__(self, topic, payload=b"x", qos=0, retain=False):
        self.topic, self.payload, self.qos, self.retain = topic, payload, qos, retain


class FakeBroker:
    """A tiny in-memory broker: clients subscribe by filter and receive their own publishes too."""
    def __init__(self, name):
        self.name, self.subs, self.log = name, [], []

    def deliver(self, msg):
        for flt, cb in self.subs:
            if relay_match(flt, msg.topic):
                cb(None, None, msg)


def relay_match(flt, topic):
    f, t = flt.split("/"), topic.split("/")
    for i, part in enumerate(f):
        if part == "#":
            return True
        if i >= len(t):
            return False
        if part != "+" and part != t[i]:
            return False
    return len(f) == len(t)


class FakeClient:
    def __init__(self, broker):
        self.broker, self.published = broker, []

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, retain))
        self.broker.deliver(Msg(topic, payload, qos, retain))


def run():
    sj, loc = FakeBroker("sjmesh"), FakeBroker("local")
    remote, local = FakeClient(sj), FakeClient(loc)
    r = relay.Relay(local, remote)
    sj.subs.append(("msh/US/2/e/CentralNJ/#", r.on_remote_message))   # our inbound subscription
    loc.subs.append(("msh/US/2/e/CentralNJ/+", r.on_local_message))   # our outbound subscription

    # 1. Our gateway uploads locally -> goes out once, echoes back from SJMesh, stops.
    loc.deliver(Msg("msh/US/2/e/CentralNJ/!9ea3e8d4", b"hello"))
    assert r.outbound_count == 1, r.outbound_count
    assert r.echo_count == 1, r.echo_count
    assert local.published == [], "echo must never be republished locally"
    assert remote.published == [("msh/US/2/e/CentralNJ/!9ea3e8d4", False)]

    # 2. An SJMesh gateway's packet comes in -> goes local, is NOT sent back out.
    sj.deliver(Msg("msh/US/2/e/CentralNJ/!a6965300", b"cape may"))
    assert r.relayed_count == 1 and r.outbound_count == 1
    assert local.published == [("msh/US/2/e/CentralNJ/!a6965300", False)]

    # 3. Blocked flood node: dropped inbound, and never forwarded outbound.
    sj.deliver(Msg("msh/US/2/e/CentralNJ/!699a9390", b"flood"))
    assert r.blocked_count == 1
    assert not relay.should_forward_outbound("msh/US/2/e/CentralNJ/!699a9390")

    # 4. Topics outside CentralNJ or from other gateways are never forwarded.
    assert not relay.should_forward_outbound("msh/US/2/e/LongFast/!9ea3e8d4")
    assert not relay.should_forward_outbound("msh/US/2/json/CentralNJ/!9ea3e8d4")
    assert not relay.should_forward_outbound("msh/US/2/e/CentralNJ/!deadbeef")
    assert relay.should_forward_outbound("msh/US/NJ/2/e/CentralNJ/!69841fe0")

    # 5. Rate cap: only the cap gets out, extras are counted as dropped.
    t = [0.0]
    r2 = relay.Relay(local, remote, limiter=relay.RateLimiter(3, clock=lambda: t[0]))
    before = r2.outbound_count
    for _ in range(10):
        r2.on_local_message(None, None, Msg("msh/US/2/e/CentralNJ/!69841fe0"))
    assert r2.outbound_count - before == 3 and r2.outbound_dropped == 7
    t[0] = 61.0
    r2.on_local_message(None, None, Msg("msh/US/2/e/CentralNJ/!69841fe0"))
    assert r2.outbound_count - before == 4

    # 6. Long chatter: 200 packets from our gateways produce exactly 200 outbound, no storm.
    sj2, loc2 = FakeBroker("sj2"), FakeBroker("loc2")
    rem2, lcl2 = FakeClient(sj2), FakeClient(loc2)
    r3 = relay.Relay(lcl2, rem2, limiter=relay.RateLimiter(10**6))
    sj2.subs.append(("msh/US/2/e/CentralNJ/#", r3.on_remote_message))
    loc2.subs.append(("msh/US/2/e/CentralNJ/+", r3.on_local_message))
    for i in range(200):
        loc2.deliver(Msg("msh/US/2/e/CentralNJ/!0aca423c", str(i).encode()))
    assert r3.outbound_count == 200 and r3.echo_count == 200 and lcl2.published == []
    print("all relay logic checks passed")


if __name__ == "__main__":
    run()
