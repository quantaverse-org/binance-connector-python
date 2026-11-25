import json

from _sub_account_cli import argument_parser, rest_api, run


def main():
    parser = argument_parser("查询子账户的 API Key。省略目标 Key 时按页列出。")
    parser.add_argument("--sub-account-api-key", help="精确查询指定的子账户 API Key")
    parser.add_argument("--page", type=int, default=1, help="页码，默认 1")
    parser.add_argument("--size", type=int, default=30, help="每页条数，默认 30，最多 100")
    args = parser.parse_args()
    if args.page < 1 or not 1 <= args.size <= 100:
        parser.error("--page 必须大于等于 1，--size 必须在 1 到 100 之间")

    data = rest_api().query_sub_account_api_key(
        email=args.email,
        sub_account_api_key=args.sub_account_api_key,
        page=args.page,
        size=args.size,
        recv_window=args.recv_window,
    ).data()
    payload = data.to_dict() if hasattr(data, "to_dict") else data
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run(main)
