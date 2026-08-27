#!/usr/bin/env python3
"""
HD-Electric (Smart-Shop API) -> таблица номенклатуры.

Тянет остатки (freestock), прайс (pricelist) и товары в пути (goodsintransit),
парсит JSON, сливает в один Excel-файл (несколько листов + сводная) и в CSV.

ВАЖНО: запросы уходят только с доверенного IP 91.217.63.94 (его внесли в whitelist).
С любого другого хоста словишь отлуп по авторизации. Запускай на том сервере,
у которого этот внешний IP, либо гони трафик через него.

Зависимости:  pip install requests pandas openpyxl
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

# ======================= КОНФИГ (правь тут) =======================
BASE_URL    = "http://80.252.22.15/ut_vips/hs/smsh"   # без слэша на конце
BASIC_USER  = "SmartShopUser001"
BASIC_PASS  = "Sm@rtSh0p 001"                          # да, с пробелом внутри
COMPANY_INN = "5402143985/540401001"                  # ИНН/КПП вашей конторы
SMSH_SECRET = "3rGAxa9dYM"                             # ключ организации для прайса

TIMEOUT      = 60      # сек на запрос
RETRIES      = 3       # сколько раз долбиться при сетевом обсёре
RETRY_SLEEP  = 5       # пауза между попытками, сек
# ==================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("hde")


def make_session() -> requests.Session:
    """Сессия с прибитыми заголовками. ИНН и секрет шлём везде — лишним не будет."""
    s = requests.Session()
    s.auth = HTTPBasicAuth(BASIC_USER, BASIC_PASS)
    s.headers.update({
        "CompanyINN": COMPANY_INN,
        "CompanySmShSecret": SMSH_SECRET,
        "Accept": "application/json",
    })
    return s


def fetch(session: requests.Session, path: str) -> dict:
    """GET с ретраями. Возвращает распарсенный JSON или кидает исключение."""
    url = f"{BASE_URL}/{path.lstrip('/')}"
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            log.info("GET %s (попытка %d/%d)", url, attempt, RETRIES)
            r = session.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            # 1С иногда отдаёт json с кривой кодировкой — подстрахуемся
            r.encoding = r.encoding or "utf-8"
            try:
                return r.json()
            except json.JSONDecodeError:
                log.error("Ответ не JSON. Первые 500 символов:\n%s", r.text[:500])
                raise
        except requests.RequestException as e:
            last_err = e
            log.warning("Обосрались: %s", e)
            if attempt < RETRIES:
                time.sleep(RETRY_SLEEP)
    raise RuntimeError(f"{url}: не достучались за {RETRIES} попыток -> {last_err}")


# --------------------------- ПАРСЕРЫ ---------------------------

def to_num(series: pd.Series) -> pd.Series:
    """Строки '15.000' / '200.00' -> числа. Мусор -> NaN."""
    return pd.to_numeric(series, errors="coerce")


def parse_stocks(payload: dict) -> pd.DataFrame:
    rows = payload.get("stocks", []) or []
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["vendor_code", "brand_name", "location_name", "unit", "quantity"])
    # в доке местами проскакивает 'unit_code' вместо 'unit' — сведём в одну колонку
    if "unit_code" in df.columns:
        if "unit" in df.columns:
            df["unit"] = df["unit"].fillna(df["unit_code"])
        else:
            df = df.rename(columns={"unit_code": "unit"})
        df = df.drop(columns=[c for c in ("unit_code",) if c in df.columns])
    df["quantity"] = to_num(df.get("quantity"))
    return df


def parse_prices(payload: dict) -> pd.DataFrame:
    rows = payload.get("prices", []) or []
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["vendor_code", "price_withvat", "price_novat", "vat", "base_price"])
    for col in ("price_withvat", "price_novat", "vat", "base_price"):
        if col in df.columns:
            df[col] = to_num(df[col])
    return df


def parse_transit(payload: dict) -> pd.DataFrame:
    """Разворачиваем вложенный planned_arrival в плоские строки."""
    items = payload.get("items", []) or []
    out = []
    for it in items:
        base = {
            "vendor_code": it.get("vendor_code"),
            "brand_name": it.get("brand_name"),
            "unit": it.get("unit"),
        }
        arrivals = it.get("planned_arrival") or []
        if not arrivals:
            out.append({**base, "location_name": None, "quantity": None, "planned_date": None})
            continue
        for a in arrivals:
            out.append({
                **base,
                "location_name": a.get("location_name"),
                "quantity": a.get("quantity"),
                "planned_date": a.get("planned_date"),
            })
    df = pd.DataFrame(out)
    if not df.empty:
        df["quantity"] = to_num(df["quantity"])
    return df


def build_summary(stocks: pd.DataFrame, prices: pd.DataFrame, transit: pd.DataFrame) -> pd.DataFrame:
    """Сводная по артикулу: суммарный остаток + цены + сколько в пути."""
    if not stocks.empty:
        stock_sum = (stocks.groupby("vendor_code", as_index=False)["quantity"]
                     .sum().rename(columns={"quantity": "free_total"}))
    else:
        stock_sum = pd.DataFrame(columns=["vendor_code", "free_total"])

    if not transit.empty:
        tr_sum = (transit.groupby("vendor_code", as_index=False)["quantity"]
                  .sum().rename(columns={"quantity": "transit_total"}))
    else:
        tr_sum = pd.DataFrame(columns=["vendor_code", "transit_total"])

    price_cols = [c for c in ("vendor_code", "price_novat", "price_withvat", "base_price") if c in prices.columns]
    price_slim = prices[price_cols] if price_cols else pd.DataFrame(columns=["vendor_code"])

    df = stock_sum.merge(price_slim, on="vendor_code", how="outer") \
                  .merge(tr_sum, on="vendor_code", how="outer")
    return df.sort_values("vendor_code").reset_index(drop=True)


# --------------------------- ЭКСПОРТ ---------------------------

def export(stocks, prices, transit, summary, out_xlsx: Path, also_csv: bool):
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xw:
        summary.to_excel(xw, sheet_name="Сводная", index=False)
        prices.to_excel(xw,  sheet_name="Прайс",   index=False)
        stocks.to_excel(xw,  sheet_name="Остатки", index=False)
        transit.to_excel(xw, sheet_name="В пути",  index=False)
    log.info("Записал Excel: %s", out_xlsx)

    if also_csv:
        for name, df in (("summary", summary), ("prices", prices),
                         ("stocks", stocks), ("transit", transit)):
            p = out_xlsx.with_name(f"{out_xlsx.stem}_{name}.csv")
            df.to_csv(p, index=False, encoding="utf-8-sig", sep=";")
            log.info("Записал CSV: %s", p)


# --------------------------- MAIN ---------------------------

def main():
    ap = argparse.ArgumentParser(description="Выгрузка номенклатуры HD-Electric")
    ap.add_argument("--articles", help="артикулы через запятую (по конкретным позициям). "
                                        "Пусто = полная выгрузка")
    ap.add_argument("--only", choices=["stock", "price", "transit"], action="append",
                    help="дёргать только указанные методы (можно несколько раз)")
    ap.add_argument("--out", default=None, help="путь к xlsx (по умолчанию с таймстампом)")
    ap.add_argument("--no-csv", action="store_true", help="не плодить CSV, только Excel")
    args = ap.parse_args()

    want = set(args.only) if args.only else {"stock", "price", "transit"}
    arts = [a.strip() for a in args.articles.split(",") if a.strip()] if args.articles else []

    session = make_session()
    stocks = prices = transit = None

    try:
        if "stock" in want:
            if arts:
                frames = [parse_stocks(fetch(session, f"freestock/{a}")) for a in arts]
                stocks = pd.concat(frames, ignore_index=True) if frames else parse_stocks({})
            else:
                stocks = parse_stocks(fetch(session, "freestock"))
            log.info("Остатки: %d строк", len(stocks))

        if "price" in want:
            if arts:
                frames = [parse_prices(fetch(session, f"pricelist/{a}")) for a in arts]
                prices = pd.concat(frames, ignore_index=True) if frames else parse_prices({})
            else:
                # полный прайс одним запросом; если 1С потребует артикул в пути — гони через --articles
                prices = parse_prices(fetch(session, "pricelist"))
            log.info("Прайс: %d строк", len(prices))

        if "transit" in want:
            transit = parse_transit(fetch(session, "goodsintransit"))
            log.info("В пути: %d строк", len(transit))

    except Exception as e:
        log.error("Кранты: %s", e)
        sys.exit(1)

    # пустышки для тех, что не тянули
    stocks  = stocks  if stocks  is not None else parse_stocks({})
    prices  = prices  if prices  is not None else parse_prices({})
    transit = transit if transit is not None else parse_transit({})

    summary = build_summary(stocks, prices, transit)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(args.out) if args.out else Path(f"hdelectric_{ts}.xlsx")
    export(stocks, prices, transit, summary, out, also_csv=not args.no_csv)

    log.info("Готово. Сводная: %d артикулов.", len(summary))


if __name__ == "__main__":
    main()
