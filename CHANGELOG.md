# 変更履歴

## 2026-09-10 — Sprite Studio の独立

- 自然言語による制作チャットをアプリの主な入口にした。
- `sprite-studio` 起動コマンド、`.env.local` の読み込み、Orcaの作業対象指定を追加。
- 作品・会話・素材を `data/` へ分離し、実験データからの移行処理を追加。
- 過去の版を保った画像生成・中間コマの追加・停止コマと再生順の調整に対応。
- 元絵と生成結果をClaude Sonnetで比較し、問題点を表示。
- 旧Dotter、実験用の起動スクリプト、多言語の旧READMEへの依存を整理。

画像処理エンジンは上流sprite-gen 2.0.3を継承している。以前の変更は[上流版の変更履歴](https://github.com/aldegad/sprite-gen/blob/328b311/CHANGELOG.md)と、このリポジトリのGit履歴を参照。
