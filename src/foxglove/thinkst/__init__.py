FOXGLOVE_TAG: str = "#foxglove"

SUPPORTED_KINDS: frozenset[str] = frozenset({
    "dns",
    "http",
    "aws-id",
    "slack-api",
    "qr-code",
    "windows-dir",
    "wireguard",
    "credit-card",
    "mysql-dump",
    "svn",
    "sql",
})
