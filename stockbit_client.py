"""
Stockbit MCP Client Wrapper + Cache
"""

import asyncio
import json
import os
import hashlib
import platform
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from datetime import date
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


_NODE_VERSION = "v22.14.0"


def _ensure_node():
    """Make sure Node.js >= 22 (required by stockbit-mcp) is on PATH.

    No-op when a recent-enough node is already installed. Otherwise downloads
    the official prebuilt binary into a local writable dir (repo .node-extra,
    falling back to the system temp dir) and prepends it to PATH. Needed on
    Streamlit Cloud / platforms where apt only ships an older Node.
    """
    def node_major(exe="node"):
        try:
            out = subprocess.run([exe, "-v"], capture_output=True, text=True, timeout=10)
            txt = (out.stdout or "").strip()
            if txt.startswith("v"):
                txt = txt[1:]
            return int(txt.split(".")[0]) if txt else 0
        except Exception:
            return 0

    if node_major() >= 22:
        return

    base = None
    for candidate in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".node-extra"),
        os.path.join(tempfile.gettempdir(), "node-extra"),
    ]:
        try:
            os.makedirs(candidate, exist_ok=True)
            probe = os.path.join(candidate, ".probe")
            with open(probe, "w") as f:
                f.write(".")
            os.remove(probe)
            base = candidate
            break
        except OSError:
            continue
    if base is None:
        return

    sys_name = platform.system().lower()
    if sys_name == "windows":
        dist_name = f"node-{_NODE_VERSION}-win-x64"
        filename = f"{dist_name}.zip"
        extract = zipfile.ZipFile
    elif sys_name == "darwin":
        dist_name = f"node-{_NODE_VERSION}-darwin-x64"
        filename = f"{dist_name}.tar.gz"
        extract = tarfile.open
    else:
        dist_name = f"node-{_NODE_VERSION}-linux-x64"
        filename = f"{dist_name}.tar.gz"
        extract = tarfile.open

    is_zip = filename.endswith(".zip")
    root = os.path.join(base, dist_name)
    bin_dir = root if is_zip else os.path.join(root, "bin")
    node_exe = "node.exe" if sys_name == "windows" else "node"

    if not os.path.exists(os.path.join(bin_dir, node_exe)):
        url = f"https://nodejs.org/dist/{_NODE_VERSION}/{filename}"
        dest = os.path.join(base, filename)
        try:
            urllib.request.urlretrieve(url, dest)
            with extract(dest) as z:
                z.extractall(base)
        finally:
            try:
                os.remove(dest)
            except OSError:
                pass

    if not os.path.exists(os.path.join(bin_dir, node_exe)):
        return

    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    os.environ.setdefault("npm_config_cache", os.path.join(base, "npm-cache"))
    os.environ.setdefault("npm_config_fund", "false")
    os.environ.setdefault("npm_config_update_notifier", "false")
    os.environ.setdefault("NO_UPDATE_NOTIFIER", "1")


