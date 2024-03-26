import re
import os
import time
import datetime
import gradio as gr

class MusicGenPipeline:
    def __init__(self):
        self.musicgen_path = "/project/t3_wtanae/audiocraft/dream_maker"
        self.output_dir = "outputs"

        self.savedir = ""
        self.save_prompt = ""

        self.num_samples = 5

    def generate_music(self, prompt):
        print("music generation start")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        savedir = f"outputs/MusicGen_{timestamp}"
        os.makedirs(savedir)

        # add timestamp and prompt to prompt.txt
        with open(f'{self.musicgen_path}/prompt.txt', 'w') as file:
            file.write(f"{timestamp}\n{prompt}")
        # change status.txt to T
        with open(f'{self.musicgen_path}/status.txt', 'w') as file:
            file.write("T")

        save_prompt = "-".join((prompt.replace("/", "").split(" ")[:10]))

        self.savedir = savedir
        self.save_prompt = save_prompt

        return savedir, save_prompt
    
    def generate_music_for_app(self, textbox, progress = gr.Progress()):
        prompt = textbox
        print("music prompt: ", prompt)
        savedir, save_prompt = self.generate_music(prompt)
    
    def switch_show_music(self, show_music_id):
        print("switch showing music: ", show_music_id)
        return gr.Audio(value=f"{self.savedir}/{show_music_id-1}-{self.save_prompt}.wav", visible=True)
    
    def check_generation_progress(self):
        for i in range(self.num_samples):
            if not os.path.exists(f"{self.savedir}/{i}-{self.save_prompt}.wav"):
                break
        return i
    
    def track_generation_progress(self, progress=gr.Progress()):
        # wait for savedir update
        time.sleep(3)
        # track generation progress
        i = 0
        progress_step = 1 / self.num_samples
        progress(0, f"generating the 1st sample")
        while self.check_generation_progress() < self.num_samples - 1:
            if i < self.check_generation_progress():
                i = self.check_generation_progress()
                progress(progress_step * i, f"generating the {i+1}th sample")
            time.sleep(0.5)
        return gr.Audio(label="Generated music", value=f"{self.savedir}/0-{self.save_prompt}.wav", visible=True)
    
    def restart(self):
        self.savedir = ""
        self.save_prompt = ""
        print("musicgen pipeline restarted")