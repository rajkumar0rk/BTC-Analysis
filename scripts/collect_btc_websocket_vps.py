#!/usr/bin/env python3
"""Read-only live BTC market microstructure recorder for a small VPS.

Delta India: ob_updates (full L2 snapshot/deltas with sequence and CRC32) + trades.
Binance Spot: top-20 partial book snapshots (~1s) + aggTrade (aggregate prints).
Raw exchange messages are timestamped and gzipped hourly, independently by venue.
No orders, private credentials, margin/hedging claims, or assumed maker fills.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import datetime as dt
import gzip
import json
import logging
from pathlib import Path
import shutil
import signal
import sys
import tempfile
import time
import zlib

DELTA_URL = "wss://public-socket.india.delta.exchange"
BINANCE_URL = ("wss://data-stream.binance.vision/stream?"
               "streams=btcusdt@depth20/btcusdt@aggTrade")
SUBSCRIBE_DELTA = {
    "type": "subscribe",
    "payload": {"channels": [
        {"name": "ob_updates", "symbols": ["BTCUSD"]},
        {"name": "trades", "symbols": ["BTCUSD"]},
    ]},
}

LOG = logging.getLogger("btc_ws")

def time_ns() -> int:
    return time.time_ns()

class InvalidBook(Exception):
    """Sequence gap, CRC mismatch, or impossible book: resubscribe required."""

class DeltaBook:
    """Delta ob_updates exact sequence & full-book CRC32 validation."""
    def __init__(self) -> None:
        self.asks: dict[str,str] = {}
        self.bids: dict[str,str] = {}
        self.seq: int | None = None

    @staticmethod
    def apply(levels: dict[str,str], updates) -> None:
        if not isinstance(updates, list):
            raise InvalidBook("Invalid updates array")
        for row in updates:
            if not isinstance(row,(list,tuple)) or len(row)!=2:
                raise InvalidBook("Invalid price-size level")
            price,size=str(row[0]),str(row[1])
            try:
                if float(price)<=0 or float(size)<0:
                    raise ValueError
            except ValueError:
                raise InvalidBook("Non-positive price or negative size")
            if float(size)==0.0:
                levels.pop(price,None)
            else:
                levels[price]=size

    def checksum(self) -> int:
        asks=sorted(self.asks.items(),key=lambda p:float(p[0]))[:10]
        bids=sorted(self.bids.items(),key=lambda p:-float(p[0]))[:10]
        enc=lambda rows: ",".join(f"{price}:{size}" for price,size in rows)
        return zlib.crc32((enc(asks)+"|"+enc(bids)).encode("utf8")) & 0xffffffff

    def update(self, message:dict) -> dict:
        if message.get("type")!="ob_updates":
            raise InvalidBook("Not a Delta L2 update")
        if message.get("sy")!="BTCUSD":
            raise InvalidBook("Wrong symbol")
        action=message.get("action")
        if action=="error":
            raise InvalidBook("Delta signaled snapshot error")
        if action not in ("snapshot","update"):
            raise InvalidBook("Unexpected Delta book action")
        try:seq=int(message["seq"])
        except (TypeError,ValueError,KeyError):
            raise InvalidBook("No numeric sequence")
        if action=="snapshot":
            self.asks={};self.bids={}
        elif self.seq is None or seq!=self.seq+1:
            raise InvalidBook(f"Order-book sequence gap: {self.seq} => {seq}")

        self.apply(self.asks,message.get("a"))
        self.apply(self.bids,message.get("b"))
        if not self.asks or not self.bids:
            raise InvalidBook("Empty book side")
        bid=max(float(k) for k in self.bids)
        ask=min(float(k) for k in self.asks)
        if bid>=ask:
            raise InvalidBook(f"Crossed Delta order book {bid}/{ask}")
        computed=self.checksum()
        try:expected=int(message["cs"])
        except (TypeError,ValueError,KeyError):
            raise InvalidBook("No checksum")
        if computed!=expected:
            raise InvalidBook(f"Delta CRC32 mismatch: expected {expected}, got {computed}")
        self.seq=seq
        return {"bid":bid,"ask":ask,"sequence":seq,"checksum_verified":True,
                "levels_bid":len(self.bids),"levels_ask":len(self.asks)}

class GzipJournal:
    """Single-event writes to hourly gzip chunks, bounded memory."""
    def __init__(self,path:Path, free_floor_mb:int=2048):
        self.root=path
        self.floor=free_floor_mb*1024*1024
        self.current:dict[str,tuple[str,gzip.GzipFile]]={}
        self.last_check=0.0
        self.last_flush=0.0
        self.counts=Counter()
        self.root.mkdir(parents=True,exist_ok=True)

    def safety_check(self,force=False):
        if force or time.monotonic()-self.last_check>=60:
            free=shutil.disk_usage(self.root).free
            if free<self.floor:
                raise RuntimeError(
                    f"Storage safety stop: free {free/1048576:.0f}MiB "
                    f"below minimum {self.floor/1048576:.0f}MiB. "
                    "Archive data and free space before restarting.")
            self.last_check=time.monotonic()

    def emit(self,venue:str,kind:str,payload:dict,extra:dict|None=None):
        now=time_ns()
        iso=dt.datetime.fromtimestamp(now/1e9,dt.timezone.utc)
        stamp=iso.strftime("%Y-%m-%d/%H")
        old=self.current.get(venue)
        if old is None or old[0]!=stamp:
            self.safety_check(force=True)
            if old: old[1].close()
            folder=self.root/venue/iso.strftime("%Y-%m-%d")
            folder.mkdir(parents=True,exist_ok=True)
            path=folder/(iso.strftime("%H")+".jsonl.gz")
            fp=gzip.open(path,"at",encoding="utf8",compresslevel=3)
            self.current[venue]=(stamp,fp)
            LOG.info("Writing %s -> %s",venue,path)
        record={"recv_ns":now,"venue":venue,"kind":kind,"message":payload}
        if extra:record["validation"]=extra
        fp=self.current[venue][1]
        fp.write(json.dumps(record,separators=(",",":"),ensure_ascii=False)+"\n")
        self.counts[(venue,kind)]+=1
        if time.monotonic()-self.last_flush>=5:
            self.flush()

    def flush(self):
        for _,fp in self.current.values():fp.flush()
        self.last_flush=time.monotonic()
        self.safety_check()

    def close(self):
        for _,fp in self.current.values():fp.close()
        self.current.clear()

async def relay_delta(journal:GzipJournal,stop:asyncio.Event):
    from websockets.asyncio.client import connect
    backoff=1
    while not stop.is_set():
        try:
            book=DeltaBook()
            async with connect(DELTA_URL,ping_interval=20,ping_timeout=20,
                               max_queue=128,max_size=8*1024*1024,
                               open_timeout=25,close_timeout=8) as ws:
                await ws.send(json.dumps(SUBSCRIBE_DELTA))
                LOG.info("Connected Delta India public WebSocket")
                backoff=1
                while not stop.is_set():
                    raw=await asyncio.wait_for(ws.recv(),timeout=65)
                    if not isinstance(raw,str):continue
                    try:message=json.loads(raw)
                    except json.JSONDecodeError:
                        journal.emit("delta","parse_error",{"size":len(raw)})
                        continue
                    if not isinstance(message,dict):continue
                    typ=message.get("type")
                    if typ=="ob_updates":
                        # Persist raw event BEFORE applying checks so invalid data is
                        # available for postmortem, but never trust a broken book.
                        journal.emit("delta","ob_updates_raw",message)
                        if message.get("action")=="error":
                            raise InvalidBook(str(message.get("msg","snapshot error")))
                        validation=book.update(message)
                        if validation["sequence"]%50==0:
                            journal.emit("delta","book_verified",{"seq":book.seq},validation)
                    elif typ=="trades":
                        journal.emit("delta","trades",message)
                    elif typ not in ("subscribed","pong","heartbeat"):
                        journal.emit("delta","control",message)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            LOG.warning("Delta disconnected/resync: %s",exc)
            journal.emit("delta","disconnect",{"error":str(exc)[:300],
                                                "event":"resubscribe_required"})
            if stop.is_set():break
            try:await asyncio.wait_for(stop.wait(),timeout=backoff)
            except asyncio.TimeoutError:pass
            backoff=min(backoff*2,60)

async def relay_binance(journal:GzipJournal,stop:asyncio.Event):
    from websockets.asyncio.client import connect
    backoff=1
    while not stop.is_set():
        try:
            async with connect(BINANCE_URL,ping_interval=20,ping_timeout=20,
                               max_queue=128,max_size=4*1024*1024,
                               open_timeout=25,close_timeout=8) as ws:
                LOG.info("Connected Binance Spot public WebSocket")
                backoff=1
                while not stop.is_set():
                    raw=await asyncio.wait_for(ws.recv(),timeout=65)
                    if not isinstance(raw,str):continue
                    try:packet=json.loads(raw)
                    except json.JSONDecodeError:
                        journal.emit("binance_spot","parse_error",{"size":len(raw)})
                        continue
                    if not isinstance(packet,dict):continue
                    stream=packet.get("stream","")
                    payload=packet.get("data")
                    if not isinstance(payload,dict):
                        journal.emit("binance_spot","control",packet)
                        continue
                    if stream=="btcusdt@aggTrade":
                        journal.emit("binance_spot","aggTrade",payload)
                    elif stream.startswith("btcusdt@depth20"):
                        # These are independently published TOP-20 snapshots,
                        # NOT incremental L2 diffs; no continuity claim.
                        if ("asks" not in payload or "bids" not in payload
                            or "lastUpdateId" not in payload):
                            journal.emit("binance_spot","malformed_depth",payload)
                        else:
                            journal.emit("binance_spot","depth20_snapshot",payload,
                                         {"book_type":"partial_top20_snapshot",
                                          "sequence_continuity_verified":False})
                    else:
                        journal.emit("binance_spot","other",packet)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            LOG.warning("Binance Spot disconnected: %s",exc)
            journal.emit("binance_spot","disconnect",{"error":str(exc)[:300]})
            if stop.is_set():break
            try:await asyncio.wait_for(stop.wait(),timeout=backoff)
            except asyncio.TimeoutError:pass
            backoff=min(backoff*2,60)

def self_test():
    import unittest
    class Tests(unittest.TestCase):
        def test_book_snapshot_update_gap_and_checksum(self):
            b=DeltaBook()
            snapshot={"type":"ob_updates","sy":"BTCUSD","action":"snapshot",
                      "seq":50,"a":[["102.0","3"],["103.0","6"]],
                      "b":[["101.0","4"],["100.0","7"]]}
            temp=DeltaBook()
            temp.apply(temp.asks,snapshot["a"])
            temp.apply(temp.bids,snapshot["b"])
            snapshot["cs"]=temp.checksum()
            info=b.update(snapshot)
            self.assertEqual(info["bid"],101)
            self.assertEqual(info["ask"],102)
            change={"type":"ob_updates","sy":"BTCUSD","action":"update",
                    "seq":51,"a":[["102.0","0"],["103.0","9"]],
                    "b":[["101.0","8"]]}
            temp.apply(temp.asks,change["a"]);temp.apply(temp.bids,change["b"])
            change["cs"]=temp.checksum()
            self.assertEqual(b.update(change)["ask"],103)
            self.assertEqual(b.seq,51)
            wrong=dict(change,seq=53)
            with self.assertRaises(InvalidBook):b.update(wrong)
            bad=dict(change,seq=52,cs=0)
            with self.assertRaises(InvalidBook):b.update(bad)

        def test_compressed_writer(self):
            with tempfile.TemporaryDirectory() as root:
                path=Path(root)/"data"
                j=GzipJournal(path,free_floor_mb=0)
                j.emit("delta","trades",{"p":"101","s":3})
                j.emit("binance_spot","aggTrade",{"p":"102","q":"0.1"})
                j.close()
                for name in ("delta","binance_spot"):
                    files=list((path/name).rglob("*.gz"))
                    self.assertEqual(len(files),1)
                    with gzip.open(files[0],"rt",encoding="utf8") as fp:
                        event=json.loads(fp.readline())
                    self.assertEqual(event["venue"],name)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():sys.exit(1)
    print("SELF_TEST_PASSED")

async def main_live(args):
    stop=asyncio.Event()
    def trigger_stop():
        LOG.info("Shutdown requested")
        stop.set()
    loop=asyncio.get_running_loop()
    for name in (signal.SIGINT,signal.SIGTERM):
        try:loop.add_signal_handler(name,trigger_stop)
        except NotImplementedError:pass
    journal=GzipJournal(args.data_dir,args.free_floor_mb)
    journal.safety_check(force=True)
    tasks=[
        asyncio.create_task(relay_delta(journal,stop),name="delta"),
        asyncio.create_task(relay_binance(journal,stop),name="binance_spot"),
    ]
    try:
        if args.duration:
            try:await asyncio.wait_for(stop.wait(),timeout=args.duration)
            except asyncio.TimeoutError:pass
        else:
            await stop.wait()
    finally:
        stop.set()
        for t in tasks:t.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        journal.close()
        LOG.info("Collection completed: %s",dict(journal.counts))
        if args.require_events and not (
            journal.counts.get(("delta","ob_updates_raw"),0)>0
            and journal.counts.get(("binance_spot","depth20_snapshot"),0)>0
        ):
            raise RuntimeError("Live smoke test did not receive order book updates from both venues")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir",type=Path,default=Path("/var/lib/btc-market-data"))
    p.add_argument("--duration",type=float,default=0,
                   help="Exit after N seconds, for VPS smoke testing")
    p.add_argument("--free-floor-mb",type=int,default=2048,
                   help="Stop instead of filling disk; default require >=2 GiB free")
    p.add_argument("--require-events",action="store_true",
                   help="Fail short test if both venues do not deliver book updates")
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--log-level",default="INFO",choices=("DEBUG","INFO","WARNING"))
    args=p.parse_args()
    logging.basicConfig(level=getattr(logging,args.log_level),
                        format="%(asctime)s %(levelname)s %(message)s")
    if args.self_test:
        self_test()
    else:
        asyncio.run(main_live(args))

if __name__=="__main__":
    main()
