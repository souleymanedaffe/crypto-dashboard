import os
from flask import Flask, render_template, jsonify, request, abort
import pandas as pd

def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    # --- Charger le CSV au démarrage ---
    base_dir = os.path.abspath(os.path.dirname(__file__))
    csv_path = os.path.join(base_dir, "data", "crypto_prices.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV introuvable: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["date"])
    # Nettoyage minimal
    df["symbol"] = df["symbol"].str.upper()
    df = df.sort_values(["symbol", "date"])

    # Dernière valeur par symbole (pour le tableau)
    def latest_snapshot():
        idx = df.groupby("symbol")["date"].idxmax()
        snap = df.loc[idx, ["symbol", "date", "price", "market_cap", "volume"]]
        # variation 7 jours si possible
        change_rows = []
        for sym in snap["symbol"]:
            d_sym = df[df["symbol"] == sym].sort_values("date")
            if len(d_sym) >= 8:
                last = d_sym.iloc[-1]["price"]
                prev = d_sym.iloc[-8]["price"]
                pct = (last - prev) / prev * 100
            else:
                pct = None
            change_rows.append(pct)
        snap = snap.assign(change_7d=change_rows)
        snap = snap.sort_values("symbol")
        return snap

    @app.route("/")
    def index():
        snap = latest_snapshot()
        records = []
        for _, r in snap.iterrows():
            records.append({
                "symbol": r["symbol"],
                "date": r["date"].strftime("%Y-%m-%d"),
                "price": float(r["price"]),
                "market_cap": int(r["market_cap"]),
                "volume": int(r["volume"]),
                "change_7d": None if pd.isna(r["change_7d"]) else round(float(r["change_7d"]), 2)
            })
        return render_template("index.html", snapshot=records)

    @app.route("/api/symbols")
    def api_symbols():
        symbols = sorted(df["symbol"].unique().tolist())
        return jsonify(symbols)

    @app.route("/api/series")
    def api_series():
        symbol = request.args.get("symbol", "").upper().strip()
        if not symbol:
            abort(400, "symbol is required")
        d_sym = df[df["symbol"] == symbol].sort_values("date")
        if d_sym.empty:
            abort(404, f"symbol {symbol} not found")
        series = {
            "symbol": symbol,
            "dates": d_sym["date"].dt.strftime("%Y-%m-%d").tolist(),
            "prices": d_sym["price"].astype(float).tolist()
        }
        return jsonify(series)

    return app

app = create_app()
