"""
Stockbit MCP Client Wrapper + Cache
"""

import asyncio
import json
import os
import hashlib
from datetime import date
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class StockbitClient:

    def __init__(self):
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