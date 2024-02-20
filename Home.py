import openai
import gradio as gr
import time
import datetime
import re
from prompt import video_system_content, music_system_content, video_greet_message, music_greet_message

from animatediff_pipeline import AnimateDiffPipeline # comment this line for frontend testing
from musicgen_pipeline import MusicGenPipeline # comment this line for frontend testing

class communication_module:
    def __init__(self):
        self.stage = "communication about video"
        self.messages = []
        self.video_prompt = ""
        self.music_prompt = ""

        self.animatediff_pipeline = AnimateDiffPipeline()
        self.musicgen_pipeline = MusicGenPipeline()

    def init_messages(self, system_content):
        self.messages = [{"role": "system", "content": system_content}]

    def append_assistant_message(self, messages, assistant_content):
        self.messages.append({"role": "assistant", "content": assistant_content})

    def append_user_message(self, messages, user_content):
        self.messages.append({"role": "user", "content": user_content})

    def get_response(self, messages):
        openai.api_key = "9caacd23ebca451593bf09eda10b006f"
        openai.api_base = "https://hkust.azure-api.net"
        openai.api_type = "azure"
        # openai.api_version = "2023-05-15"
        openai.api_version = "2023-12-01-preview"
        
        response = openai.ChatCompletion.create(
            # engine="gpt-35-turbo-16k",
            engine="gpt-4-32k",
            messages=messages
        )
        return response.choices[0].message.content

    def respond(self, message, chat_history):
        self.append_user_message(self.messages, message)
        bot_message = self.get_response(self.messages)
        chat_history.append((message, bot_message))
        return "", chat_history

    def move_to_next_stage(self, chatbot):
        if self.stage == "communication about video":
            self.stage = "communication about music"
        if self.stage == "communication about music":
            self.init_messages(music_system_content(self.video_prompt))
        return gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, music_greet_message(self.video_prompt)]])
    
    def export_prompt(self, chatbot):
        if self.stage == "communication about video":
            self.video_prompt = re.findall(r'\[(.*?)\]', chatbot[-1][-1])[0]
            video_visible = True
            music_visible = False
        elif self.stage == "communication about music":
            self.music_prompt = re.findall(r'\[(.*?)\]', chatbot[-1][-1])[0]
            video_visible = True
            music_visible = True
        updated_video_Textbox = gr.Textbox(label="video prompt", value=self.video_prompt)
        updated_music_Textbox = gr.Textbox(label="music prompt", value=self.music_prompt)
        updated_video_button = gr.Button(value="Generate video", visible=video_visible)
        updated_music_button = gr.Button(value="Generate music", visible=music_visible)
        return updated_video_Textbox, updated_music_Textbox, updated_video_button, updated_music_button, gr.Button(value="move to the next stage", visible=True)


if __name__ == "__main__":

    cm = communication_module()
    
    # build an interface using gradio
    with gr.Blocks() as demo:

        cm.init_messages(video_system_content)
        
        gr.Markdown(
        """
        # Dream-maker Demo
        Type to chat with our chatbot.
        """)
        
        video_greet_message = """
        Hi, this is Dream-maker.
        Tell me anything, and I will turn your dream into an amazing video.
        """

        cm.append_assistant_message(cm.messages, video_greet_message)
        
        # Chatbot for video
        chatbot = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, video_greet_message]])
        msg = gr.Textbox(label="Input")
        
        msg.submit(cm.respond, [msg, chatbot], [msg, chatbot])

        # Click to generate video and switch to music chatbot
        export_prompt_btn = gr.Button(value = "Export prompt")

        move_to_next_stage_btn = gr.Button(value = "move to the next stage", visible=False)
        move_to_next_stage_btn.click(cm.move_to_next_stage, inputs = [chatbot], outputs = [chatbot])

        with gr.Row():
            with gr.Column():
                video_prompt_textbox = gr.Textbox(label="video prompt", lines=2, max_lines=2)
                generate_video_btn = gr.Button(value = "Generate video", visible=False)
            with gr.Column():
                music_prompt_textbox = gr.Textbox(label="music prompt", lines=2, max_lines=2)
                generate_music_btn = gr.Button(value = "Generate music", visible=False)

        export_prompt_btn.click(cm.export_prompt, inputs = [chatbot], 
                                outputs = [video_prompt_textbox, music_prompt_textbox, generate_video_btn, generate_music_btn, move_to_next_stage_btn])
        

        gr.Markdown(
        """
        ## Generated video and background music
        """
        )

        video_id_list = [i for i in range(1,cm.animatediff_pipeline.num_samples+1)]
        music_id_list = [i for i in range(1,cm.musicgen_pipeline.num_samples+1)]

        with gr.Row():
            with gr.Column():
                show_video_id = gr.Dropdown(label="Select a video", value=1, choices=video_id_list, interactive=True)
            with gr.Column():
                show_music_id = gr.Dropdown(label="Select a music", value=1, choices=music_id_list, interactive=True)

        with gr.Row(equal_height=True):
            generated_video = gr.Video(label="Generated video", value=None, visible=True)
            generated_music = gr.Audio(label="Generated music", value=None, visible=True)

        generate_video_btn.click(fn = cm.animatediff_pipeline.generate_video_for_app, inputs = video_prompt_textbox)
        generate_video_btn.click(cm.animatediff_pipeline.track_generation_progress, outputs = generated_video)
        show_video_id.change(fn = cm.animatediff_pipeline.switch_show_video, inputs = show_video_id, outputs = generated_video)

        generate_music_btn.click(fn = cm.musicgen_pipeline.generate_music_for_app, inputs = music_prompt_textbox)
        generate_music_btn.click(cm.musicgen_pipeline.track_generation_progress, outputs = generated_music)
        show_music_id.change(fn = cm.musicgen_pipeline.switch_show_music, inputs = show_music_id, outputs = generated_music)
                
        gr.Markdown(
            """
            ## Get the final output
            """
        )
        with gr.Row():
            seleted_video_id = gr.CheckboxGroup(video_id_list, label="Select videos for final output")
            seleted_music_id = gr.Radio(music_id_list, label="Select music for final output")
        btn_merge = gr.Button(value = "Merge generated video and music")
        gr.Video(label="Merged output", visible=False)
        
    demo.queue(concurrency_count=4)
    demo.launch()
    