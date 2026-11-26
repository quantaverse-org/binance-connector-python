from _binance_cli import margin_parser, nonempty_argument, signed_margin_request


def main():
    parser = margin_parser("按完整 apiKey 删除一把 Margin Special Key。")
    parser.add_argument("--api-key", required=True, type=nonempty_argument, help="要删除的完整 Special Key")
    args = parser.parse_args()
    response = signed_margin_request(
        "DELETE",
        "/sapi/v1/margin/apiKey",
        symbol=args.symbol,
        recv_window=args.recv_window,
        api_key=args.api_key,
    )
    print(f"HTTP {response.status_code}，已删除指定的 Margin Special Key。")


if __name__ == "__main__":
    main()
