import gradio as gr
import ollama
import asyncio
import json
import os
import shutil
from pydub import AudioSegment
from pydub.silence import split_on_silence
import whisper
import httpx
import base64
import subprocess

# キャラクター設定をロード
with open('characters.json', 'r', encoding='utf-8') as f:
    characters = json.load(f)

character_map = {char['id']: char for char in characters}
current_character_id = list(character_map.keys())[0]

# UI表示を更新する関数
def change_character(character_id):
    global current_character_id
    current_character_id = character_id
    selected_character = character_map[character_id]
    return {
        title_label: gr.update(value=f"# {selected_character['name']} AIチャットボット"),
        description_label: gr.update(value=f"{selected_character['name']}と楽しくおしゃべりできるAIチャットボットです.")
    }

# チャット生成ロジック
async def chat_with_ollama(message, history):
    try:
        selected_character = character_map[current_character_id]
        messages = [{'role': 'system', 'content': selected_character['system_prompt']}]
        
        # 履歴の再構築
        for human_message, ai_message in history:
            # AIのメッセージ（辞書型）からテキストを抽出
            if isinstance(ai_message, dict):
                ai_text = ai_message.get("text", "")
            else:
                ai_text = ai_message
            
            messages.append({'role': 'user', 'content': human_message})
            messages.append({'role': 'assistant', 'content': ai_text})
            
        messages.append({'role': 'user', 'content': message})

        full_response = ""
        # 4.x系での一貫性のための辞書形式yield
        yield {"text": "考え中なのだ...", "files": []}
        
        stream = ollama.chat(
            model=selected_character['llm_model'],
            messages=messages,
            stream=True
        )
        
        for chunk in stream:
            content = ""
            if 'message' in chunk and 'content' in chunk['message']:
                content = chunk['message']['content']
            elif 'content' in chunk:
                content = chunk['content']
            
            full_response += content
            yield {"text": full_response, "files": []}

        # 音声生成
        audio_path = generate_voice(full_response, selected_character)
        
        if audio_path:
            # 音声ファイルを添えて最終応答
            yield {"text": full_response, "files": [audio_path]}
        else:
            yield {"text": full_response, "files": []}

    except Exception as e:
        yield {"text": f"エラーが発生したのだ！: {e}", "files": []}

# 音声合成 (GPT-SoVITS api.py 連携版)
def generate_voice(text: str, character_config: dict):
    try:
        tts_api_url = "http://127.0.0.1:9880"
        tts_config = character_config.get("tts_config", {})
        ref_audio_path = tts_config.get("ref_audio_path")
        prompt_text = tts_config.get("prompt_text")

        if not ref_audio_path or not prompt_text:
            print(f"[{character_config['name']}] TTS設定が不完全です。")
            return None

        # 絶対パスに変換
        abs_ref_path = os.path.abspath(ref_audio_path)

        payload = {
            "refer_wav_path": abs_ref_path,
            "prompt_text": prompt_text,
            "prompt_language": "ja",
            "text": text,
            "text_language": "ja"
        }

        response = httpx.post(f"{tts_api_url}/", json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"TTS APIエラー: {response.status_code}")
            return None

        # 一時ファイルとして保存
        temp_audio_path = os.path.abspath(f"temp_audio_{character_config['id']}.wav")
        with open(temp_audio_path, "wb") as f:
            f.write(response.content)

        return temp_audio_path

    except Exception as e:
        print(f"音声生成エラー: {e}")
        return None

