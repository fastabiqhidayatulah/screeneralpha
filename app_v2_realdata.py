"""
AI SCREENER BEI — VERSI FINAL
Dashboard + Berita + AI Control (7 Kategori) + Optimasi
"""

from concurrent.futures import ThreadPoolExecutor
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import os
import sys
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

sys.path.insert(0, os.path.dirname(__file__))
from stockbit_client import StockbitClient

# =========================================================================
# KONFIGURASI HALAMAN
# =========================================================================

st.set_page_config(
    page_title="🤖 AI Screener Saham BEI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================================
# CSS
# =========================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&family=Orbitron:wght@400;700&display=swap');
.stApp { background: #0a0f1a;
    background-image: radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.05) 0%, transparent 40%),
                      radial-gradient(circle at 80% 80%, rgba(129, 140, 248, 0.05) 0%, transparent 40%); }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:0.5;transform:scale(0.95);} }
@keyframes glow { 0%,100%{box-shadow:0 0 20px rgba(56,189,248,0.2);} 50%{box-shadow:0 0 50px rgba(56,189,248,0.6);} }
@keyframes float { 0%,100%{transform:translateY(0px);} 50%{transform:translateY(-10px);} }
@keyframes rotateGlow { 0%{transform:rotate(0deg);} 100%{transform:rotate(360deg);} }
.ai-avatar { width:80px; height:80px; border-radius:50%;
    background: linear-gradient(135deg,#38bdf8,#818cf8);
    display:flex; align-items:center; justify-content:center; font-size:2.8rem;
    animation: pulse 2s ease-in-out infinite, float 3s ease-in-out infinite;
    box-shadow: 0 0 40px rgba(56,189,248,0.3); margin:0 auto 15px auto; position:relative; }
.ai-avatar::after { content:''; position:absolute; inset:-4px; border-radius:50%;
    background: conic-gradient(from 0deg, transparent, #38bdf8, transparent, #818cf8, transparent);
    animation: rotateGlow 3s linear infinite; z-index:-1; }
.ai-status { background:rgba(30,41,59,0.8); backdrop-filter:blur(10px);
    border:1px solid rgba(56,189,248,0.2); border-radius:12px; padding:12px 20px;
    margin:10px 0; display:flex; align-items:center; gap:15px;
    animation: glow 3s ease-in-out infinite; flex-wrap:wrap; }
.ai-dot { width:12px; height:12px; border-radius:50%; background:#22c55e;
    animation:pulse 1s ease-in-out infinite; display:inline-block; }
.ai-dot.scanning { background:#f59e0b; animation:pulse 0.5s ease-in-out infinite; }
.deep-card { background: rgba(22, 30, 46, 0.7); backdrop-filter: blur(16px);
    border: 1px solid rgba(56, 189, 248, 0.15); border-left: 4px solid #38bdf8;
    border-radius: 12px; padding: 20px; margin-bottom: 16px; transition: all 0.3s ease; }
.deep-card:hover { border-color: rgba(56, 189, 248, 0.3);
    box-shadow: 0 10px 20px -5px rgba(56, 189, 248, 0.2); transform: translateY(-3px); }
.metric-strip { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:10px; }
.metric-item { background: rgba(22, 30, 46, 0.6); backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.1); border-radius: 10px;
    padding: 12px 18px; min-width: 150px; transition: all 0.3s ease; }
.metric-item:hover { border-color: rgba(56, 189, 248, 0.3); transform: translateY(-2px); }
.metric-item .val { font-size:1.2rem; font-weight:700; color:#e2e8f0; }
.metric-item .lbl { font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1.5px; }
.stSidebar { background-color:#0f172a !important; border-right:1px solid rgba(56,189,248,0.1) !important; }
.stSidebar .stButton button { background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    color: white !important; border: none !important; border-radius: 8px !important;
    padding: 10px 16px !important; font-weight: 600 !important; transition: all 0.3s ease; }
.stSidebar .stButton button:hover { transform: scale(1.02); box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4); }
.disclaimer { background:rgba(12,26,46,0.8); border:1px dashed rgba(71,85,105,0.5);
    padding:10px 14px; border-radius:8px; color:#94a3b8; font-size:0.75rem; margin-top:10px; }
.news-item { padding:10px 12px; margin:6px 0; background:rgba(30,41,59,0.4);
    border-radius:8px; border-left:3px solid #38bdf8; }
.news-title { color:#93c5fd; font-weight:600; font-size:0.9rem; text-decoration:none; display:block; margin-bottom:4px; }
.news-title:hover { color:#38bdf8; text-decoration:underline; }
.news-meta { color:#64748b; font-size:0.72rem; margin-top:4px; display:flex; gap:10px; flex-wrap:wrap; }
.news-meta .date { color:#f59e0b; }
.news-meta .source { color:#22c55e; font-style:italic; }
.sector-impact { background:rgba(56,189,248,0.08); padding:8px 12px; border-radius:6px; margin:4px 0; font-size:0.78rem; border-left:2px solid #38bdf8; }
.screener-table { width: 100%; border-collapse: collapse; background: rgba(22, 30, 46, 0.5); border-radius: 12px; overflow: hidden; margin-top: 15px; }
.screener-table th { background: linear-gradient(135deg, #1e293b, #0f172a); color: #38bdf8; padding: 12px 8px; text-align: left; font-family: 'Orbitron', monospace; font-size: 0.7rem; text-transform: uppercase; border-bottom: 2px solid #38bdf8; }
.screener-table td { padding: 10px 8px; color: #e2e8f0; border-bottom: 1px solid rgba(56, 189, 248, 0.1); font-size: 0.82rem; }
.screener-table tr:hover { background: rgba(56, 189, 248, 0.08); }
.badge-gorengan { background: #ef4444; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.65rem; font-weight: 600; }
.badge-murah { background: #f59e0b; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.65rem; font-weight: 600; }
.badge-midcap { background: #3b82f6; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.65rem; font-weight: 600; }
.badge-bigcap { background: #22c55e; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.65rem; font-weight: 600; }
.kategori-header { background: linear-gradient(135deg, rgba(56,189,248,0.1), rgba(129,140,248,0.1));
    border-left: 4px solid #38bdf8; border-radius: 8px; padding: 15px 20px; margin: 20px 0 10px 0; }
.kategori-header h2 { margin: 0; font-size: 1.3rem; }
.kategori-header p { margin: 5px 0 0 0; color: #94a3b8; font-size: 0.82rem; }
.accel-badge { background: linear-gradient(135deg, #facc15, #f59e0b); color: #0a0f1a; padding: 3px 8px; border-radius: 10px; font-size: 0.65rem; font-weight: 700; }
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#1e293b; }
::-webkit-scrollbar-thumb { background:#38bdf8; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# AI STATE + HEADER
# =========================================================================

if "ai_status" not in st.session_state:
    st.session_state.ai_status = "🟢 Online"
    st.session_state.ai_message = "Siap memindai akumulasi."

def ai_speak(message, status="🟢 Online"):
    st.session_state.ai_message = message
    st.session_state.ai_status = status

current_time = datetime.now().strftime("%H:%M:%S")
current_date = datetime.now().strftime("%d %b %Y")

col1, col2, col3 = st.columns([1, 2.5, 1])
with col1:
    st.markdown('<div class="ai-avatar">🤖</div>', unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div style="text-align: center;">
        <h1 style="font-family: 'Orbitron', monospace; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2rem; margin-bottom: 5px;">
            AI SCREENER BEI
        </h1>
        <div style="font-size: 0.7rem; color: #64748b; font-family: 'Orbitron', monospace; letter-spacing: 2px; margin-bottom: 8px;">
            • REAL-TIME MARKET INTELLIGENCE •
        </div>
        <div class="ai-status">
            <span class="ai-dot {'scanning' if 'Scanning' in st.session_state.ai_status else ''}"></span>
            <span style="color:#94a3b8;font-size:0.75rem;">STATUS:</span>
            <span style="color:#f8fafc;font-weight:600;font-size:0.8rem;">{st.session_state.ai_status}</span>
            <span style="color:#334155;">|</span>
            <span style="color:#f59e0b;font-size:0.75rem;">🕐 {current_time} WIB</span>
            <span style="color:#334155;">|</span>
            <span style="color:#94a3b8;font-size:0.75rem;">📅 {current_date}</span>
        </div>
        <div style="margin-top:6px;">
            <span style="color:#38bdf8;font-size:0.8rem;">{st.session_state.ai_message}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown('<div style="text-align:right;padding-top:20px;"><span style="color:#334155;font-size:0.6rem;">v10.0 • CACHED</span></div>', unsafe_allow_html=True)

st.markdown("---")

# =========================================================================
# DASHBOARD GLOBAL
# =========================================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_index_quotes():
    out = {}
    tickers = {
        "^JKSE": "IHSG", "IDR=X": "USD/IDR",
        "^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones",
        "^KS11": "KOSPI", "^HSI": "Hang Seng", "^N225": "Nikkei",
        "GC=F": "XAU/USD", "CL=F": "OIL/USD"
    }
    for tk, name in tickers.items():
        try:
            time.sleep(0.3)
            data = yf.download(tk, period="5d", interval="1d", progress=False, auto_adjust=True)
            if data.empty: continue
            if isinstance(data.columns, pd.MultiIndex):
                close_series = data[("Close", tk)].dropna()
            else:
                close_series = data["Close"].dropna()
            if len(close_series) == 0: continue
            last = float(close_series.iloc[-1])
            if len(close_series) >= 2:
                prev = float(close_series.iloc[-2])
                chg = (last - prev) / prev * 100 if prev != 0 else 0
            else:
                chg = 0
            out[name] = {"last": last, "chg": chg}
        except: pass
    for name in ["IHSG","USD/IDR","S&P 500","Nasdaq","Dow Jones","KOSPI","Hang Seng","Nikkei","XAU/USD","OIL/USD"]:
        if name not in out:
            out[name] = {"last": 0, "chg": 0}
    return out

def render_dashboard():
    quotes = get_index_quotes()
    st.markdown("### 🌐 GLOBAL MARKET DASHBOARD")
    for label, names in [
        ("🇮🇩 Indonesia", ["IHSG"]),
        ("💱 Forex", ["USD/IDR"]),
        ("🇺🇸 Bursa US", ["S&P 500", "Nasdaq", "Dow Jones"]),
        ("🌏 Bursa Asia", ["Nikkei", "Hang Seng", "KOSPI"]),
        ("🛢️ Komoditas", ["XAU/USD", "OIL/USD"]),
    ]:
        st.markdown(f"**{label}**")
        strip = '<div class="metric-strip">'
        for name in names:
            d = quotes.get(name, {})
            if d and d.get("last", 0) != 0:
                last, chg = d["last"], d["chg"]
                color = "#22c55e" if chg >= 0 else "#ef4444"
                prefix = "$" if name in ["XAU/USD", "OIL/USD"] else ""
                strip += f'<div class="metric-item"><div class="lbl">{name}</div><div class="val" style="color:{color}">{prefix}{last:,.2f} ({chg:+.2f}%)</div></div>'
            else:
                strip += f'<div class="metric-item"><div class="lbl">{name}</div><div class="val">N/A</div></div>'
        strip += "</div>"
        st.markdown(strip, unsafe_allow_html=True)

# =========================================================================
# BERITA
# =========================================================================

CREDIBLE_SOURCES = ["idx.co.id", "bloomberg.com", "kontan.co.id", "antaranews.com",
                    "reuters.com", "cnbcindonesia.com", "bisnis.com", "investor.id"]

POS_WORDS = ["tumbuh","naik","menguat","melonjak","surplus","ekspansi","positif","optimis","laba","profit","dividen"]
NEG_WORDS = ["resesi","perang","sanksi","konflik","tarif","jatuh","melemah","krisis","phk","rugi"]

NEWS_FEEDS = {
    "🇮🇩 Pasar Modal Indonesia": "IHSG OR bursa saham Indonesia",
    "🌐 Aksi Korporasi": "dividen OR stock split OR right issue",
    "🌍 Global & Komoditas": "harga minyak OR harga emas OR The Fed",
    "⚔️ Geopolitik": "geopolitik OR perang OR konflik OR sanksi",
}

SECTOR_IMPACT = {
    "minyak": {"positif": ["Energi"], "negatif": ["Transportasi"]},
    "perang": {"positif": ["Pertahanan"], "negatif": ["Penerbangan", "Pariwisata"]},
    "suku bunga naik": {"positif": ["Perbankan"], "negatif": ["Properti"]},
    "laba": {"positif": ["Sektor Emiten"], "negatif": []},
    "rugi": {"positif": [], "negatif": ["Sektor Emiten"]},
}

@st.cache_data(ttl=900, show_spinner=False)
def fetch_credible_news(query, max_items=5):
    try:
        q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id&num=30"
        r = requests.get(url, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        root = ET.fromstring(r.content)
        items = []
        for it in root.iter("item"):
            src = it.find("source")
            if src is None or not src.text: continue
            if not any(c in src.text.lower() for c in CREDIBLE_SOURCES): continue
            pub_raw = (it.findtext("pubDate") or "").strip()
            pub_formatted = pub_raw[:30]
            try:
                pub_dt = datetime.strptime(pub_raw, "%a, %d %b %Y %H:%M:%S %Z")
                pub_formatted = pub_dt.strftime("%d %b %Y, %H:%M WIB")
            except: pass
            title = (it.findtext("title") or "").split(" - ")[0].strip()
            items.append({"title": title, "link": it.findtext("link") or "",
                          "pub": pub_formatted, "source": src.text.strip()})
            if len(items) >= max_items: break
        return items
    except: return []

def _sent_score(items):
    s = 0
    for it in items:
        t = (it.get("title") or "").lower()
        s += sum(1 for w in POS_WORDS if w in t)
        s -= sum(1 for w in NEG_WORDS if w in t)
    return s

def impact_label(s):
    if s >= 4: return "🟢🟢 Positif kuat"
    if s >= 2: return "🟢 Positif"
    if s <= -4: return "🔴🔴 Negatif kuat"
    if s <= -2: return "🔴 Negatif"
    return "⚪ Netral"

def analyze_sector_impact(news_items):
    impacts = []
    for it in news_items:
        title = (it.get("title") or "").lower()
        for keyword, sectors in SECTOR_IMPACT.items():
            if keyword in title:
                if sectors["positif"]:
                    impacts.append(f"📈 {keyword.title()} → {', '.join(sectors['positif'])}")
                if sectors["negatif"]:
                    impacts.append(f"📉 {keyword.title()} → {', '.join(sectors['negatif'])}")
    return impacts[:5]

def render_news():
    with st.expander("📰 Berita Kredibel & Analisis", expanded=False):
        total = 0
        for lbl, q in NEWS_FEEDS.items():
            items = fetch_credible_news(q, max_items=5)
            s = _sent_score(items)
            total += s
            st.markdown(f"### {lbl} — {impact_label(s)}")
            if items:
                for it in items:
                    st.markdown(f"""<div class="news-item">
                        <a href="{it['link']}" target="_blank" class="news-title">{it['title']}</a>
                        <div class="news-meta"><span class="date">📅 {it['pub']}</span><span class="source">🏢 {it['source']}</span></div>
                    </div>""", unsafe_allow_html=True)
                impacts = analyze_sector_impact(items)
                if impacts:
                    for imp in impacts:
                        st.markdown(f'<div class="sector-impact">{imp}</div>', unsafe_allow_html=True)
            st.markdown("---")
        bg = "#14532d" if total >= 2 else ("#7f1d1d" if total <= -2 else "#1e293b")
        st.markdown(f'<div style="background:{bg};padding:12px;border-radius:8px;text-align:center;"><b>DAMPAK KE IHSG:</b> skor {total:+.1f}</div>', unsafe_allow_html=True)

# =========================================================================
# FUNGSI SCREENER
# =========================================================================

def get_kategori_badge(harga):
    if harga < 100: return '<span class="badge-gorengan">🪙 GORENGAN</span>'
    elif harga < 500: return '<span class="badge-murah">💵 MURAH</span>'
    elif harga < 2000: return '<span class="badge-midcap">💎 MID</span>'
    return '<span class="badge-bigcap">🏆 BIG</span>'

def get_yahoo_intraday_batch(symbols, interval="15m", period="10d"):
    out = {}
    if not symbols: return out
    try:
        tickers = [f"{s}.JK" for s in symbols]
        df = yf.download(tickers, period=period, interval=interval, group_by="ticker", progress=False, auto_adjust=True)
        if df.empty: return out
        for symbol in symbols:
            ticker = f"{symbol}.JK"
            try:
                if isinstance(df.columns, pd.MultiIndex):
                    if ticker not in df.columns.get_level_values(0): continue
                    sub = df[ticker].dropna()
                else:
                    sub = df.dropna()
                if len(sub) < 20: continue
                sub["TP"] = (sub["High"] + sub["Low"] + sub["Close"]) / 3
                sub["VWAP"] = (sub["TP"] * sub["Volume"]).cumsum() / sub["Volume"].cumsum()
                sub["OBV"] = (np.sign(sub["Close"].diff()) * sub["Volume"]).fillna(0).cumsum()
                recent = sub.tail(20)
                high_20 = recent["High"].max(); low_20 = recent["Low"].min()
                range_pct = ((high_20 - low_20) / low_20 * 100) if low_20 > 0 else 100
                vol_trend_up = False
                if len(sub) >= 3:
                    v1 = sub["Volume"].iloc[-1]; v2 = sub["Volume"].iloc[-2]; v3 = sub["Volume"].iloc[-3]
                    vol_trend_up = v1 > v2 > v3
                obv_20 = sub["OBV"].tail(20)
                obv_trend_up = obv_20.iloc[-1] > obv_20.iloc[0] if len(obv_20) > 0 else False
                last = sub.iloc[-1]
                close = float(last["Close"]); vwap = float(last["VWAP"])
                out[symbol] = {"close": close, "vwap": vwap, "close_above_vwap": close > vwap,
                               "range_pct": range_pct, "vol_trend_up": vol_trend_up, "obv_trend_up": obv_trend_up}
            except: continue
    except: pass
    return out

def deteksi_skenario(status_7d, status_latest):
    s7 = str(status_7d).lower(); sl = str(status_latest).lower()
    if ("neutral" in s7 or "dist" in s7) and ("big acc" in sl or "acc" in sl):
        if "big acc" in sl: return ("akumulasi_baru", 25, "🟢🟢 BARU MULAI")
        else: return ("akumulasi_baru", 20, "🟢 BARU MULAI")
    if "acc" in s7 and "big acc" in sl: return ("akselerasi", 25, "🟢🟢 AKSELERASI")
    if "dist" in s7 and "acc" in sl: return ("reversal", 22, "🟢 REVERSAL")
    if "big acc" in s7 and "big acc" in sl: return ("konsisten_kuat", 15, "🟢 KONSISTEN")
    if "acc" in s7 and "acc" in sl: return ("konsisten", 10, "🟢 KONSISTEN")
    if "big acc" in s7 and "dist" in sl: return ("sudah_telat", -10, "🔴 SUDAH TELAT")
    if "dist" in sl: return ("distribusi", -5, "🔴 DISTRIBUSI")
    return ("netral", 0, "⚪ NETRAL")

def skor_silent_accumulation(row):
    s = 0
    sl = str(row.get("status_latest", "")); s7 = str(row.get("status_7d", ""))
    if "Big Acc" in sl: s += 30
    elif "Acc" in sl: s += 22
    elif "Big Acc" in s7: s += 18
    elif "Acc" in s7: s += 12
    chg = row.get("change", 0) or 0
    if chg <= -7: s += 20
    elif chg <= -5: s += 16
    elif chg <= -3: s += 12
    elif chg <= 0: s += 8
    top_acc = row.get("top_acc_lots", 0) or 0; top_dist = row.get("top_dist_lots", 0) or 0
    if top_dist > 0:
        ratio = abs(top_acc) / abs(top_dist)
        if ratio > 3: s += 20
        elif ratio > 2: s += 15
        elif ratio > 1.5: s += 10
    vol = row.get("volume", 0) or 0
    if vol > 5000000: s += 15
    elif vol > 2000000: s += 11
    elif vol > 1000000: s += 7
    intraday = row.get("intraday_data")
    if intraday and intraday.get("obv_trend_up"): s += 15
    elif intraday and intraday.get("vol_trend_up"): s += 8
    return round(max(0, min(100, s)))

def skor_scalping_markup(row):
    s = 0
    intraday = row.get("intraday_data")
    if intraday and intraday.get("range_pct", 100) < 5: s += 10
    if intraday and intraday.get("obv_trend_up"): s += 10
    if intraday and intraday.get("vol_trend_up"): s += 10
    _, bobot, _ = deteksi_skenario(row.get("status_7d", ""), row.get("status_latest", ""))
    s += bobot
    top_acc = row.get("top_acc_lots", 0) or 0; top_dist = row.get("top_dist_lots", 0) or 0
    if top_dist > 0:
        ratio = abs(top_acc) / abs(top_dist)
        if ratio > 3: s += 15
        elif ratio > 2: s += 10
        elif ratio > 1.5: s += 6
    rsi = row.get("rsi", 50) or 50
    if 50 <= rsi <= 60: s += 10
    elif 45 <= rsi <= 65: s += 6
    macd = row.get("macd", 0) or 0; macd_sig = row.get("macd_signal", 0) or 0
    if macd > macd_sig: s += 10
    if intraday and intraday.get("close_above_vwap"): s += 10
    return round(max(0, min(100, s)))

def skor_bpjs(row):
    s = 0
    _, bobot, _ = deteksi_skenario(row.get("status_7d", ""), row.get("status_latest", ""))
    s += bobot
    harga = row.get("harga", 0) or 0; volume = row.get("volume", 0) or 0
    rank_mc = row.get("rank_market_cap", 100) or 100
    if harga < 100: s += 10
    elif harga < 200: s += 7
    if volume > 10000000: s += 15
    elif volume > 5000000: s += 10
    if rank_mc < 40: s += 15
    elif rank_mc < 70: s += 10
    chg = row.get("change", 0) or 0
    if chg > 5: s += 15
    elif chg > 3: s += 10
    rsi = row.get("rsi", 50) or 50
    if 55 <= rsi <= 65: s += 10
    return round(max(0, min(100, s)))

def skor_bsjp(row):
    s = 0
    _, bobot, _ = deteksi_skenario(row.get("status_7d", ""), row.get("status_latest", ""))
    s += bobot
    harga = row.get("harga", 0) or 0; volume = row.get("volume", 0) or 0
    rank_mc = row.get("rank_market_cap", 100) or 100
    if harga < 100: s += 10
    elif harga < 200: s += 7
    if volume > 10000000: s += 15
    elif volume > 5000000: s += 10
    if rank_mc < 40: s += 15
    elif rank_mc < 70: s += 10
    high = row.get("high", 0) or 0; low = row.get("low", 0) or 0; close = row.get("harga", 0) or 0
    if high > low and close > 0:
        cp = (close - low) / (high - low)
        if cp > 0.8: s += 15
        elif cp > 0.7: s += 10
    rsi = row.get("rsi", 50) or 50
    if 45 <= rsi <= 60: s += 10
    return round(max(0, min(100, s)))

def skor_swing(row):
    s = 0
    if "Big Acc" in str(row.get("status_7d", "")): s += 25
    elif "Acc" in str(row.get("status_7d", "")): s += 18
    macd = row.get("macd", 0) or 0; macd_sig = row.get("macd_signal", 0) or 0
    if macd > macd_sig: s += 20
    rsi = row.get("rsi", 50) or 50
    if 45 <= rsi <= 65: s += 20
    elif 40 <= rsi <= 70: s += 12
    harga = row.get("harga", 0) or 0; sma20 = row.get("sma20", 0) or 0
    if sma20 and harga > sma20: s += 20
    vol = row.get("volume", 0) or 0
    if vol > 1000000: s += 15
    elif vol > 500000: s += 8
    return round(s)

def skor_value(row):
    s = 0
    per = row.get("per", 100) or 100
    if 0 < per < 10: s += 30
    elif per < 15: s += 22
    elif per < 20: s += 12
    pbv = row.get("pbv", 100) or 100
    if 0 < pbv < 1: s += 25
    elif pbv < 2: s += 18
    elif pbv < 3: s += 10
    ey = row.get("earnings_yield", 0) or 0
    if ey > 10: s += 25
    elif ey > 7: s += 18
    elif ey > 5: s += 12
    if "Big Acc" in str(row.get("status_7d", "")): s += 20
    elif "Acc" in str(row.get("status_7d", "")): s += 12
    return round(s)

def skor_hidden_gem(row):
    s = 0
    per = row.get("per", 100) or 100
    if 0 < per < 8: s += 25
    elif per < 12: s += 18
    elif per < 15: s += 10
    pbv = row.get("pbv", 100) or 100
    if 0 < pbv < 1: s += 20
    elif pbv < 2: s += 14
    ey = row.get("earnings_yield", 0) or 0
    if ey > 12: s += 20
    elif ey > 7: s += 14
    if "Big Acc" in str(row.get("status_7d", "")): s += 25
    elif "Acc" in str(row.get("status_7d", "")): s += 15
    fpe = row.get("forward_pe", 100) or 100
    if 0 < fpe < 10: s += 10
    elif fpe < 15: s += 5
    return round(s)

def render_tabel(df, show_segar=False):
    if df.empty:
        st.info("Tidak ada saham di kategori ini.")
        return
    html = '<table class="screener-table"><thead><tr>'
    html += '<th>Kode</th><th>Nama</th><th>Harga</th><th>Change</th><th>Status 7D</th>'
    if show_segar: html += '<th>LATEST</th><th>Skenario</th>'
    html += '<th>RSI</th><th>VWAP</th><th>Skor</th><th>TP</th><th>CL</th>'
    html += '</tr></thead><tbody>'
    for _, r in df.iterrows():
        chg = r.get("change", 0) or 0
        chg_color = "#22c55e" if chg >= 0 else "#ef4444"
        intraday = r.get("intraday_data")
        vwap_status = "✅" if (intraday and intraday.get("close_above_vwap")) else "❌"
        skenario_html = ""
        if show_segar:
            _, bobot, label = deteksi_skenario(r.get("status_7d", "-"), r.get("status_latest", "-"))
            skenario_html = f'<span class="accel-badge">{label}</span>' if bobot > 15 else label
        html += f"""<tr>
            <td><b style="color:#38bdf8;">{r['symbol']}</b></td>
            <td>{str(r.get('name', ''))[:18]}</td>
            <td>Rp {r['harga']:,.0f}</td>
            <td style="color:{chg_color};">{chg:+.2f}%</td>
            <td>{r.get('status_7d', '-')}</td>"""
        if show_segar:
            html += f"""<td>{r.get('status_latest', '-')}</td><td>{skenario_html}</td>"""
        html += f"""<td>{(r.get('rsi', 0) or 0):.1f}</td>
            <td style="text-align:center;">{vwap_status}</td>
            <td><b style="color:#facc15;">{r['skor']}</b></td>
            <td style="color:#22c55e;">Rp {r.get('tp', 0):,.0f}</td>
            <td style="color:#ef4444;">Rp {r.get('cl', 0):,.0f}</td>
        </tr>"""
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)

# =========================================================================
# UI UTAMA
# =========================================================================

render_dashboard()
render_news()
st.markdown("---")

# =========================================================================
# AI CONTROL
# =========================================================================

with st.sidebar:
    st.markdown("### ⚙️ AI CONTROL")
    st.markdown("**📂 Pilih Kategori:**")
    kategori = st.radio("Kategori", [
        "🎯 Silent Accumulation",
        "⚡ Scalping Markup",
        "🌅 BPJS (Beli Pagi Jual Sore)",
        "🌆 BSJP (Beli Sore Jual Pagi)",
        "🔄 Swing (1-2 Minggu)",
        "💎 Value (1-3 Bulan)",
        "🏆 Hidden Gem (3-12 Bulan)",
        "📊 Semua Kategori"
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**🔧 Filter:**")
    min_price = st.number_input("Harga Min (Rp)", 50, 5000, 50, step=50)
    max_price = st.number_input("Harga Max (Rp)", 100, 10000, 5000, step=100)
    max_scan = st.slider("Max Saham", 10, 100, 30, step=10)

    st.markdown("---")
    st.markdown("**🎯 Threshold:**")
    th_silent = st.slider("Silent Accumulation", 0, 100, 65)
    th_scalping = st.slider("Scalping Markup", 0, 100, 70)
    th_bpjs = st.slider("BPJS", 0, 100, 65)
    th_bsjp = st.slider("BSJP", 0, 100, 65)
    th_swing = st.slider("Swing", 0, 100, 60)
    th_value = st.slider("Value", 0, 100, 55)
    th_hg = st.slider("Hidden Gem", 0, 100, 60)

    st.markdown("---")
    use_intraday = st.checkbox("Yahoo Intraday", value=True)
    scan_btn = st.button("🚀 SCAN", type="primary", use_container_width=True)
    st.caption("**Sumber:** Stockbit MCP + Yahoo")

# =========================================================================
# SCAN
# =========================================================================

if scan_btn:
    client = StockbitClient()
    ai_speak("🔍 Memindai...", "🟡 Scanning")

    with st.spinner("🔍 Mengambil daftar saham..."):
        movers = client.market_movers()
        st.info(f"📊 Ditemukan {len(movers)} saham")

        filtered = [m for m in movers if min_price <= (m.get("price") or 0) <= max_price][:max_scan]

        # Tentukan kebutuhan berdasarkan kategori
        need_latest = kategori in ["⚡ Scalping Markup", "🌅 BPJS (Beli Pagi Jual Sore)",
                                   "🌆 BSJP (Beli Sore Jual Pagi)", "🎯 Silent Accumulation", "📊 Semua Kategori"]
        need_intraday = use_intraday and kategori in ["⚡ Scalping Markup", "🎯 Silent Accumulation", "📊 Semua Kategori"]
        need_keystats = kategori in ["💎 Value (1-3 Bulan)", "🏆 Hidden Gem (3-12 Bulan)", "📊 Semua Kategori"]

        # Batch Yahoo
        batch_intraday = {}
        if need_intraday:
            with st.spinner("📊 Batch Yahoo intraday..."):
                symbols_list = [r.get("symbol") for r in filtered if r.get("symbol")]
                batch_intraday = get_yahoo_intraday_batch(symbols_list, interval="15m", period="10d")

        # Parallel scan
        results = []
        progress = st.progress(0, text="Memindai...")

        def scan_one(args):
            i, row = args
            symbol = row.get("symbol", "")
            if not symbol: return None
            try:
                bandar_7d = client.bandar_detector_cached(symbol, period="LAST_7_DAYS")
                if not bandar_7d: return None

                bandar_latest = client.bandar_detector_cached(symbol, period="LATEST") if need_latest else None
                tech = client.technicals_cached(symbol)
                if not tech: return None
                ks = client.keystats_cached(symbol) if need_keystats else {}

                status_latest = bandar_latest.get("status", bandar_7d.get("status", "-")) if bandar_latest else bandar_7d.get("status", "-")

                harga = row.get("price", 0) or 0
                volume = row.get("volume", 0) or 0
                atr = tech.get("atr", 0) or 0
                high = row.get("high", 0) or harga
                low = row.get("low", 0) or harga

                intraday_data = batch_intraday.get(symbol)
                top_acc_lots = abs(bandar_7d["top_accumulator"].get("netLots", 0)) if bandar_7d.get("top_accumulator") else 0
                top_dist_lots = abs(bandar_7d["top_distributor"].get("netLots", 0)) if bandar_7d.get("top_distributor") else 0

                tp = harga + (2 * atr) if atr else harga * 1.05
                cl = harga - (1.5 * atr) if atr else harga * 0.95

                data_row = {
                    "symbol": symbol, "name": row.get("name", ""),
                    "harga": harga, "change": row.get("changePercent", 0) or 0,
                    "volume": volume, "high": high, "low": low,
                    "frequency": row.get("frequency", 0) or 0,
                    "status_7d": bandar_7d.get("status", "-"),
                    "status_latest": status_latest,
                    "percent_7d": bandar_7d.get("percent", 0) or 0,
                    "top_acc_lots": top_acc_lots, "top_dist_lots": top_dist_lots,
                    "rsi": tech.get("rsi", 50) or 50,
                    "macd": tech.get("macd", 0) or 0,
                    "macd_signal": tech.get("macd_signal", 0) or 0,
                    "atr": atr, "sma20": tech.get("sma20", 0) or 0,
                    "per": ks.get("per", 0) if ks else 0,
                    "pbv": ks.get("pbv", 0) if ks else 0,
                    "earnings_yield": ks.get("earnings_yield", 0) if ks else 0,
                    "forward_pe": ks.get("forward_pe", 0) if ks else 0,
                    "rank_market_cap": ks.get("rank_market_cap", 100) if ks else 100,
                    "altman_z": ks.get("altman_z", 3) if ks else 3,
                    "tp": tp, "cl": cl, "intraday_data": intraday_data,
                }
                data_row["skor_silent"] = skor_silent_accumulation(data_row)
                data_row["skor_scalping"] = skor_scalping_markup(data_row)
                data_row["skor_bpjs"] = skor_bpjs(data_row)
                data_row["skor_bsjp"] = skor_bsjp(data_row)
                data_row["skor_swing"] = skor_swing(data_row)
                data_row["skor_value"] = skor_value(data_row)
                data_row["skor_hidden_gem"] = skor_hidden_gem(data_row)
                return data_row
            except Exception as e:
                print(f"Error {symbol}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scan_one, (i, row)) for i, row in enumerate(filtered)]
            for i, future in enumerate(futures):
                progress.progress((i + 1) / len(futures), text=f"Scanning {i+1}/{len(futures)}...")
                result = future.result()
                if result: results.append(result)

        progress.empty()
        st.success(f"✅ Scan selesai: {len(results)} saham")
        ai_speak(f"✅ {len(results)} saham ditemukan.", "🟢 Online")

        if results:
            df = pd.DataFrame(results)
            kategori_map = {
                "🎯 Silent Accumulation": ("skor_silent", th_silent, "🎯 SILENT ACCUMULATION", "Top Loser + Akumulasi", False),
                "⚡ Scalping Markup": ("skor_scalping", th_scalping, "⚡ SCALPING MARKUP", "Akumulasi SEGAR + VWAP", True),
                "🌅 BPJS (Beli Pagi Jual Sore)": ("skor_bpjs", th_bpjs, "🌅 BPJS", "Momentum pagi + Gorengan", True),
                "🌆 BSJP (Beli Sore Jual Pagi)": ("skor_bsjp", th_bsjp, "🌆 BSJP", "Closing kuat + Gorengan", True),
                "🔄 Swing (1-2 Minggu)": ("skor_swing", th_swing, "🔄 SWING", "Akumulasi 7D + MACD", False),
                "💎 Value (1-3 Bulan)": ("skor_value", th_value, "💎 VALUE", "PER + PBV + Earnings Yield", False),
                "🏆 Hidden Gem (3-12 Bulan)": ("skor_hidden_gem", th_hg, "🏆 HIDDEN GEM", "PER + PBV + Forward PE", False),
            }
            if kategori in kategori_map:
                key, threshold, nama, desc, show_segar = kategori_map[kategori]
                df_result = df[df[key] >= threshold].copy()
                df_result["skor"] = df_result[key]
                df_result = df_result.sort_values("skor", ascending=False)
                st.markdown(f'<div class="kategori-header"><h2>{nama} — {len(df_result)} saham</h2><p>{desc} | Threshold: {threshold}</p></div>', unsafe_allow_html=True)
                render_tabel(df_result, show_segar=show_segar)
            else:
                st.markdown("## 📊 SEMUA KATEGORI")
                for kat_nama, (key, threshold, nama, desc, show_segar) in kategori_map.items():
                    df_kat = df[df[key] >= threshold].copy()
                    df_kat["skor"] = df_kat[key]
                    df_kat = df_kat.sort_values("skor", ascending=False)
                    st.markdown(f'<div class="kategori-header"><h2>{nama} — {len(df_kat)} saham</h2><p>{desc} | Threshold: {threshold}</p></div>', unsafe_allow_html=True)
                    render_tabel(df_kat.head(10), show_segar=show_segar)
        else:
            st.warning("Tidak ada data.")

else:
    st.markdown("""
    <div style="background:rgba(30,41,59,0.5);padding:40px;border-radius:12px;text-align:center;margin-top:20px;">
        <div style="font-size:4rem;margin-bottom:20px;">🎯</div>
        <h3 style="color:#38bdf8;">AI CONTROL — 7 KATEGORI SCREENER</h3>
        <p style="color:#94a3b8;">Pilih kategori, atur threshold, lalu klik <b>"🚀 SCAN"</b>.</p>
        <p style="color:#64748b;font-size:0.85rem;margin-top:20px;">
            ⚡ Cache aktif — scan kedua ~10x lebih cepat
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
    ⚠️ <b>Disclaimer:</b> Screener ini hanya alat bantu analisis. Keputusan investasi di tangan Anda.
</div>
""", unsafe_allow_html=True)