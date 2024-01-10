import openai
import gradio as gr
import time
import re
from prompt import video_system_content, music_system_content, video_greet_message, music_greet_message

from animatediff_pipeline import AnimateDiffPipeline # comment this line for frontend testing

def init_messages(system_content):
    return [
        {"role": "system", "content": system_content}
    ]

def reset_messages(messages, system_content):
    messages.clear()
    messages.append({"role": "system", "content": system_content})

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

def change_to_music(chatbot):
    print("change to music chatbot")
    video_prompt = re.findall(r'\[(.*?)\]', chatbot[-1][-1])
    reset_messages(messages, music_system_content(video_prompt))
    print("messages: ", messages)
    return gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, music_greet_message(video_prompt)]])


if __name__ == "__main__":


    animatediff_pipeline = AnimateDiffPipeline()
    
    # build an interface using gradio
    with gr.Blocks() as demo:
        messages = init_messages(video_system_content)
        
        gr.Markdown(
        """
        # Dream-maker Demo
        Type to chat with our chatbot.
        """)
        
        video_greet_message = """
        Hi, this is Dream-maker.
        Tell me anything, and I will turn your dream into an amazing video.
        """

        append_assistant_message(messages, video_greet_message)
        
        # Chatbot for video
        chatbot = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, video_greet_message]])
        msg = gr.Textbox(label="Input")
        
        msg.submit(respond, [msg, chatbot], [msg, chatbot])

        # Click to generate video and switch to music chatbot
        btn = gr.Button(value = "Generate and move to the next stage")
        btn.click(change_to_music, inputs = chatbot, outputs = chatbot)
        
        gr.Markdown(
        """
        ## Generated video and background music
        """
        )

        video_id_list = [1,2,3,4,5]
        music_id_list = [1,2,3,4,5]

        with gr.Row():
            with gr.Column():
                show_video_id = gr.Dropdown(label="Select a video", choices=video_id_list, interactive=True)
                generated_video = gr.Video(label="Generated video")
            with gr.Column():
                show_music_id = gr.Dropdown(label="Select a music", choices=music_id_list, interactive=True)
                generated_music = gr.Audio(label="Generated music")

        btn.click(fn = animatediff_pipeline.generate_video_for_app, inputs = [chatbot], outputs = generated_video)
        show_video_id.change(fn = animatediff_pipeline.switch_show_video, inputs = show_video_id, outputs = generated_video)
                
        gr.Markdown(
            """
            ## Get the final output
            """
        )
        with gr.Row():
            seleted_video_id = gr.CheckboxGroup(video_id_list, label="Select videos for final output")
            seleted_music_id = gr.CheckboxGroup(music_id_list, label="Select music for final output")
        btn_merge = gr.Button(value = "Merge generated video and music")
        gr.Video(label="Merged output")
        
    demo.launch(share=True)
    