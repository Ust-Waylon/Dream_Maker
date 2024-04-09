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
        return gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, music_greet_message(self.video_prompt)]]), gr.Button(value="move to the next stage", visible=False)
    
    def export_prompt(self, chatbot):
        if self.stage == "communication about video":
            self.video_prompt = re.findall(r'\[(.*?)\]', chatbot[-1][-1])[0]
            video_visible = True
            music_visible = False
            # chatbot_type_instruction = gr.Markdown(
            #     '''
            #     ## Music generation model
            #     Answer the chatbot's serial question, and it will generate the Music prompt for you.
            #     The chatbot is a communication model, feel free to propose question or ask for its idea.
            #     '''
            # )
        elif self.stage == "communication about music":
            self.music_prompt = re.findall(r'\[(.*?)\]', chatbot[-1][-1])[0]
            video_visible = True
            music_visible = True
            # chatbot_type_instruction = gr.Markdown(
            #     '''
            #     ## Music generation model
            #     Answer the chatbot's serial question, and it will generate the Music prompt for you.
            #     The chatbot is a communication model, feel free to propose question or ask for its idea.
            #     '''
            # )
        updated_video_Textbox = gr.Textbox(label="video prompt", value=self.video_prompt)
        updated_music_Textbox = gr.Textbox(label="music prompt", value=self.music_prompt)
        updated_video_button = gr.Button(value="Generate video", visible=video_visible)
        updated_music_button = gr.Button(value="Generate music", visible=music_visible)
        return updated_video_Textbox, updated_music_Textbox, updated_video_button, updated_music_button, gr.Button(value="move to the next stage", visible=True)
    
    def postprocess_to_final_output(self, video_id_list, music_id):
        self.postprocess_pipeline.set_source_path(self.animatediff_pipeline, self.musicgen_pipeline)
        self.postprocess_pipeline.postprocess_video(video_id_list)
        self.postprocess_pipeline.postprocess_music(music_id)
        self.postprocess_pipeline.combine_video_music()
        return gr.Video(label="Merged output", value=self.postprocess_pipeline.output_folder + "/final_output.mp4", visible=True)
    
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

        # video_id_list = [i for i in range(1,self.animatediff_pipeline.num_samples+1)]
        # music_id_list = [i for i in range(1,self.musicgen_pipeline.num_samples+1)]
        # new_show_video_id = gr.Radio(video_id_list, label="Select a video", interactive=False)
        # new_show_music_id = gr.Radio(music_id_list, label="Select a music", interactive=False)
        new_show_video_id = gr.Dropdown(label="Select a video", value=1, choices=[i for i in range(1,self.animatediff_pipeline.num_samples+1)], interactive=True)
        new_show_music_id = gr.Dropdown(label="Select a music", value=1, choices=[i for i in range(1,self.musicgen_pipeline.num_samples+1)], interactive=True)
        new_generated_video = gr.Video(label="Generated video", value=None, visible=True)
        new_generated_music = gr.Audio(label="Generated music", value=None, visible=True)

        new_selected_video_id = gr.CheckboxGroup([i for i in range(1,self.animatediff_pipeline.num_samples+1)], label="Select videos for final output")
        new_selected_music_id = gr.Radio([i for i in range(1,self.musicgen_pipeline.num_samples+1)], label="Select music for final output")
        
        new_btn_merge = gr.Button(value = "Merge generated video and music")
        new_merged_output = gr.Video(label="Merged output", visible=False)

        # new_btn_evaluation = gr.Button(value="move on to the system evaluation!", visible=False)
        
        return_list = [new_chatbot, new_msg, 
                       new_export_prompt_btn, new_move_to_next_stage_btn, 
                       new_video_prompt_textbox, new_generate_video_btn, 
                       new_music_prompt_textbox, new_generate_music_btn, 
                       new_show_video_id, new_show_music_id, 
                       new_generated_video, new_generated_music, 
                       new_selected_video_id, new_selected_music_id, 
                       new_btn_merge, new_merged_output]

        print("commnication module restarted")

        return return_list

js = """
function createGradioAnimation() {
    var container = document.createElement('div');
    container.id = 'gradio-animation';
    container.style.fontSize = '2em';
    container.style.fontWeight = 'bold';
    container.style.textAlign = 'center';
    container.style.marginBottom = '20px';

    var text = 'Hi, this is Dream-maker!';
    for (var i = 0; i < text.length; i++) {
        (function(i){
            setTimeout(function(){
                var letter = document.createElement('span');
                letter.style.opacity = '0';
                letter.style.transition = 'opacity 0.5s';
                letter.innerText = text[i];

                container.appendChild(letter);

                setTimeout(function() {
                    letter.style.opacity = '1';
                }, 50);
            }, i * 200);
        })(i);
    }

    var text2 = 'Talk to me, and I will turn your dream into an amazing music video!';
    var container2 = document.createElement('div');
    container2.style.fontSize = '1.5em';
    container2.style.fontWeight = 'bold';
    container2.style.textAlign = 'center';
    container2.style.marginBottom = '20px';

    for (var j = 0; j < text2.length; j++) {
        (function(j){
            setTimeout(function(){
                var letter2 = document.createElement('span');
                letter2.style.opacity = '0';
                letter2.style.transition = 'opacity 0.5s';
                letter2.innerText = text2[j];

                container2.appendChild(letter2);

                setTimeout(function() {
                    letter2.style.opacity = '1';
                }, 50);
            }, j * 100 + (text.length + 1) * 200);
        })(j);
    }

    var gradioContainer = document.querySelector('.gradio-container');
    gradioContainer.insertBefore(container2, gradioContainer.firstChild);
    gradioContainer.insertBefore(container, gradioContainer.firstChild);

    return 'Animation created';
}
"""

