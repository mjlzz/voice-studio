# Voice Studio

[中文](README.md) | [English](README_EN.md) | 日本語

音声創作を身近に - 軽量・柔軟・拡張可能な音声処理ツールキット

## プレビュー

<p align="center">
  <img src="docs/screenshots/web-stt.png" width="90%" alt="STT Web UI">
</p>
<p align="center">
  <img src="docs/screenshots/web-tts.png" width="90%" alt="TTS Web UI">
</p>

<p align="center">
  <img src="docs/screenshots/floating-mic.png" width="20%" alt="フローティングマイク">
  <img src="docs/screenshots/system-tray.png" width="30%" alt="システムトレイメニュー">
</p>

## 機能

- **Web UI**: モダンでシンプルなWebインターフェース、すぐに使える
- **STT（音声認識）**: faster-whisperベース、日英中混合認識対応、単語レベルのタイムスタンプ付き
  - TXT、SRT、JSON形式でエクスポート
- **TTS（音声合成）**:
  - **クラウド**: edge-ttsベース、高品質な多声合成
  - **ローカル**: Piper TTSベース、オフライン対応、CPU最適化
  - **中日混合**: ONNXモデルベース、中日語シームレス混合合成、長文自動処理
- **フローティングマイク**: デスクトップ浮遊ウィンドウ、ワンクリックで音声認識、システムトレイ対応、クリップボードに自動コピー
  - **リアルタイムストリーミング**: 話しながらリアルタイム認識
  - **一括モード**: 録音完了後に一括認識（デフォルト）
- **REST API**: FastAPIバックエンドサービス、統合が簡単
- **CLIツール**: コマンドラインで素早く操作、プロセス管理対応

## インストール

```bash
# Python依存パッケージをインストール
pip install -e .

# Web UI依存パッケージをインストール
cd web && npm install
```

> **ヒント**: インストール後、`vs`コマンドが使えます。コマンドが見つからない場合は、`python -m voice_studio.cli`を代わりに使用してください：
> ```bash
> python -m voice_studio.cli serve
> ```
> または、Python ScriptsディレクトリがPATH環境変数にあることを確認してください。

## クイックスタート

### Web UI

```bash
# バックエンドサービスを起動
vs serve

# フロントエンド開発サーバーを起動（別ターミナル）
cd web && npm run dev

# http://localhost:2345 にアクセス
```

### CLIの使用

```bash
# ========== 音声認識 ==========

# ファイル認識
vs stt -i recording.mp3 -o result.json

# ========== 音声合成 ==========

# クラウドTTS（デフォルト、インターネット必要）
vs tts -t "こんにちは、テストです" -o output.mp3

# ローカルTTS（オフライン、初回は自動でモデルをダウンロード）
vs tts -t "こんにちは、テストです" -o output.wav --engine local

# 中日混合TTS（中日語シームレス混合、オフライン対応）
vs tts -t "voice studioへようこそ、素晴らしいツールです" -o output.wav --engine mixed

# 利用可能な音声を確認
vs voices

# ローカルモデルの状態を確認
vs voices --local

# ========== サービス管理 ==========

# 開発サーバーを起動（フロントエンド＋バックエンド）
vs dev

# 開発サーバーを起動してブラウザを開く
vs dev --open

# バックエンド/フロントエンドのみ起動
vs dev --backend-only
vs dev --frontend-only

# サービス状態を確認
vs status

# サービスを停止
vs stop

# サービスを再起動
vs restart

# ログを確認
vs logs              # 最新50行
vs logs --backend    # バックエンドログのみ
vs logs -f           # ログをリアルタイム追跡

# APIサーバーを起動（バックエンドのみ）
vs serve

# ========== フローティングマイク ==========

# フローティングマイクを起動（バックエンドサービスが必要）
vs mic

# フローティングマイクは2つの認識モードをサポート：
# - 一括モード（デフォルト）：録音完了後に一括認識
# - リアルタイムストリーミング：話しながらリアルタイム認識
# トレイアイコンを右クリック → 認識モード → モードを選択
```

### APIの使用

サービス起動後、http://localhost:8765/docs でインタラクティブAPIドキュメントを確認

#### STTエンドポイント

```bash
# 音声ファイルをアップロードして認識
curl -X POST "http://localhost:8765/api/v1/stt/transcribe" \
  -F "file=@test.mp3"
```

#### TTSエンドポイント

