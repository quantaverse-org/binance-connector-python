import json

from _binance_cli import margin_parser, signed_margin_request


def main():
    parser = margin_parser("查询当前杠杆账户的 Margin Special Key 列表。")
    args = parser.parse_args()
    response = signed_margin_request(
        "GET",
        "/sapi/v1/margin/api-key-list",
        symbol=args.symbol,
        recv_window=args.recv_window,
    )
    try:
        keys = response.json()
    except ValueError:
        raise SystemExit("币安响应不是有效的 JSON。") from None
    if not isinstance(keys, list):
        raise SystemExit("币安响应中缺少预期的 Special Key 列表。")
    print(json.dumps(keys, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
