import argparse
import datetime
import inspect
import os
from omegaconf import OmegaConf

import torch

import diffusers
from diffusers import AutoencoderKL, DDIMScheduler

from tqdm.auto import tqdm
from transformers import CLIPTextModel, CLIPTokenizer

from AnimateDiff.animatediff.models.unet import UNet3DConditionModel
from AnimateDiff.animatediff.pipelines.pipeline_animation import AnimationFreeInitPipeline
from AnimateDiff.animatediff.utils.util import save_videos_grid
from AnimateDiff.animatediff.utils.util import load_weights
from diffusers.utils.import_utils import is_xformers_available

from einops import rearrange, repeat

import csv, pdb, glob
import math
from pathlib import Path
from diffusers.training_utils import set_seed

def init_animatediff_pipeline():

    pretrained_model_path = "/data1/wtanae/AnimateDiff/models/StableDiffusion/stable-diffusion-v1-5"
    inference_config = "AnimateDiff/configs/inference/inference-v2.yaml"
    config = "AnimateDiff/configs/prompts/RealisticVision_v2.yaml"

    W = 512
    H = 384
    L = 16

    *_, func_args = inspect.getargvalues(inspect.currentframe())
    func_args = dict(func_args)
    
    model_config  = OmegaConf.load(config)

    # set global seed
    set_seed(42)
        
    motion_module = model_config.motion_module[0]

    inference_config = OmegaConf.load(inference_config)

    ### >>> create validation pipeline >>> ###
    tokenizer    = CLIPTokenizer.from_pretrained(pretrained_model_path, subfolder="tokenizer")
    text_encoder = CLIPTextModel.from_pretrained(pretrained_model_path, subfolder="text_encoder")
    vae          = AutoencoderKL.from_pretrained(pretrained_model_path, subfolder="vae")            
    unet         = UNet3DConditionModel.from_pretrained_2d(pretrained_model_path, subfolder="unet", unet_additional_kwargs=OmegaConf.to_container(inference_config.unet_additional_kwargs))

    if is_xformers_available(): unet.enable_xformers_memory_efficient_attention()
    else: assert False

    pipeline = AnimationFreeInitPipeline(
        vae=vae, text_encoder=text_encoder, tokenizer=tokenizer, unet=unet,
        scheduler=DDIMScheduler(**OmegaConf.to_container(inference_config.noise_scheduler_kwargs)),
    ).to("cuda")

    pipeline = load_weights(
        pipeline,
        # motion module
        motion_module_path         = motion_module,
        motion_module_lora_configs = model_config.get("motion_module_lora_configs", []),
        # image layers
        dreambooth_model_path      = model_config.get("dreambooth_path", ""),
        lora_model_path            = model_config.get("lora_model_path", ""),
        lora_alpha                 = model_config.get("lora_alpha", 0.8),
    ).to("cuda")

    # (freeinit) initialize frequency filter for noise reinitialization -------------
    pipeline.init_filter(
        width               = W,
        height              = H,
        video_length        = L,
        filter_params       = model_config.filter_params,
    )

    return pipeline, model_config

def generate_video(pipeline, prompt, n_prompt, model_config, W, H, L, num_samples):
    time_str = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    savedir = f"outputs/AnimateDiff_{time_str}"
    os.makedirs(savedir)

    print(f"sampling {prompt} ...")
    save_prompt = "-".join((prompt.replace("/", "").split(" ")[:10]))

    for sample_idx in range(num_samples):
        sample = pipeline(
                    prompt,
                    negative_prompt     = n_prompt,
                    num_inference_steps = model_config.steps,
                    guidance_scale      = model_config.guidance_scale,
                    width               = W,
                    height              = H,
                    video_length        = L,
                    num_iters = 1,
                    use_fast_sampling = False,
                    save_intermediate = False,
                    save_dir = f"{savedir}/sample/intermediate",
                    save_name = f"{0}-{save_prompt}",
                    use_fp16            = True
                ).videos
        
        save_videos_grid(sample, f"{savedir}/{sample_idx}-{save_prompt}.gif")
        print(f"save to {savedir}/{sample_idx}-{save_prompt}.gif")

    return savedir, save_prompt

if __name__ == "__main__":
    animatediff_pipeline, animatediff_model_config = init_animatediff_pipeline()

    W = 512
    H = 384
    L = 16

    num_samples = 10

    while True:
        prompt = input("Enter prompt: ")
        n_prompt = "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime, mutated hands and fingers:1.4), (deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, mutated, ugly, disgusting, amputation"
        savedir, save_prompt = generate_video(animatediff_pipeline, prompt, n_prompt, animatediff_model_config, W, H, L, num_samples)
