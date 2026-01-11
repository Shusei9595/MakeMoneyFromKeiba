#!/bin/bash
set -e

# 引数がある場合はそのまま実行
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

# デフォルトはヘルプ表示
exec keiba-ai --help
