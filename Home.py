import openai
import gradio as gr
import time
from prompt import video_system_content, music_system_content

from animatediff_pipeline import AnimateDiffPipeline

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

    # for frontend testing, set use_animatediff to False
    use_animatediff = False

    W = 512
    H = 384
    L = 16
    num_samples = 5
    
    if use_animatediff:
        animatediff_pipeline = AnimateDiffPipeline()
    
    # build an interface using gradio
    with gr.Blocks() as demo:
        messages = init_messages(video_system_content)
        
        gr.Markdown(
        """
        # Dream-maker Demo for Video-generation
        Type to chat with our chatbot.
        """)
        
        video_greet_message = """
        Hi, this is Dream-maker.
        Tell me anything, and I will turn your dream into an amazing video.
        """

        music_greet_message = """
        Your video is now generating! Now let's talks about the background music!
        How would you like your music? You can describe the style, mood, instruments, tempo, etc.
        """

        append_assistant_message(messages, video_greet_message)
        
        # Chatbot for video
        chatbot = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, greet_message]])
        msg = gr.Textbox(label="Input")
        
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        # Click to generate video and switch to music chatbot
        btn = gr.Button(value = "Generate Video")

        btn.click(change_to_video, inputs = chatbot, outputs = chatbot)
        gr.Markdown(
        """
        ## Generated video and background music
        """
        )

        video_id_list = [1,2,3,4,5,6,7,8,9,10]
        music_id_list = [1,2,3,4,5]

        with gr.Row():
            with gr.Column():
                generated_video = gr.Video(label="Generated video")
                gr.Dropdown(label="Select a video", choices=video_id_list, interactive=True)
            with gr.Column():
                generated_music = gr.Audio(label="Generated music")
                gr.Dropdown(label="Select a music", choices=music_id_list, interactive=True)

        if use_animatediff:
            btn.click(fn = animatediff_pipeline.generate_video_for_app, inputs = [chatbot_1], outputs = generated_video)
        
    demo.launch()
    