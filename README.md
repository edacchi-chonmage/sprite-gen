# Sprite Studio

自然言語でドット絵とアニメーションを作り、見ながら修正するアプリ。

Orca経由のClaude Sonnetが元絵・会話・必要な参考資料を確認して生成指示を作り、Images 2.5が描画する。中間コマの追加、停止コマや再生順の調整、生成後の比較に対応し、会話と作品のバージョンを残す。

## 起動

CPython 3.10+ と `venv`/`ensurepip`、起動済みのOrca、サブスクでログインしたClaude CLIが必要。画像生成にはOpenAIのAPIキーとAPIクレジットを使う。

```sh
git clone https://github.com/edacchi-chonmage/sprite-gen.git
cd sprite-gen
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
cp .env.example .env.local
```

`.env.local` の `OPENAI_API_KEY` を設定し、このリポジトリをOrcaで開いて起動する。

```sh
.venv/bin/sprite-studio
```

[制作チャットを開く](http://127.0.0.1:4323/)。Tailscale経由では `--host <端末のTailscale IP>` を追加する。モデルのサブスク認証はClaude CLI、画像APIの認証はサーバーが扱い、ブラウザーへキーを渡さない。

## 開発

```sh
.venv/bin/python -m pytest -q
```

| 場所 | 役割 |
|---|---|
| `sprite_gen/serve/chat_studio.py` | チャット・生成・保存をつなぐアプリ |
| `sprite_gen/serve/chat_ui/` | チャットと作品ビューアー |
| `sprite_gen/serve/sonnet_bridge.py` | OrcaとClaude Sonnetの接続 |
| `sprite_gen/gen/` | 画像生成APIとの接続 |
| `sprite_gen/frames/`・`compose/`・`effects/` | 抽出・書き出し・モーション加工 |
| `tests/` | アプリと画像処理の検証 |
| `docs/` | 使い方・構成・画像処理の技術資料 |
| `data/` | 作品・会話・参照素材。Git管理外 |

`.env.local` と `data/` をバックアップすれば、秘密情報と制作データをコードから分けて保管できる。旧Dotterのインストールや過去の実験フォルダは起動に必要ない。

[使い方と運用](docs/chat-studio.md) · [資料一覧](docs/README.md) · [開発上の注意](AGENTS.md)

## 元になったソフトウェア

[aldegad/sprite-gen](https://github.com/aldegad/sprite-gen) をforkし、制作チャットを中心とするアプリとして開発している。画像処理エンジンとそのテストを引き継いでいる。Apache-2.0の[LICENSE](LICENSE)と[NOTICE](NOTICE)を維持する。
