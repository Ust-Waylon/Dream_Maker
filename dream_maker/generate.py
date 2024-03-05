import time
import torchaudio
import os
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

output_dir = "/project/t3_wtanae/communication_module/outputs"

if __name__ == "__main__":

    num_samples = 5

    print("start loading MusicGen")
    model = MusicGen.get_pretrained('facebook/musicgen-large')
    model.set_generation_params(duration=11)  # generate 11 seconds.
    wav = model.generate_unconditional(4)    # generates 4 unconditional audio samples
    print("MusicGen loaded")

    while True:
        with open('status.txt', 'r') as file:
            status = file.read()

        if status == "K":
            break
        # if status.txt is T (True), then generate audio with prompt
        if status == "T":
            with open('prompt.txt', 'r') as file:
                txt_file = file.read()
            if txt_file != "":
                time_and_prompt = txt_file.split("\n")
                timestamp = time_and_prompt[0]
                prompt = time_and_prompt[1]
                save_prompt = "-".join((prompt.replace("/", "").split(" ")[:10]))
                
                for i in range(num_samples):
                    print(f"generating the {i + 1}th sample")
                    wav = model.generate([prompt])  # generates 5 samples.

                    # make directory
                    directory = output_dir + f'/MusicGen_{timestamp}'
                    if not os.path.exists(directory):
                        os.mkdir(directory)

                    # Will save under {idx}-{save_prompt}.wav, with loudness normalization at -14 db LUFS.
                    audio_write(directory + f'/{i}-{save_prompt}', wav[0].cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)
                    print(f"output audio saved as {directory}/{i}-{save_prompt}.wav")
        
                # change status.txt to F (False)
                with open('status.txt', 'w') as file:
                    file.write("F")
                # change prompt.txt to ""
                with open('prompt.txt', 'w') as file:
                    file.write("")
        
        time.sleep(1)