# 学習処理 (ディレクトリ名を GPT-SoVITS- に修正)
def start_training(character_id):
    if not character_id:
        yield "エラー: IDを入力してくれ。"
        return

    # あなたの環境に合わせたパス
    gpt_sovits_root = "/Users/taks/GPT-SoVITS-"
    s1_train_script = os.path.join(gpt_sovits_root, "s1_train.py")
    s2_train_script = os.path.join(gpt_sovits_root, "s2_train.py")
    
    log_output = []

    def run_command(command, description):
        log_output.append(f"--- {description} ---")
        yield "\n".join(log_output)
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True
        )
        for line in process.stdout:
            log_output.append(line.strip())
            yield "\n".join(log_output)
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"{description} failed")

    try:
        s1_command = ["python", s1_train_script, "-s", character_id, "-t", "-m", "-e", "-o", "4", "--epochs", "10"]
        yield from run_command(s1_command, "GPT学習")
        s2_command = ["python", s2_train_script, "-s", character_id, "-t", "-e", "-o", "4", "--epochs", "10"]
        yield from run_command(s2_command, "SoVITS学習")
        yield "\n".join(log_output) + "\n学習完了なのだ！"
    except Exception as e:
        yield f"エラー: {e}"

# スライス処理
def slice_audio(character_id, audio_file):
    if not character_id or not audio_file:
        return "エラー: IDとファイルを指定するのだ。"

    base_dir = f"dataset/{character_id}"
    raw_dir = os.path.join(base_dir, "raw")
    sliced_dir = os.path.join(base_dir, "sliced")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(sliced_dir, exist_ok=True)

    raw_audio_path = os.path.join(raw_dir, os.path.basename(audio_file.name))
    shutil.copy(audio_file.name, raw_audio_path)

    audio = AudioSegment.from_file(raw_audio_path)
    chunks = split_on_silence(audio, min_silence_len=300, silence_thresh=-40, keep_silence=100)

    for i, chunk in enumerate(chunks):
        chunk.export(os.path.join(sliced_dir, f"voice_{i}.wav"), format="wav")

    return f"スライス完了: {len(chunks)}個保存したぞ！"

# 文字起こし
def generate_transcription(character_id):
    if not character_id:
        return "エラー: IDを指定するのだ。"

    sliced_dir = f"dataset/{character_id}/sliced"
    metadata_path = f"dataset/{character_id}/metadata.list"

    if not os.path.exists(sliced_dir):
        return "先にスライスしてくれ。"

    model = whisper.load_model("base")

    with open(metadata_path, "w", encoding="utf-8") as f:
        files = sorted([fn for fn in os.listdir(sliced_dir) if fn.endswith(".wav")])
        for filename in files:
            filepath = os.path.abspath(os.path.join(sliced_dir, filename))
            result = model.transcribe(filepath, language="ja")
            text = result["text"].strip()
            f.write(f"{filepath}|{character_id}|ja|{text}\n")
    
    return f"文字起こし完了！ {metadata_path} を確認なのだ。"

# UI構築 (Gradio 4.x対応)
with gr.Blocks() as demo:
    with gr.Tab("チャット"):
        character_dropdown = gr.Dropdown(
            choices=[(char["name"], char["id"]) for char in characters],
            value=current_character_id,
            label="誰と話すのだ？",
            interactive=True
        )

        title_label = gr.Markdown(f"# {character_map[current_character_id]['name']} AIチャットボット")
        description_label = gr.Markdown(f"{character_map[current_character_id]['name']}とおしゃべりするのだ。")

        # chatbotコンポーネントを明示的に定義
        my_chatbot = gr.Chatbot(height=450)

        chat_interface = gr.ChatInterface(
            chat_with_ollama,
            chatbot=my_chatbot,
            textbox=gr.Textbox(placeholder="メッセージを入力するのだ！", container=False, scale=7),
        )

        character_dropdown.change(
            fn=change_character,
            inputs=character_dropdown,
            outputs=[title_label, description_label]
        )

    with gr.Tab("キャラクター追加"):
        char_id = gr.Textbox(label="キャラクターID")
        audio_up = gr.File(label="元音声(.wav)", file_types=[".wav"])
        btn_slice = gr.Button("1. スライス実行")
        btn_trans = gr.Button("2. 文字起こし実行")
        btn_train = gr.Button("3. 学習開始")
        log_out = gr.Textbox(label="ログ", interactive=False, lines=10)

        btn_slice.click(slice_audio, [char_id, audio_up], log_out)
        btn_trans.click(generate_transcription, [char_id], log_out)
        btn_train.click(start_training, [char_id], log_out)

if __name__ == "__main__":
    demo.launch()