if __name__ == "__main__":

    cm = communication_module()
    
    # build an interface using gradio
    with gr.Blocks(js = js) as demo:

        cm.init_messages(video_system_content)
        
        # gr.Markdown(
        # """
        # Talk to me, and I will turn your dream into an amazing music video!
        # """)

        gr.Markdown(
            '''
            ## Chatbox
            - You can chat with the Dream-maker through this chatbox. Press enter to send your message.
            - He would ask you a few questions about your preference and expectation.
            - If you have no idea for the questions' answer, feel free to ask him for his suggestion!
            - When he responds with a prompt (like "Here is my prompt: [...]"), then press the "Export prompt" button below the chatbox to export the prompt. 
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
            with gr.Column(scale=4):
                export_prompt_btn = gr.Button(value = "Export prompt")
            with gr.Column(scale=1):
                restart_btn = gr.Button(value = "Restart")
        move_to_next_stage_btn = gr.Button(value = "move to the next stage", visible=False)

        move_to_next_stage_btn.click(cm.move_to_next_stage, inputs = [chatbot], outputs = [chatbot, move_to_next_stage_btn])

        gr.Markdown(
            '''
            - Click the generate button below the prompt textbox to generate video or music.
            - After you click the button for video generation, it would take around 3 minutes to generate the video.
            - At the same time, you could click the "Move to the next stage" button to talk about your music preference with the Dream-maker in the same chatbox.
            - If you are not satisfied with the generated prompt, you could manually edit them in the prompt textbox before passing them into the generation model.
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
                                outputs = [video_prompt_textbox, music_prompt_textbox, generate_video_btn, generate_music_btn, move_to_next_stage_btn])
        

        gr.Markdown(
        """
        ## Generated video and background music
        """
        )

        video_id_list = [i for i in range(1,cm.animatediff_pipeline.num_samples+1)]
        music_id_list = [i for i in range(1,cm.musicgen_pipeline.num_samples+1)]
        gr.Markdown('''
            - After finising generating the outputs, they will be shown below. You can check the output one-by-one by selecting the index in the dropdown menu above.      
            - You could play them directly or save them into your local machine by clicking the download button on the top-right corner of the player.
        ''')

        # with gr.Row():
        #     with gr.Column():
        #         show_video_id = gr.Radio(video_id_list, label="Select a video", interactive=False)
        #     with gr.Column():
        #         show_music_id = gr.Radio(music_id_list, label="Select a music", interactive=False)

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
             - You need to select **5** videos and **1** music that best meet your expectations, by simply checking the corresponding indexes below.
             - Then click the "Merge generated video and music" button to merge the selected video and music into a final output.
             - You can save the final output to your local machine by clicking the download button on the top-right corner of the player.
            """
        )
        with gr.Row():
            seleted_video_id = gr.CheckboxGroup(video_id_list, label="Select 5 videos for final output")
            seleted_music_id = gr.Radio(music_id_list, label="Select 1 music for final output")
        btn_merge = gr.Button(value = "Merge generated video and music")
        merged_output = gr.Video(label="Merged output", visible=False)

        btn_merge.click(cm.postprocess_to_final_output, inputs = [seleted_video_id, seleted_music_id], outputs = merged_output)

        # btn_evaluation = gr.Button(value="move on to the system evaluation", visible=False)

        gr.Markdown(
            '''
            ## System evaluation
            We value your feedback, please click on this link (https://forms.gle/HJVZp5yQvf3hjaq76) and fill out a questionnarie and share your thoughts with us!
            '''
        )

        # evaluation_confirm = gr.Radio(evaluation_confirm_choices, label="Would you grant us permission to save the music video that you just generated by Dream-maker for further analysis?", visible=False)

        item_list = [chatbot, msg, 
                     export_prompt_btn, move_to_next_stage_btn, 
                     video_prompt_textbox, generate_video_btn, 
                     music_prompt_textbox, generate_music_btn, 
                     show_video_id, show_music_id, 
                     generated_video, generated_music, 
                     seleted_video_id, seleted_music_id, 
                     btn_merge, merged_output]
        restart_btn.click(cm.restart, outputs = item_list)
        
    demo.queue()
    demo.launch(max_threads=40)
    