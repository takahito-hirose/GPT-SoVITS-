
import gradio as gr
import ollama
import asyncio
import json

# キャラクター設定をロード
with open('characters.json', 'r', encoding='utf-8') as f:
    characters = json.load(f)

# キャラクターIDをキーとしてキャラクター情報をマッピング
character_map = {char['id']: char for char in characters}

# 現在選択されているキャラクターのIDを保持する変数
current_character_id = list(character_map.keys())[0] # デフォルトは最初のキャラクター

# キャラクター変更時の処理
def change_character(character_id):
    global current_character_id
    current_character_id = character_id
    selected_character = character_map[character_id]
    return {
        title_label: gr.Markdown(f"# {selected_character['name']} AIチャットボット"),
        description_label: gr.Markdown(f"{selected_character['name']}と楽しくおしゃべりできるAIチャットボットです."),
        chat_interface: gr.ChatInterface(fn=chat_with_ollama, chatbot=gr.Chatbot(height=400), textbox=gr.Textbox(placeholder=f"{selected_character['name']}に話しかけてみよう！", container=False, scale=7), title="", description="", theme="")
    }

# Ollama APIと連携するチャット関数
async def chat_with_ollama(message, history):
    try:
        selected_character = character_map[current_character_id]
        messages = [{'role': 'system', 'content': selected_character['system_prompt']}]
        for human_message, ai_message in history:
            messages.append({'role': 'user', 'content': human_message})
            messages.append({'role': 'assistant', 'content': ai_message})
        messages.append({'role': 'user', 'content': message})

        # Ollamaにリクエストを送信し、ストリーミングで応答を受け取る
        stream = ollama.chat(
            model=selected_character['llm_model'],
            messages=messages,
            stream=True
        )
        
        full_response = ""
        # 逐次応答を処理し、Gradioに表示するためにyieldする
        for chunk in stream:
            if chunk['done']:
                break
            full_response += chunk['content']
            yield full_response

    except Exception as e:
        # エラーハンドリング: Ollamaが起動していないなどのエラーを捕捉
        error_message = f"Ollamaが起動していないのだ！エラー: {e}"
        yield error_message

# 将来の音声合成用のプレースホルダー関数
def generate_voice(text: str):
    print(f"ここで音声を生成します: {text}")
    # ここに音声合成API連携のロジックを追加予定

# Gradio UIの構築
with gr.Blocks() as demo:
    character_dropdown = gr.Dropdown(
        choices=[(char["name"], char["id"]) for char in characters],
        value=current_character_id,
        label="キャラクター選択",
        interactive=True,
        scale=1
    )

    title_label = gr.Markdown(f"# {character_map[current_character_id]["name"]} AIチャットボット")
    description_label = gr.Markdown(f"{character_map[current_character_id]["name"]}と楽しくおしゃべりできるAIチャットボットです.")

    chat_interface = gr.ChatInterface(
        chat_with_ollama,
        chatbot=gr.Chatbot(height=400),
        textbox=gr.Textbox(placeholder=f"{character_map[current_character_id]["name"]}に話しかけてみよう！", container=False, scale=7),
        title="", # タイトルは動的に変更するため空に
        description="", # 説明も動的に変更するため空に
    )

    character_dropdown.change(
        fn=change_character,
        inputs=character_dropdown,
        outputs=[title_label, description_label, chat_interface] # chat_interfaceも更新対象に追加
    )

# Gradio UIを起動
if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="purple", secondary_hue="gray"))

# NOTE: Gradio 4.0以降、`gr.ChatInterface`や`gr.Blocks`のコンストラクタに`theme`引数を直接渡すのは非推奨となりました。
# `launch()`メソッドに渡すように変更しました。
# また、色の指定はGradioが認識できる文字列（"purple", "black", "gray"など）を使用する必要があります。
# カスタムカラーコード（"#4B0082"など）を使用する場合は、`gr.themes.builder`を使う必要がありますが、
# 今回は簡易的に文字列で指定しています。

