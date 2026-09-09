# Sprite Studio の開発

このリポジトリの主役は、Orca経由のClaude SonnetとImages 2.5を使う制作チャット。
旧Dotterのコード・設定・ディレクトリに依存させない。

- 起動入口は `sprite-studio`、アプリは `sprite_gen/serve/chat_studio.py`、画面は `sprite_gen/serve/chat_ui/index.html`。
- `sprite_gen` 配下の抽出・減色・書き出しはアプリが使う画像処理エンジン。名前だけで不要と判断しない。
- 作品・会話・参照素材は `data/` に保存しGitへ含めない。APIキーは `.env.local` または環境変数。
- 元画像と過去の版は上書きしない。移行では件数・画像ハッシュ・参照先を確認する。
- 画像生成APIは有料。自動再試行やテストからの実API呼び出しを増やさない。
- Sonnetには実画像と実際の再生順を渡す。生成終了と見た目の合格を分けて表示する。
- 実行中の制作がある場合は停止・データ移動・サーバー再起動を行わず、終了を待つ。
- UI変更はスマホ幅とPC幅で確認し、下書き・選択中の版・会話スクロールを保つ。
- `.venv/bin/python -m pytest -q` で検証する。OpenAI/Orcaはテストでは差し替える。
- 上流sprite-genの技術資料は `docs/`。アプリの使い方と混同しない。