```bash
# クラウドTTS（デフォルト）
curl -X POST "http://localhost:8765/api/v1/tts/synthesize?engine=cloud" \
  -H "Content-Type: application/json" \
  -d '{"text": "こんにちは世界", "voice": "ja-JP-NanamiNeural"}' \
  --output speech.mp3

# ローカルTTS（オフライン）
curl -X POST "http://localhost:8765/api/v1/tts/synthesize?engine=local" \
  -H "Content-Type: application/json" \
  -d '{"text": "こんにちは世界", "voice": "ja_JP-voice"}' \
  --output speech.wav

# 中日混合TTS
curl -X POST "http://localhost:8765/api/v1/tts/synthesize-mixed" \
  -H "Content-Type: application/json" \
  -d '{"text": "voice studioへようこそ、素晴らしいツールです", "length_scale": 1.0}' \
  --output speech_mixed.wav

# 利用可能な音声を取得
curl "http://localhost:8765/api/v1/tts/voices?engine=cloud&language=ja"
curl "http://localhost:8765/api/v1/tts/voices?engine=local"
```

## Web UIの機能

### 多言語対応
Web UIは中国語、英語、日本語の3つのインターフェース言語をサポート：
- ブラウザ言語を自動検出
- 設定ページで言語を切り替え
- 言語設定を自動保存

### 音声認識（STT）
- ドラッグ＆ドロップまたはクリックで音声ファイルをアップロード
- 複数の形式に対応（MP3、WAV、M4A、OGG、FLAC）
- リアルタイムで認識進捗を表示
- 単語レベルのタイムスタンプ
- エクスポート形式：TXT、SRT、JSON

### 音声合成（TTS）
- 3つのエンジンモード：クラウド / ローカル / 混合
- **クラウドモード**: 多声選択、話速・音量調整
- **ローカルモード**: Piper TTSオフライン合成
- **混合モード**:
  - 中日語シームレス入力対応
  - 初回使用時にモデルを自動ダウンロード
  - 長文をスマートにチャンク処理
  - 話速調整（0.5x ～ 2.0x）
- 試聴とダウンロード

## プリセット音声

### クラウド音声（edge-tts）

#### 日本語音声

| 名前 | 音声ID | 特徴 |
|------|---------|------|
| nanami | ja-JP-NanamiNeural | 七海 - 女性、自然 |
| keita | ja-JP-KeitaNeural | 圭太 - 男性、自然 |

#### 中国語音声

| 名前 | 音声ID | 特徴 |
|------|---------|------|
| xiaoxiao | zh-CN-XiaoxiaoNeural | 暁暁 - 女性、自然 |
| yunxi | zh-CN-YunxiNeural | 雲希 - 男性、若々しい |

#### 英語音声

| 名前 | 音声ID | 特徴 |
|------|---------|------|
| jenny | en-US-JennyNeural | Jenny - 女性、自然 |
| guy | en-US-GuyNeural | Guy - 男性、自然 |
| aria | en-US-AriaNeural | Aria - 女性、感情豊か |

### ローカル音声（Piper TTS）

| 名前 | 音声ID | 言語 | 説明 |
|------|---------|------|------|
| huayan | zh_CN-huayan | 中国語 | 華燕 - 女性 |
| lessac | en_US-lessac | 英語 | Lessac - 女性、自然 |
| amy | en_US-amy | 英語 | Amy - 女性 |

### 中日混合TTS

ONNXモデルベースの中日混合音声合成の特徴：

| 特徴 | 説明 |
|------|------|
| 中日混合 | 同じテキストでシームレスに切り替え、「voice studioへようこそ」など |
| 完全オフライン | モデルダウンロード後はインターネット不要 |
| 統一音声 | 中日語で同じ音声を使用、より自然 |
| 長文対応 | 自動チャンク処理、並列合成 |
| 話速制御 | 0.5x ～ 2.0x で調整可能 |

> 初回使用時、モデルはModelScopeから`~/.voicestudio/models/mixed_tts/`に自動ダウンロードされます（約125MB）

> ローカルエンジン初回使用時、モデルは`~/.voicestudio/models/piper/`に自動ダウンロードされます

## 設定

環境変数（プレフィックス`VS_`）:

```bash
# サーバー設定
VS_HOST=127.0.0.1
VS_PORT=8765
VS_DEBUG=true

# STT設定
VS_WHISPER_MODEL=base  # tiny/base/small/medium
VS_WHISPER_DEVICE=cpu

# TTS設定
VS_DEFAULT_VOICE=ja-JP-NanamiNeural
```

## ドキュメント

- [技術アーキテクチャとプロジェクト構成](docs/ARCHITECTURE.md) - 技術スタック、アーキテクチャ設計、拡張ガイド

## ライセンス

MIT