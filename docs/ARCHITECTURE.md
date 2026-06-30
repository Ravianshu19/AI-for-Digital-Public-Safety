# Prahari — Architecture

![Architecture](architecture.png)

## Prototype (this repo)
A single FastAPI service (`backend/`) serves a vanilla JS dashboard (`frontend/`) and
five glass-box analytics modules. State is in-memory / flat-file so the whole thing
runs from `./run.sh` with no external services — ideal for a hackathon demo, explicitly
**not** the production topology.

| Concern | Prototype (now) | Why it's fine for a demo |
|---|---|---|
| Scam / counterfeit / shield | Stateless request→response | Pure functions, millisecond latency |
| Fraud graph | NetworkX, loaded per request | Tiny demo graph; instant |
| Audit ledger | Hash-chained JSONL (`backend/audit_log.jsonl`) | Tamper-evident, zero-dependency |
| Auth / limits | None | Local single-user demo |

## Production architecture (scale-out)
The prototype's known limits and how production closes each — this is the roadmap behind
the in-app "roadmap" notes.

### Ingestion & serving
- **API gateway** (Kong / AWS API Gateway / NGINX) in front of every endpoint for
  **rate limiting, OAuth2/mTLS auth, request quotas and WAF** — none of the public
  endpoints should be open at scale (the prototype already adds input-validation caps:
  5 000-char text limit, 10 MB image cap, MIME allow-list).
- **Stateless app tier** (the FastAPI service) behind a load balancer, scaled
  horizontally (k8s HPA); it holds no state, so it scales linearly.
- **Kafka** for streaming ingest of live TSP CDR, NPCI/UPI, and bank STR feeds →
  consumers feed the detectors and the graph incrementally (vs. the prototype's
  load-everything-per-request).

### Data & state
- **Audit ledger → append-only Postgres** (or a WORM store / QLDB-style ledger) with a
  per-row hash chain and a signing key, replacing the local JSONL. Gives distributed
  append guarantees, durability, and court-grade chain-of-custody at thousands of
  verdicts/minute.
- **Fraud graph → a graph database** (Neo4j / ArangoDB / TigerGraph) with **incremental
  upserts** instead of rebuilding in memory. Community detection / GNN inference run as
  scheduled or streaming jobs (Spark/GraphScope); the API reads precomputed campaigns.
- **Redis** for hot-path caching: scam signal/model results, counterfeit feature vectors,
  geospatial aggregates, and rate-limit counters.
- **Object store (S3)** for uploaded note images and evidence artifacts; **PostGIS** for
  geospatial queries.

### Models (replacing the glass-box v1)
- **Counterfeit:** fine-tuned **CNN/ViT** per security-feature ROI (the heuristic's
  measured real-world ceiling — 27% clearance on uncontrolled photos — is what this
  closes), served via TF-Serving/Triton + ONNX/TFLite for on-device bank-counter / POS.
- **Scam:** transformer classifier + **speech-AI** front-end for live synthetic-voice
  detection; keep the additive glass-box scorer as an explainability/fallback layer.
- **Fraud:** GraphSAGE/GNN node embeddings for mule/kingpin scoring.
- **Citizen Shield:** IndicTrans + LLM for full 12-language NLG (prototype localises the
  verdict scaffold in 5 today; the rest fall back to English).
- **MLOps:** model registry, drift monitoring, scheduled retraining (scammers adapt weekly).

### Security, privacy & compliance
- **DPDP Act 2023** alignment: PII tokenisation at ingest, encryption at rest/in transit,
  RBAC, consent + retention policy, data residency.
- Signed, append-only audit ledger + immutable evidence hashes for legal admissibility.
- Integrations gated through the agency stack: I4C / NCRP (1930), RBI, NPCI, DoT.

### Observability & reliability
- Prometheus/Grafana metrics, structured logs, tracing; SLOs on detector latency and
  false-positive rate; alerting on model drift.

## Honest current limitations (what a judge should know)
- Counterfeit detection is a **transparent heuristic (PIL/NumPy)**, not a trained CNN —
  strong on controlled captures, weak on uncontrolled mobile photos (documented in the
  README real-world stress test). The CNN/ViT is the top production item.
- Audit ledger and fraud graph are **single-node** here; production moves them to the
  databases above.
- No auth/rate-limit in the prototype beyond input-validation caps; production adds the
  API gateway.
