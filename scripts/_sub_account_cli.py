import argparse
import os
from pathlib import Path

from binance_common.errors import Error, NetworkError
from binance_sdk_sub_account.sub_account import ConfigurationRestAPI, SubAccount
from dotenv import load_dotenv


def argument_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--email", required=True, help="子账户邮箱")
    parser.add_argument("--recv-window", type=int, help="请求有效期（毫秒），最大 60000")
    return parser


def rest_api():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", interpolate=False)
    key = os.getenv("BINANCE_MASTER_API_KEY")
    secret = os.getenv("BINANCE_MASTER_API_SECRET")
    if not key or not secret:
        raise SystemExit("请在 .env 或环境变量中设置 BINANCE_MASTER_API_KEY 和 BINANCE_MASTER_API_SECRET")
    config = ConfigurationRestAPI(api_key=key, api_secret=secret)
    return SubAccount(config_rest_api=config).rest_api


def run(main):
    try:
        main()
    except NetworkError:
        raise SystemExit("网络请求失败，请检查网络连接。") from None
    except Error as exc:
        raise SystemExit(f"币安请求失败：{exc}") from None
