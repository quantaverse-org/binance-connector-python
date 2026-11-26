import argparse
import os
from pathlib import Path

import requests
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import MARGIN_TRADING_REST_API_PROD_URL
from binance_common.utils import (
    clean_none_value,
    encoded_string,
    get_signature,
    get_timestamp,
)
from dotenv import load_dotenv


def rest_configuration():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", interpolate=False)
    key = os.getenv("BINANCE_MASTER_API_KEY")
    secret = os.getenv("BINANCE_MASTER_API_SECRET")
    if not key or not secret:
        raise SystemExit("请在 .env 或环境变量中设置 BINANCE_MASTER_API_KEY 和 BINANCE_MASTER_API_SECRET")
    return ConfigurationRestAPI(api_key=key, api_secret=secret)


def nonempty_argument(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("参数不能为空")
    return value.strip()


def margin_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--symbol", type=nonempty_argument, help="逐仓交易对，例如 BTCUSDT；全仓时省略")
    parser.add_argument("--recv-window", type=int, help="请求有效期（毫秒），最大 60000")
    return parser


def signed_margin_request(method, path, *, symbol, recv_window, api_key=None):
    if recv_window is not None and not 1 <= recv_window <= 60000:
        raise SystemExit("--recv-window 必须在 1 到 60000 毫秒之间")
    config = rest_configuration()
    params = clean_none_value(
        {
            "symbol": symbol,
            "apiKey": api_key,
            "recvWindow": recv_window,
            "timestamp": get_timestamp(),
        }
    )
    query = encoded_string(params)
    signature = get_signature(config, query)
    try:
        response = requests.request(
            method=method,
            url=f"{MARGIN_TRADING_REST_API_PROD_URL}{path}",
            headers=config.base_headers,
            params=f"{query}&signature={signature}",
            timeout=10,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise SystemExit("网络请求失败，无法确认币安的执行结果。") from None

    if not 200 <= response.status_code < 300:
        try:
            error = response.json()
        except ValueError:
            error = None
        message = f"币安请求失败（HTTP {response.status_code}）"
        if isinstance(error, dict):
            message += f" {error.get('code', '')} {error.get('msg', '')}"
        raise SystemExit(message.rstrip())
    return response
