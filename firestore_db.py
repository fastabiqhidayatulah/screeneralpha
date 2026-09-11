"""
Firestore persistence: scan history + per-stock daily snapshots.

Credentials come from Streamlit secrets section [firebase] (service-account
JSON) or env var FIREBASE_CREDENTIALS (raw JSON). All functions fail silently
(bare except) to match the app's conventions -- scanning must never break
because storage is unavailable.
"""

import json
import math
import os
from datetime import datetime

_client = None


def _credentials():
    try:
        import streamlit as st
        secrets = st.secrets
        if "firebase" in secrets:
            return secrets["firebase"]
    except Exception:
        pass
    try:
        raw = os.environ.get("FIREBASE_CREDENTIALS")
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


def _db():
    global _client
    if _client is None:
        creds = _credentials()
        if not creds:
            return None
        import firebase_admin
        from firebase_admin import credentials
        from firebase_admin import firestore
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(dict(creds)))
        _client = firestore.client()
    return _client


def _jsonable(value):
    import numpy as np
    import pandas as pd
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (str, int, bool)):
        return value
    return str(value)


def save_scan(rows, kategori, threshold):
    """Save one scan run into the `scans` collection."""
    db = _db()
    if db is None:
        return False
    now = datetime.now()
    rows = list(rows or [])
    db.collection("scans").document().set({
        "category": kategori,
        "threshold": float(threshold or 0),
        "date": now.strftime("%Y-%m-%d"),
        "scanned_at": now.isoformat(),
        "count": len(rows),
        "results": [_jsonable(r) for r in rows],
    })
    return True


_SCORE_KEYS = ("skor_silent", "skor_scalping", "skor_bpjs", "skor_bsjp",
               "skor_swing", "skor_value", "skor_hidden_gem")


def save_stock_snapshots(df):
    """Save a daily snapshot per stock into `stock_history` (doc: {symbol}_{date})."""
    db = _db()
    if db is None or df is None or df.empty:
        return False
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    for _, r in df.iterrows():
        symbol = str(r.get("symbol", "")).strip()
        if not symbol:
            continue
        doc = {
            "symbol": symbol,
            "date": today,
            "scanned_at": now.isoformat(),
            "harga": float(r.get("harga", 0) or 0),
            "change": float(r.get("change", 0) or 0),
            "volume": float(r.get("volume", 0) or 0),
            "status_7d": str(r.get("status_7d", "")),
            "status_latest": str(r.get("status_latest", "")),
        }
        for key in _SCORE_KEYS:
            val = r.get(key)
            doc[key] = _jsonable(val) if val is not None else None
        db.collection("stock_history").document(f"{symbol}_{today}").set(doc)
    return True