# communication_module
## Get started
### Install Animatediff
### Install audiocraft
### Install dependencies
```bash
conda activate animatediff
pip install openai==0.28
pip install moviepy
pip install gradio
```
### Specify the paths
### Run the code
Since we need to run the video generation model and the music generation model concurrently, two different terminals are needed.
```bash
# Terminal 1
conda activate audiocraft
cd audiocraft/dream_maker
python generate.py

# Terminal 2
conda activate animatediff
cd communication_module
python Home.py
```
Then you can play with the interface on the browser by clicking the link in the terminal.
```
...
Running on local URL:  http://127.0.0.1:7860
...
```
## Acknowledgements
Video generation model [AnimateDiff](https://github.com/guoyww/AnimateDiff).  
Music generation model [audiocraft](https://github.com/facebookresearch/audiocraft) - [MusicGen](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md) & [MAGNeT](https://github.com/facebookresearch/audiocraft/blob/main/docs/MAGNET.md).
