import argparse

from binance_common.errors import Error, NetworkError
from binance_sdk_sub_account.sub_account import SubAccount

from _binance_cli import rest_configuration


def argument_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--email", required=True, help="子账户邮箱")
    parser.add_argument("--recv-window", type=int, help="请求有效期（毫秒），最大 60000")
    return parser


def rest_api():
    return SubAccount(config_rest_api=rest_configuration()).rest_api


def run(main):
    try:
        main()
    except NetworkError:
        raise SystemExit("网络请求失败，请检查网络连接。") from None
    except Error as exc:
        raise SystemExit(f"币安请求失败：{exc}") from None
