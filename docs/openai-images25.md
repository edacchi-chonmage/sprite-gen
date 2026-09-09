# OpenAI Images 2.5 接続

制作チャットは画像生成と中間コマ生成にOpenAI Images APIを使う。内部エンジンからは `--provider openai` で同じ接続先を指定できる。

参照画像がある場合は `/v1/images/edits` に画像の実バイトを送信し、ない場合は `/v1/images/generations` を呼ぶ。既定モデルは `gpt-image-2.5-sunburst`。APIキーは環境変数 `OPENAI_API_KEY` から読み、レポートには書かない。

```bash
/path/to/sprite-gen/.venv/bin/sprite-gen gen \
  --provider openai --model gpt-image-2.5-sunburst \
  --prompt-file /path/to/run/prompts/run.txt \
  --ref /path/to/run/base-source.png \
  --ref /path/to/run/references/layout-guides/run.png \
  --out /path/to/run/raw/run.png \
  --report /path/to/run/reports/openai-run.json
```

`quality=high`、`size=auto`、PNG出力、1枚生成で実行する。参照ごとのSHA256とバイト数、使用量、リクエスト識別子、要求モデルをレポートに残す。APIがモデル名を返さない場合は、要求したモデル名であることを `model_source=request` と記録する。

透明画像をAPIから直接取得する場合は `--transparent --alpha-mode native` を指定する。スプライトの行生成では、既存の背景色除去・切り出し処理を使えるよう、通常はプロンプトで単色背景を指定する。

通信の失敗は課金状態が不明なため自動再試行しない。CodexやGrokにも切り替えない。既存CLIの `--aspect-ratio` はこの経路では受け付けず、配置はプロンプトと参照ガイドで指示する。

中間コマ生成では前後の姿勢の実画像を参照として送る。生成直後と抽出後の画像を比較し、同一人物に見えるか、ドット化で顔が崩れていないか、動きが自然につながるかを個別に確認する。チャットからの起動と保存先は [制作チャット](chat-studio.md) を参照。

公式仕様: https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst
