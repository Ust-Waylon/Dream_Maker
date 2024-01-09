import openai
import gradio as gr
import time
from prompt import video_system_content, music_system_content
def init_messages(system_content):
    return [
        {"role": "system", "content": system_content}
    ]

def append_assistant_message(messages, assistant_content):
    messages.append({"role": "assistant", "content": assistant_content})

def append_user_message(messages, user_content):
    messages.append({"role": "user", "content": user_content})
    
def get_response(messages):
    openai.api_key = "9caacd23ebca451593bf09eda10b006f"
    openai.api_base = "https://hkust.azure-api.net"
    openai.api_type = "azure"
    openai.api_version = "2023-05-15"
    
    response = openai.ChatCompletion.create(
        # engine="gpt-35-turbo-16k",
        engine="gpt-4-32k",
        messages=messages
    )
    
    return response.choices[0].message.content

def respond(message, chat_history):
    append_user_message(messages, message)
    bot_message = get_response(messages)
    chat_history.append((message, bot_message))
    return "", chat_history

def change_to_video(chatbot):
    print("change to video")
    print(chatbot[-1][-1])
    music_greet_message = """
        Your video will be generated soon. Now tell me about your music preferences.
        How would you like your music? You can describe the style, mood, instruments, tempo, etc.
        """
    return gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, music_greet_message]])
    
    
    # print(msg)


if __name__ == "__main__":
    
    # build an interface using gradio
    with gr.Blocks() as demo:
        messages = init_messages(video_system_content)
        
        gr.Markdown(
        """
        # Dream-maker Demo for Video-generation
        Type to chat with our chatbot.
        """)
        
        greet_message = """
        Hi, this is Dream-maker.
        Tell me anything, and I will turn your dream into an amazing video.
        """

        music_greet_message = """
        Your video will be generated soon. Now tell me about your music preferences.
        How would you like your music? You can describe the style, mood, instruments, tempo, etc.
        """

        append_assistant_message(messages, greet_message)
        
        chatbot = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, greet_message]])
        msg = gr.Textbox(label="Input")
        
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        btn = gr.Button(value = "Generate Video")

        btn.click(change_to_video, inputs = chatbot, outputs = chatbot)
        gr.Markdown(
        """
        ## Generated video
        """
        )
        with gr.Row():
            gr.Video()
            gr.Video()
        
        
        
    demo.launch()
    