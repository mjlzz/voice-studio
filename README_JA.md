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

## 動作環境

- **Python**: 3.10 以上
- **Node.js**: 16.0 以上（Web UI のみ）
- **OS**: Windows / macOS / Linux
- **メモリ**: 4GB以上推奨（STTモデルの読み込み用）
- **ストレージ**: 約2GB（初回使用時にモデルが自動ダウンロードされます）

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

### 1. バックエンド起動

```bash
vs serve
# http://localhost:8765/docs でAPIドキュメントを確認
```

### 2. Web UI

```bash
# フロントエンド開発サーバーを起動（バックエンド起動が必要）
cd web && npm run dev
# http://localhost:2345 にアクセス
```

### 3. フローティングマイク

```bash
# フローティングマイクを起動（バックエンド起動が必要）
vs mic

# 2つの認識モード：
# - 一括モード（デフォルト）：録音完了後に一括認識
# - リアルタイムストリーミング：話しながらリアルタイム認識
# トレイアイコンを右クリック → 認識モード → モードを選択
```

### 4. CLIコマンド

```bash
# 音声認識
vs stt -i recording.mp3 -o result.json

# 音声合成
vs tts -t "こんにちは世界" -o output.mp3              # クラウド（デフォルト）
vs tts -t "こんにちは世界" -o output.wav --engine local  # ローカルオフライン
vs tts -t "Hello 世界" -o output.wav --engine mixed  # 中日混合

# 利用可能な音声を確認
vs voices
vs voices --local  # ローカルモデルの状態を確認

# サービス管理
vs dev        # 開発サーバー起動（フロントエンド＋バックエンド）
vs dev --open # 起動してブラウザを開く
vs status     # サービス状態を確認
vs stop       # サービスを停止
vs restart    # サービスを再起動
vs logs -f    # ログをリアルタイム追跡
```

### API呼び出し

http://localhost:8765/docs で完全なAPIドキュメントを確認

```bash
# 音声認識
curl -X POST "http://localhost:8765/api/v1/stt/transcribe" \
  -F "file=@test.mp3"

# 音声合成
curl -X POST "http://localhost:8765/api/v1/tts/synthesize?engine=cloud" \
  -H "Content-Type: application/json" \
  -d '{"text": "こんにちは世界", "voice": "ja-JP-NanamiNeural"}' \
  --output speech.mp3
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

2つの設定方法をサポートしています：

**方法1：環境変数**
```bash
export VS_HOST=127.0.0.1
export VS_PORT=8765
```

**方法2：設定ファイル**

テンプレートをコピーして必要に応じて変更してください：
```bash
cp .env.example .env
```

### 主な設定項目

| 変数 | 説明 | デフォルト |
|------|------|----------|
| `VS_HOST` | サーバーバインドアドレス | `127.0.0.1` |
| `VS_PORT` | サーバーポート | `8765` |
| `VS_DEBUG` | デバッグモード | `false` |
| `VS_WHISPER_MODEL` | Whisperモデル (tiny/base/small/medium) | `base` |
| `VS_WHISPER_DEVICE` | 計算デバイス (cpu/cuda) | `cpu` |
| `VS_TTS_ENGINE` | TTSエンジン (cloud/local) | `cloud` |
| `VS_DEFAULT_VOICE` | デフォルト音声 | `ja-JP-NanamiNeural` |

## プライバシーについて

- **ローカルモード**: STTとローカルTTSエンジンは完全にオフラインで動作します。外部サーバーにデータは送信されません
- **クラウドTTS**: クラウド（edge-tts）エンジンを使用する場合、入力テキストは音声合成のためにMicrosoftサーバーに送信されます
- **データ保存**: 生成された音声ファイルはすべてローカルの`~/.voicestudio/output/`に保存されます
- **テレメトリなし**: このプロジェクトは使用データやユーザー情報を収集しません

## ドキュメント

- [技術アーキテクチャとプロジェクト構成](docs/ARCHITECTURE.md) - 技術スタック、アーキテクチャ設計、拡張ガイド

## ライセンス

MIT