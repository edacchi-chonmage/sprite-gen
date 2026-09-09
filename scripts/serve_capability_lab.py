#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""実験用の素材ディレクトリだけを静的配信する。"""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class LabHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        requested = Path(unquote(urlsplit(self.path).path))
        if any(part.startswith(".") for part in requested.parts):
            self.send_error(403)
            return None
        target = Path(self.translate_path(self.path)).resolve()
        if not target.is_relative_to(Path(self.directory).resolve()):
            self.send_error(403)
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(403)
        return None

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="待ち受けアドレス")
    parser.add_argument("--port", type=int, default=4322, help="待ち受けポート")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1] / "assets/capability-lab", help="公開する実験素材のディレクトリ")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("公開ディレクトリがありません。先に実験一覧を作成してください")
    if any((root / name).exists() for name in (".git", "pyproject.toml", "package.json", ".env", ".env.local")):
        parser.error("ソースコードや秘密情報を含むルートは公開できません")
    server = ThreadingHTTPServer((args.host, args.port), partial(LabHandler, directory=str(root)))
    print(f"実験一覧を配信中: http://{args.host}:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
