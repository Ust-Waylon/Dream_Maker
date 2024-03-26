import os
import datetime
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx, afx, transfx, concatenate, CompositeVideoClip, AudioFileClip

class PostprocessPipeline:
    def __init__(self):
        self.video_folder_path = ""
        self.video_save_prompt = ""
        self.video_duration = 0

        self.music_folder_path = ""
        self.music_save_prompt = ""

        self.ouput_folder = ""

    def set_source_path(self, video_pipeline, music_pipeline):
        self.video_folder_path = video_pipeline.savedir
        self.video_save_prompt = video_pipeline.save_prompt

        self.music_folder_path = music_pipeline.savedir
        self.music_save_prompt = music_pipeline.save_prompt

        # output folder is Final_output_{timestamp}
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        self.output_folder = f"outputs/Final_output_{timestamp}"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def postprocess_video(self, video_id_list):
        video_id_list = [int(video_id) for video_id in video_id_list]
        video_list = []
        for video_id in video_id_list:
            video = VideoFileClip(self.video_folder_path + f"/{video_id - 1}-{self.video_save_prompt}.mp4")
            video_list.append(video)

        # add transition effects
        video_list[0] = (CompositeVideoClip([video_list[0]]).crossfadein(0.5))
        video_list[1] = (CompositeVideoClip([video_list[1]]).crossfadein(0.2))
        video_list[2] = (CompositeVideoClip([video_list[2]]).crossfadein(0.2))
        video_list[3] = (CompositeVideoClip([video_list[3]]).crossfadein(0.2))
        video_list[4] = (CompositeVideoClip([video_list[4]]).crossfadein(0.2).crossfadeout(0.5))

        # concatenate video clips
        final_video = concatenate_videoclips(video_list, padding=-0.1, method="compose")
        self.video_duration = final_video.duration

        # write the video to the output path
        final_video.write_videofile(self.output_folder + f"/final_video.mp4")

    def postprocess_music(self, music_id):
        music_id = int(music_id)
        music = AudioFileClip(self.music_folder_path + f"/{music_id - 1}-{self.music_save_prompt}.wav")
        music = music.set_duration(self.video_duration)

        music = music.audio_fadein(2).audio_fadeout(2)

        music.write_audiofile(self.output_folder + f"/final_music.wav")

    def combine_video_music(self):
        video = VideoFileClip(self.output_folder + "/final_video.mp4")
        music = AudioFileClip(self.output_folder + "/final_music.wav")

        music = music.set_duration(video.duration)

        final_output = video.set_audio(music)
        final_output.write_videofile(self.output_folder + "/final_output.mp4", codec="libx264", audio_codec="aac")

    def restart(self):
        self.video_folder_path = ""
        self.video_save_prompt = ""
        self.video_duration = 0

        self.music_folder_path = ""
        self.music_save_prompt = ""

        self.output_folder = ""
        print("postprocess pipeline restarted")