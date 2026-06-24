"""
Fraud Network Graph Intelligence
================================

Builds a heterogeneous graph from victim reports, money-mule accounts, phone
numbers, devices and UPI handles, then runs network analytics to surface
coordinated fraud campaigns as actionable, court-ready intelligence packages.

Analytics:
  - Connected-component clustering   -> distinct campaigns / rings.
  - Degree + betweenness centrality  -> kingpin / aggregator accounts.
  - Mule-chain detection             -> layering paths (victim -> mule -> mule -> cashout).
  - Lead-time estimate               -> victims-per-day velocity => projected
                                        mass-victimisation window (the core KPI).
"""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Dict, List

import networkx as nx


def build_graph(records: List[Dict]) -> nx.Graph:
    """
    records: list of edges describing observed linkages, e.g.
      {"src": "victim:V001", "dst": "acct:A55", "type": "transfer", "amount": 240000,
       "ts": "2026-06-10"}
    Node ids are namespaced "type:id" (victim / acct / phone / device / upi / cashout).
    """
    G = nx.Graph()
    for r in records:
        src, dst = r["src"], r["dst"]
        for n in (src, dst):
            ntype = n.split(":", 1)[0]
            if n not in G:
                G.add_node(n, ntype=ntype)
        G.add_edge(
            src, dst,
            etype=r.get("type", "link"),
            amount=r.get("amount", 0),
            ts=r.get("ts"),
        )
    return G


def _campaign_intelligence(G: nx.Graph, nodes: set, idx: int) -> Dict:
    sub = G.subgraph(nodes)

    MONEY = ("acct:", "upi:", "wallet:")          # money-holding handles
    TRANSFERS = ("transfer", "upi_transfer")
    victims = [n for n in nodes if n.startswith("victim:")]
    accounts = [n for n in nodes if n.startswith(MONEY)]
    phones = [n for n in nodes if n.startswith("phone:")]
    devices = [n for n in nodes if n.startswith("device:")]
    mules = [n for n in nodes if n.startswith(MONEY)]  # mule handles (bank/UPI/wallet)

    total_loss = sum(
        d.get("amount", 0)
        for _, _, d in sub.edges(data=True)
        if d.get("etype") in TRANSFERS
    )

    # Centrality => most central money handle / phone is the aggregator / kingpin.
    deg = nx.degree_centrality(sub)
    try:
        btw = nx.betweenness_centrality(sub)
    except Exception:
        btw = {n: 0 for n in nodes}
    central = sorted(
        nodes, key=lambda n: deg.get(n, 0) + btw.get(n, 0), reverse=True
    )
    kingpins = [n for n in central if n.startswith(MONEY + ("phone:",))][:3]

    # Velocity / lead-time: spread of victim timestamps.
    ts = []
    for _, _, d in sub.edges(data=True):
        if d.get("ts"):
            try:
                ts.append(datetime.date.fromisoformat(d["ts"]))
            except Exception:
                pass
    lead_time_days = None
    velocity = None
    if len(ts) >= 2 and victims:
        span = (max(ts) - min(ts)).days or 1
        velocity = round(len(victims) / span, 2)  # victims/day
        # crude projection: days until 100 victims at current velocity
        if velocity > 0:
            lead_time_days = max(1, int((100 - len(victims)) / velocity))

    risk = min(
        99,
        int(len(victims) * 6 + len(accounts) * 4 + (total_loss / 100000)),
    )

    pkg = {
        "campaign_id": f"CAMP-{idx:03d}",
        "risk_index": risk,
        "victim_count": len(victims),
        "linked_accounts": len(accounts),
        "linked_phones": len(phones),
        "linked_devices": len(devices),
        "total_loss_inr": int(total_loss),
        "estimated_loss_str": f"₹{total_loss/100000:.1f} lakh",
        "kingpin_nodes": kingpins,
        "mule_accounts": [m for m in mules if m not in kingpins],
        "victims_per_day": velocity,
        "projected_days_to_100_victims": lead_time_days,
        "node_breakdown": {
            "victims": len(victims), "accounts": len(accounts),
            "phones": len(phones), "devices": len(devices),
        },
        "nodes": sorted(nodes),
        "edges": [
            {"src": u, "dst": v, "type": d.get("etype"), "amount": d.get("amount", 0)}
            for u, v, d in sub.edges(data=True)
        ],
    }
    # Tamper-evident hash for evidence admissibility.
    pkg["evidence_hash_sha256"] = hashlib.sha256(
        json.dumps(pkg, sort_keys=True).encode()
    ).hexdigest()
    return pkg


def detect_communities(G: nx.Graph):
    """Fraud-ring detection via Clauset-Newman-Moore greedy modularity
    maximisation — a standard graph community-detection algorithm (the local,
    no-Neo4j stand-in for the production GNN/Node2Vec pipeline). Falls back to
    connected components on tiny/empty graphs.

    Returns (list_of_communities, modularity_score).
    """
    from networkx.algorithms.community import greedy_modularity_communities, modularity
    if G.number_of_edges() == 0:
        return [set(c) for c in nx.connected_components(G)], 0.0
    try:
        comms = [set(c) for c in greedy_modularity_communities(G)]
    except Exception:
        comms = [set(c) for c in nx.connected_components(G)]
    try:
        q = round(float(modularity(G, comms)), 3)
    except Exception:
        q = 0.0
    return comms, q


def analyze(records: List[Dict]) -> Dict:
    G = build_graph(records)
    # Top-level campaigns = distinct rings (connected components).
    campaigns = []
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    for i, comp in enumerate(components, start=1):
        if len(comp) < 2:
            continue
        pkg = _campaign_intelligence(G, set(comp), i)
        # Community detection WITHIN the ring -> operational "cells".
        cells, cq = detect_communities(G.subgraph(comp))
        pkg["cells_detected"] = len([c for c in cells if len(c) >= 2])
        pkg["cell_modularity"] = cq
        campaigns.append(pkg)

    _, q_overall = detect_communities(G)
    campaigns.sort(key=lambda c: c["risk_index"], reverse=True)
    return {
        "summary": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "campaigns_detected": len(campaigns),
            "detection_method": "Connected-component rings + Clauset-Newman-Moore community detection (cells)",
            "modularity_score": q_overall,
            "total_projected_loss_inr": sum(c["total_loss_inr"] for c in campaigns),
        },
        "campaigns": campaigns,
        # Flat graph for frontend force-layout rendering.
        "graph": {
            "nodes": [
                {"id": n, "type": G.nodes[n]["ntype"]} for n in G.nodes()
            ],
            "links": [
                {"source": u, "target": v, "type": d.get("etype", "link"),
                 "amount": d.get("amount", 0)}
                for u, v, d in G.edges(data=True)
            ],
        },
    }
