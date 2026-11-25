from _sub_account_cli import argument_parser, rest_api, run


def main():
    parser = argument_parser("删除指定子账户的一把 API Key。")
    parser.add_argument("--sub-account-api-key", required=True, help="要删除的完整子账户 API Key")
    args = parser.parse_args()
    if not args.sub_account_api_key:
        parser.error("--sub-account-api-key 不能为空")

    response = rest_api().delete_sub_account_api_key(
        email=args.email,
        sub_account_api_key=args.sub_account_api_key,
        recv_window=args.recv_window,
    )
    print(f"HTTP {response.status}，已删除 {args.email} 的指定 API Key。")


if __name__ == "__main__":
    run(main)