class StockbitClient:

    def __init__(self):
        _ensure_node()
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "stockbit-mcp"],
        )

    async def _call_tool(self, tool_name, arguments):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                if result.content and len(result.content) > 0:
                    text = result.content[0].text
                    try:
                        return json.loads(text)
                    except:
                        return {"raw": text}
                return None

    def call(self, tool_name, arguments):
        return asyncio.run(self._call_tool(tool_name, arguments))

    # =========================================================================
    # CACHE HELPER
    # =========================================================================

    def _get_cache_path(self, key):
        cache_dir = "cache"
        os.makedirs(cache_dir, exist_ok=True)
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return f"{cache_dir}/{hash_key}.json"

    def _read_cache(self, key):
        path = self._get_cache_path(key)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                pass
        return None

    def _write_cache(self, key, data):
        path = self._get_cache_path(key)
        try:
            with open(path, "w") as f:
                json.dump(data, f)
        except:
            pass

    # =========================================================================
    # BANDAR DETECTOR
    # =========================================================================

    def bandar_detector(self, symbol, period="LATEST"):
        args = {"symbol": symbol}
        if period != "LATEST":
            args["period"] = period

        result = self.call("bandar_detector", args)
        if not result or "data" not in result:
            return None

        data = result["data"]
        stockbit_detector = data.get("stockbitBandarDetector", {})
        avg = stockbit_detector.get("avg", {})

        top_acc = data.get("topAccumulators", [])
        top_dist = data.get("topDistributors", [])

        return {
            "symbol": data.get("symbol"),
            "from": data.get("from"),
            "to": data.get("to"),
            "net_value": data.get("netValueIdr", 0),
            "status": avg.get("accdist", "-"),
            "percent": avg.get("percent", 0),
            "top_accumulator": top_acc[0] if top_acc else None,
            "top_distributor": top_dist[0] if top_dist else None,
        }

    def bandar_detector_cached(self, symbol, period="LATEST"):
        cache_key = f"bandar_{symbol}_{period}_{date.today()}"
        cached = self._read_cache(cache_key)
        if cached:
            return cached
        result = self.bandar_detector(symbol, period)
        if result:
            self._write_cache(cache_key, result)
        return result

    # =========================================================================
    # TECHNICALS
    # =========================================================================

    def technicals(self, symbol):
        result = self.call("technicals", {"symbol": symbol})
        if not result or "data" not in result:
            return None

        data = result["data"]
        ind = data.get("indicators", {})
        last = data.get("last", {})

        return {
            "rsi": ind.get("rsi14"),
            "macd": ind.get("macd"),
            "macd_signal": ind.get("macdSignal"),
            "macd_hist": ind.get("macdHistogram"),
            "atr": ind.get("atr14"),
            "sma20": ind.get("sma20"),
            "sma50": ind.get("sma50"),
            "sma200": ind.get("sma200"),
            "close": last.get("close"),
            "volume": last.get("volumeLots"),
        }

    def technicals_cached(self, symbol):
        cache_key = f"tech_{symbol}_{date.today()}"
        cached = self._read_cache(cache_key)
        if cached:
            return cached
        result = self.technicals(symbol)
        if result:
            self._write_cache(cache_key, result)
        return result

    # =========================================================================
    # KEYSTATS
    # =========================================================================

    def keystats(self, symbol):
        result = self.call("keystats", {"symbol": symbol})
        if not result or "data" not in result:
            return None

        data = result["data"]
        items = data.get("closure_fin_items_results", [])

        def parse_num(v, default=0):
            try:
                return float(str(v).replace(",", "").replace("%", "").replace("(", "-").replace(")", ""))
            except:
                return default

        metrics = {}
        for group in items:
            for item in group.get("fin_name_results", []):
                name = item.get("fitem_name", "")
                value = item.get("fitem_value", "")

                if "Current PE Ratio (TTM)" in name:
                    metrics["per"] = parse_num(value, 100)
                elif "Current Price to Book Value" in name:
                    metrics["pbv"] = parse_num(value, 100)
                elif "Earnings Yield (TTM)" in name:
                    metrics["earnings_yield"] = parse_num(value, 0)
                elif "Forward PE Ratio" in name:
                    metrics["forward_pe"] = parse_num(value, 100)
                elif "Return on Equity (TTM)" in name:
                    metrics["roe"] = parse_num(value, 0)
                elif "Rank (Market Cap)" in name:
                    metrics["rank_market_cap"] = parse_num(value, 100)
                elif "Altman Z-Score" in name:
                    metrics["altman_z"] = parse_num(value, 3)
                elif "Piotroski F-Score" in name:
                    metrics["piotroski"] = parse_num(value, 5)
                elif "Dividend Yield" in name:
                    metrics["dividend_yield"] = parse_num(value, 0)
                elif "Debt to Equity Ratio" in name:
                    metrics["der"] = parse_num(value, 0)
                elif "Dividend (TTM)" in name:
                    metrics["dividend_ttm"] = parse_num(value, 0)
                elif "Payout Ratio" in name:
                    metrics["payout_ratio"] = parse_num(value, 0)
                elif "Latest Dividend Ex-Date" in name:
                    metrics["ex_date"] = value
                elif "Net Profit Margin (Quarter)" in name:
                    metrics["net_margin"] = parse_num(value, 0)
                elif "Revenue (Quarter YoY Growth)" in name:
                    metrics["revenue_growth"] = parse_num(value, 0)
                elif "Net Income (Quarter YoY Growth)" in name:
                    metrics["earnings_growth"] = parse_num(value, 0)

        return metrics

    def keystats_cached(self, symbol):
        cache_key = f"ks_{symbol}_{date.today()}"
        cached = self._read_cache(cache_key)
        if cached:
            return cached
        result = self.keystats(symbol)
        if result:
            self._write_cache(cache_key, result)
        return result

    # =========================================================================
    # MARKET MOVERS
    # =========================================================================

    def market_movers(self, mover_type="MOVER_TYPE_TOP_VALUE"):
        result = self.call("market_movers", {"type": mover_type})
        if not result or "data" not in result:
            return []
        return result["data"].get("rows", [])


# =========================================================================
# TEST
# =========================================================================

if __name__ == "__main__":
    client = StockbitClient()

    print("=" * 60)
    print("TEST STOCKBIT CLIENT")
    print("=" * 60)

    print("\nBandar Detector BBCA (7D):")
    data = client.bandar_detector("BBCA", period="LAST_7_DAYS")
    if data:
        print(f"   Status: {data['status']}")
        print(f"   Percent: {data['percent']:.2f}%")

    print("\nTechnicals BBCA:")
    tech = client.technicals("BBCA")
    if tech:
        print(f"   RSI: {tech['rsi']}")
        print(f"   ATR: {tech['atr']}")

    print("\nKeystats BBCA:")
    ks = client.keystats("BBCA")
    if ks:
        print(f"   PER: {ks.get('per')}")
        print(f"   PBV: {ks.get('pbv')}")
        print(f"   Dividend Yield: {ks.get('dividend_yield')}")
        print(f"   ROE: {ks.get('roe')}")