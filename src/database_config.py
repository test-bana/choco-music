import os

# データベースの接続設定
# ReplitのPostgreSQL（Neon）を使用するための設定ファイルです。
# 実際の接続情報は環境変数（DATABASE_URL）から読み込まれます。

DB_CONFIG = {
    "DB_TYPE": "PostgreSQL",
    "DATABASE_URL": os.environ.get('DATABASE_URL'),
    "PGHOST": os.environ.get('PGHOST'),
    "PGPORT": os.environ.get('PGPORT'),
    "PGUSER": os.environ.get('PGUSER'),
    "PGDATABASE": os.environ.get('PGDATABASE'),
}

# Flask-SQLAlchemy用のURI変換（postgres:// を postgresql:// に修正）
def get_sqlalchemy_uri():
    uri = DB_CONFIG["DATABASE_URL"]
    if uri and uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri
