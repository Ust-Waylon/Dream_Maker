import openai
import gradio as gr
import time
import datetime
import re
from prompt import video_system_content, music_system_content, video_greet_message, music_greet_message

from animatediff_pipeline import AnimateDiffPipeline
from musicgen_pipeline import MusicGenPipeline
from postprocess_pipeline import PostprocessPipeline

class communication_module:
    def __init__(self):
        self.stage = "communication about video"
        self.messages = []
        self.video_prompt = ""
        self.music_prompt = ""

        self.animatediff_pipeline = AnimateDiffPipeline()
        self.musicgen_pipeline = MusicGenPipeline()
        self.postprocess_pipeline = PostprocessPipeline()

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
            chatbot_type_instruction = gr.Markdown(
                '''
                ## Music generation model
                Answer the chatbot's serial question, and it will generate the Music prompt for you.
                The chatbot is a communication model, feel free to propose question or ask for its idea.
                '''
            )
        elif self.stage == "communication about music":
            self.music_prompt = re.findall(r'\[(.*?)\]', chatbot[-1][-1])[0]
            video_visible = True
            music_visible = True
            chatbot_type_instruction = gr.Markdown(
                '''
                ## Music generation model
                Answer the chatbot's serial question, and it will generate the Music prompt for you.
                The chatbot is a communication model, feel free to propose question or ask for its idea.
                '''
            )
        updated_video_Textbox = gr.Textbox(label="video prompt", value=self.video_prompt)
        updated_music_Textbox = gr.Textbox(label="music prompt", value=self.music_prompt)
        updated_video_button = gr.Button(value="Generate video", visible=video_visible)
        updated_music_button = gr.Button(value="Generate music", visible=music_visible)
        return updated_video_Textbox, updated_music_Textbox, updated_video_button, updated_music_button, gr.Button(value="move to the next stage", visible=True), chatbot_type_instruction
    
    def postprocess_to_final_output(self, video_id_list, music_id):
        self.postprocess_pipeline.set_source_path(self.animatediff_pipeline, self.musicgen_pipeline)
        self.postprocess_pipeline.postprocess_video(video_id_list)
        self.postprocess_pipeline.postprocess_music(music_id)
        self.postprocess_pipeline.combine_video_music()
        return gr.Video(label="Merged output", value=self.postprocess_pipeline.output_path + "final_output.mp4", visible=True)
    
    def restart(self):
        self.animatediff_pipeline.restart()
        self.musicgen_pipeline.restart()
        self.postprocess_pipeline.restart()
        self.stage = "communication about video"
        self.messages = []
        self.video_prompt = ""
        self.music_prompt = ""

        # renew all the gradio items
        # remember to change the gradio items here if there is any change to them
        cm.init_messages(video_system_content)

        video_greet_message = """
        Hi, this is Dream-maker.
        Tell me anything, and I will turn your dream into an amazing video.
        """

        new_chatbot = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, video_greet_message]])
        new_msg = gr.Textbox(label="Input")

        new_export_prompt_btn = gr.Button(value = "Export prompt")
        new_move_to_next_stage_btn = gr.Button(value = "move to the next stage", visible=False)

        new_video_prompt_textbox = gr.Textbox(label="video prompt", lines=2, max_lines=2)
        new_generate_video_btn = gr.Button(value = "Generate video", visible=False)
        new_music_prompt_textbox = gr.Textbox(label="music prompt", lines=2, max_lines=2)
        new_generate_music_btn = gr.Button(value = "Generate music", visible=False)

        new_show_video_id = gr.Dropdown(label="Select a video", value=1, choices=[i for i in range(1,self.animatediff_pipeline.num_samples+1)], interactive=True)
        new_show_music_id = gr.Dropdown(label="Select a music", value=1, choices=[i for i in range(1,self.musicgen_pipeline.num_samples+1)], interactive=True)
        new_generated_video = gr.Video(label="Generated video", value=None, visible=True)
        new_generated_music = gr.Audio(label="Generated music", value=None, visible=True)

        new_selected_video_id = gr.CheckboxGroup([i for i in range(1,self.animatediff_pipeline.num_samples+1)], label="Select videos for final output")
        new_selected_music_id = gr.Radio([i for i in range(1,self.musicgen_pipeline.num_samples+1)], label="Select music for final output")
        
        new_btn_merge = gr.Button(value = "Merge generated video and music")
        new_merged_output = gr.Video(label="Merged output", visible=False)

        new_btn_evaluation = gr.Button(value="move on to the system evaluation!", visible=False)
        
        return_list = [new_chatbot, new_msg, 
                       new_export_prompt_btn, new_move_to_next_stage_btn, 
                       new_video_prompt_textbox, new_generate_video_btn, 
                       new_music_prompt_textbox, new_generate_music_btn, 
                       new_show_video_id, new_show_music_id, 
                       new_generated_video, new_generated_music, 
                       new_selected_video_id, new_selected_music_id, 
                       new_btn_merge, new_merged_output, new_btn_evaluation]

        print("commnication module restarted")

        return return_list


