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

def change_to_video(msg, chatbot_1):
    print("change to video")
    # print(msg)
    print(chatbot_1)
    print(chatbot_1[-1][-1])
    
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
        
        chatbot_1 = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, greet_message]])
        msg_1 = gr.Textbox(label="Input")
        
        msg_1.submit(respond, [msg_1, chatbot_1], [msg_1, chatbot_1])
        btn = gr.Button(value = "Generate Video")
        btn.click(change_to_video, inputs = chatbot_1)
        gr.Markdown(
        """
        ## Generated video
        """
        )
        with gr.Row():
            gr.Video()
            gr.Video()
        
        chatbot_2 = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, music_greet_message]], render = False)
        msg_2 = gr.Textbox(label="Input", render = False)
        
        msg_2.submit(respond, [msg_2, chatbot_2], [msg_2, chatbot_2])
        
    demo.launch()
    