# Local Voice AI Chatbot (v0.9) - Baikinman Edition

MacBook Air M3 (Unified Memory 16GB) 環境で動作する、ローカルLLMとGPT-SoVITSを統合した音声付きAIチャットボットシステムです。
お子様向けに「ばいきんまん」や「アンパンマン」などのキャラクターと、プライバシーを保ちながらローカル完結で会話を楽しむことができます。

## 🏗️ システムアーキテクチャ

本システムは以下の3つのコンポーネントで構成されています：

1. **LLM (脳みそ):** [Ollama](https://ollama.com/) - Llama 3.2 3B 等を使用し、キャラクターの性格を再現。
2. **TTS (声帯):** [GPT-SoVITS v2Pro](https://github.com/RVC-Boss/GPT-SoVITS) - 学習させた特定の音声モデルでリアルタイム音声合成。
3. **UI/App (統合環境):** Python + Gradio - 音声処理、文字起こし、チャットUIを統合管理。

## 💻 動作環境・前提条件

- **Hardware:** MacBook Air M3 (RAM 16GB) 推奨
- **OS:** macOS (Apple Silicon)
- **Software:**
    - Homebrew (`brew install ffmpeg`)
    - Ollama (バックグラウンドで稼働していること)
    - Python 3.10+ (venv仮想環境を推奨)

## 🚀 セットアップ

### 1. 依存ライブラリのインストール

```bash
# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate

# 必要なパッケージのインストール
pip install gradio ollama pydub openai-whisper httpx
```

### 2. キャラクターの設定 (`characters.json`)

ルートディレクトリに `characters.json` を配置し、キャラクター情報を定義します。

```json
[
  {
    "id": "baikinman",
    "name": "ばいきんまん",
    "llm_model": "llama3.2:3b",
    "system_prompt": "あなたはアニメ「アンパンマン」の「ばいきんまん」です。一人称は「オレ様」で、語尾は「〜なのだ！」「〜してやるぞ！」など特徴的な口調で話します。挨拶は「ハヒフヘホー！」です。アンパンマンのことが嫌いで、いつもいたずらを企んでいます。",
    "tts_config": {
      "ref_audio_path": "./dataset/baikinman/sliced/voice_0.wav",
      "prompt_text": "ここにvoice_0.wavが実際に喋っているテキスト（例：驚き桃の木山椒の木）を入力"
    }
  },
  {
    "id": "anpanman",
    "name": "アンパンマン",
    "llm_model": "llama3.2:3b",
    "system_prompt": "あなたはアンパンマンです。正義感が強く、困っている人を助けるのが大好きです。一人称は「僕」で、優しく話します。",
    "tts_config": {
      "ref_audio_path": "",
      "prompt_text": ""
    }
  }
]
```

## 🎙️ 使い方

### Step 1: 音声合成APIサーバーの起動

GPT-SoVITSのディレクトリで、以下のコマンドを実行し、APIサーバーを立ち上げます。

```bash
# v2Proモデルを指定して起動（MacのGPU/MPSを使用）
python api.py -a 127.0.0.1 -p 9880 -g GPT_weights_v2Pro/baikinman-e15.ckpt -s SoVITS_weights_v2Pro/baikinman_e8_s408.pth -dr mps
```

### Step 2: チャットアプリの起動

プロジェクトのディレクトリ（`GPT-SoVITS-`）で、統合UIアプリを起動します。

```bash
# 別のターミナルウィンドウで実行
python app.py
```

ブラウザで `http://127.0.0.1:7860` にアクセスしてください。

## 🏋️‍♂️ 新しいキャラクターを追加する方法

アプリ内の「キャラクター追加」タブを使用して、以下の手順で行います。

1. **音声スライス:** 長いWAVファイルをアップロードし、無音部分で自動分割を実行します。
2. **文字起こし:** Whisperを使用して、分割された音声のテキストラベル（metadata.list）を自動生成します。
3. **学習:** GPT-SoVITS本家のWebUI（localhost:9874）を使用し、`1A-Formatting` を経て `1B-Training` を実行します。
4. **反映:** 生成されたモデルパスを `characters.json` に追記し、APIサーバーのコマンド引数を更新して再起動します。

## ⚠️ 注意事項・免責事項

- **著作権について:** 本システムで利用するキャラクターの音声、画像、およびモデルデータは、個人および家庭内での私的使用に限定してください。生成した音声データの配布や公開は絶対に行わないでください。
- **リソース管理:** 学習処理（Training）は非常に負荷が高いため、実行中は他の重いアプリケーションを終了させることを推奨します。
- **外部連携:** OllamaおよびGPT-SoVITSのAPIサーバーが正常に稼働している必要があります。

---
Developed by Local Voice AI Architect