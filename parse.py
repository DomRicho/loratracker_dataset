import csv
import math
import numpy as np
from dataclasses import dataclass

@dataclass
class Anchor:
    x: float
    y: float

@dataclass
class Obs:
    rssi: float
    snr: float
    timestamp: int
    ticks: int

def parse_csv(path):
    anchors = {}
    truth_xy = None
    by_packet = {}

    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if r and any(cell.strip() for cell in r)]

    # Find the positions header
    pos_hdr_i = None
    for i, r in enumerate(rows[:10]):  # only search first few lines
        if set(["gw0_x","gw0_y","an0_x","an0_y","an1_x","an1_y"]).issubset({c.strip().lower() for c in r}):
            pos_hdr_i = i
            break
    if pos_hdr_i is None:
        raise ValueError("Positions header not found (expected gw0_x,gw0_y,an0_x,an0_y,an1_x,an1_y,...)")

    pos_val_i = pos_hdr_i + 1
    pos_hdr = [c.strip().lower() for c in rows[pos_hdr_i]]
    pos_val = rows[pos_val_i]

    def get_val(name, default=None):
        try:
            j = pos_hdr.index(name)
            return float(pos_val[j])
        except Exception:
            return default

    anchors["GW0"] = Anchor(get_val("gw0_x", 0.0), get_val("gw0_y", 0.0))
    anchors["AN0"] = Anchor(get_val("an0_x", 0.0), get_val("an0_y", 0.0))
    anchors["AN1"] = Anchor(get_val("an1_x", 0.0), get_val("an1_y", 0.0))
    tx_x = get_val("en0_x", None)
    tx_y = get_val("en0_y", None)
    if tx_x is not None and tx_y is not None:
        truth_xy = (tx_x, tx_y)

    # Find data header
    data_hdr_i = None
    for i in range(pos_val_i + 1, min(pos_val_i + 10, len(rows))):
        r = [c.strip().lower() for c in rows[i]]
        if set(["node_id","packet_id","rssi","snr","timestamp","ticks"]).issubset(set(r)):
            data_hdr_i = i
            break
    if data_hdr_i is None:
        raise ValueError("Data header not found (expected node_id,packet_id,rssi,snr,timestamp,ticks,...)")

    hdr = [c.strip().lower() for c in rows[data_hdr_i]]
    idx = {name: hdr.index(name) for name in ["node_id","packet_id","rssi","snr","timestamp","ticks"]}

    for r in rows[data_hdr_i+1:]:
        if len(r) < len(hdr):
            continue
        node_id = r[idx["node_id"]].strip().upper()
        packet_id = r[idx["packet_id"]].strip()
        try:
            ob = Obs(
                rssi=float(r[idx["rssi"]]),
                snr=float(r[idx["snr"]]),
                timestamp=int(r[idx["timestamp"]]),
                ticks= int(r[idx["ticks"]]), 
            )
        except ValueError:
            continue
        by_packet.setdefault(packet_id, {})[node_id] = ob
    return anchors, truth_xy, by_packet

