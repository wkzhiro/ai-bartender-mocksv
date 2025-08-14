# Gunicorn設定ファイル
import os
import multiprocessing

# サーバーソケット
bind = "0.0.0.0:8000"

# ワーカープロセス設定
workers = multiprocessing.cpu_count() * 2 + 1  # CPUコア数の2倍+1（推奨値）
worker_class = "uvicorn.workers.UvicornWorker"  # FastAPI用のワーカークラス
worker_connections = 1000
max_requests = 1000  # ワーカープロセスが処理するリクエスト数の上限
max_requests_jitter = 100  # ランダムな値を加えて同時に再起動しないようにする

# タイムアウト設定
timeout = 90  # ワーカーがリクエストを処理するタイムアウト（秒）
keepalive = 2  # Keep-Aliveコネクションの持続時間

# プロセス設定
preload_app = True  # アプリケーションの事前読み込み（メモリ使用量削減）
daemon = False  # デーモンモードは無効（Dockerで実行するため）

# ログ設定
accesslog = "-"  # アクセスログを標準出力に出力
errorlog = "-"   # エラーログを標準出力に出力
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# セキュリティ設定
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 環境変数からワーカー数をオーバーライド可能
if os.getenv("GUNICORN_WORKERS"):
    workers = int(os.getenv("GUNICORN_WORKERS"))

# 環境変数からポートをオーバーライド可能
port = os.getenv("PORT", "8000")
bind = f"0.0.0.0:{port}"

# メモリリーク対策
max_requests = 1000
max_requests_jitter = 50