if __name__ == "__main__":

    cm = communication_module()
    
    # build an interface using gradio
    with gr.Blocks() as demo:

        cm.init_messages(video_system_content)
        
        gr.Markdown(
        """
        # Dream-maker Demo 
        Type in to chat with our chatbot.
        """)

        chatbot_type_instruction = gr.Markdown(
            '''
            ## Video generation model
            Answer the chatbot's serial questions, and it will generate the video prompt for you.

            The chatbot is a communication model, feel free to propose questions or ask for its idea.
            '''
        )
        
        video_greet_message = """
        Hi, I am a Dream-maker.
        Tell me anything, and I will turn your dream into an amazing video.
        """

        cm.append_assistant_message(cm.messages, video_greet_message)
        
        # Chatbot for video
        chatbot = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, video_greet_message]])
        msg = gr.Textbox(label="Input")
        
        msg.submit(cm.respond, [msg, chatbot], [msg, chatbot])

        # Click to generate video and switch to music chatbot
        with gr.Row():
            with gr.Column(scale=3):
                export_prompt_btn = gr.Button(value = "Export prompt")
                move_to_next_stage_btn = gr.Button(value = "move to the next stage", visible=False)
            with gr.Column(scale=1):
                restart_btn = gr.Button(value = "Restart")

        move_to_next_stage_btn.click(cm.move_to_next_stage, inputs = [chatbot], outputs = [chatbot])

        gr.Markdown(
            '''
            If you are not satisfied with the generated prompt, you could manually change them in the prompt textbox before passing them into the generation model.
            
            Click the generate button beneath the prompt box to generate video or music, there will be 10 samples in a batch and it would take some time to finish.
            '''
        )

        with gr.Row():
            
            with gr.Column():
                video_prompt_textbox = gr.Textbox(label="video prompt", lines=2, max_lines=2)
                generate_video_btn = gr.Button(value = "Generate video", visible=False)
            with gr.Column():
                music_prompt_textbox = gr.Textbox(label="music prompt", lines=2, max_lines=2)
                generate_music_btn = gr.Button(value = "Generate music", visible=False)

        export_prompt_btn.click(cm.export_prompt, inputs = [chatbot], 
                                outputs = [video_prompt_textbox, music_prompt_textbox, generate_video_btn, generate_music_btn, move_to_next_stage_btn, chatbot_type_instruction])
        

        gr.Markdown(
        """
        ## Generated video and background music
        """
        )

        video_id_list = [i for i in range(1,cm.animatediff_pipeline.num_samples+1)]
        music_id_list = [i for i in range(1,cm.musicgen_pipeline.num_samples+1)]
        gr.Markdown('''
            - After finising generating the outputs, they are shown below. You can check the output one-by-one by selecting the dropdown menu above.      
            - You may select **5** videos and **5** music that suits your expectation the most, by simply checking the below indexes.
            - You could play them directly or save them into your local machine by right-clicking on them.
        ''')
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
            Click the merge button and the 5 individual clips of videos would be merged into one single output. Have fun!
            """
        )
        with gr.Row():
            seleted_video_id = gr.CheckboxGroup(video_id_list, label="Select videos for final output")
            seleted_music_id = gr.Radio(music_id_list, label="Select music for final output")
        btn_merge = gr.Button(value = "Merge generated video and music")
        merged_output = gr.Video(label="Merged output", visible=False)

        btn_merge.click(cm.postprocess_to_final_output, inputs = [seleted_video_id, seleted_music_id], outputs = merged_output)

        btn_evaluation = gr.Button(value="move on to the system evaluation", visible=False)

        evaluation_confirm_choices = ["Yes", "No"]
        with gr.Row():
            evaluation_confirm_1 = gr.Radio(evaluation_confirm_choices, label="Do you want to evaluate the performance of the Dream-maker?", visible=False)
            evaluation_confirm_2 = gr.Radio(evaluation_confirm_choices, label="Would you grant us permission to collect your evaluation results?", visible=False)

        evaluation_title_value = """
        ## System Evaluation
        Please evaluate the performance of the Dream-maker system.
        """
        evaluation_title = gr.Markdown(value=evaluation_title_value, visible=True)

        # evaluation_choices = ["Terrible", "Bad", "Okay", "Good", "Excellent"]
        # evaluation_choices = ["Completely Disagree", "Disagree", "Neutral", "Agree", "Completely Agree"]
        # evaluation_choices = ["Completely no", "No", "Neutral", "Yes", "Completely yes"]
        # evaluation_choices = ["No", "Sometimes yes, sometimes no", "Yes"]

        # Part 1: Evaluate the performance of the communication system
        evaluation_subtitle_1_value = """
        ### Evaluation Part 1: Evaluate the performance of the communication system
        """
        evaluation_subtitle_1 = gr.Markdown(value=evaluation_subtitle_1_value, visible=True)

        evaluation_1_1 = gr.Markdown(value="#### 1.1: About questioning", visible=True)
        evaluation_choices = ["No", "Sometimes yes, sometimes no", "Yes"]
        evaluation_1_1_1 = gr.Radio(evaluation_choices, label="Did the communication module ask questions clearly and politely?", visible=True)
        evaluation_1_1_2 = gr.Radio(evaluation_choices, label="Are the questions directly related to the elements needed for video generation?", visible=True)
        evaluation_choices = ["No", "Yes"]
        evaluation_1_1_3 = gr.Radio(evaluation_choices, label="Are there any repetitive questions?", visible=True)

        evaluation_1_2 = gr.Markdown(value="#### 1.2: About prompt generation", visible=True)
        evaluation_choices = ["No", "Yes"]
        evaluation_1_2_1 = gr.Radio(evaluation_choices, label="Does the communication module comprehensively integrate valid information from user's responses into the prompt for video generation?", visible=True)
        evaluation_1_2_2 = gr.Radio(evaluation_choices, label="Does the communication module comprehensively integrate valid information from user's responses into the prompt for music generation?", visible=True)

        # Part 2: Evaluate the performance of the video generation
        evaluation_subtitle_2_value = """
        ### Evaluation Part 2: Evaluate the performance of the video generation
        """
        evaluation_subtitle_2 = gr.Markdown(value=evaluation_subtitle_2_value, visible=True)

        evaluation_2_1 = gr.Markdown(value="#### 2.1: About video quality", visible=True)
        evaluation_2_2 = gr.Markdown(value="#### 2.2: About prompt alignment", visible=True)

        # Part 3: Evaluate the performance of the music generation
        evaluation_subtitle_3_value = """
        ### Evaluation Part 3: Evaluate the performance of the music generation
        """
        evaluation_subtitle_3 = gr.Markdown(value=evaluation_subtitle_3_value, visible=True)

        evaluation_3_1 = gr.Markdown(value="#### 3.1: About music quality", visible=True)
        evaluation_3_2 = gr.Markdown(value="#### 3.2: About prompt alignment", visible=True)


        evaluation_confirm_3 = gr.Radio(evaluation_confirm_choices, label="Would you grant us permission to save the music video that you just generated by Dream-maker for further analysis?", visible=False)

        item_list = [chatbot, msg, 
                     export_prompt_btn, move_to_next_stage_btn, 
                     video_prompt_textbox, generate_video_btn, 
                     music_prompt_textbox, generate_music_btn, 
                     show_video_id, show_music_id, 
                     generated_video, generated_music, 
                     seleted_video_id, seleted_music_id, 
                     btn_merge, merged_output, btn_evaluation]
        restart_btn.click(cm.restart, outputs = item_list)
        
    demo.queue()
    demo.launch(max_threads=40)
    