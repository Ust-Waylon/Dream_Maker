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

from animatediff.models.unet import UNet3DConditionModel
from animatediff.pipelines.pipeline_animation import AnimationFreeInitPipeline
from animatediff.utils.util import save_videos_grid
from animatediff.utils.util import load_weights
from diffusers.utils.import_utils import is_xformers_available

from einops import rearrange, repeat

import csv, pdb, glob
import math
from pathlib import Path
from diffusers.training_utils import set_seed


def main(args):
    *_, func_args = inspect.getargvalues(inspect.currentframe())
    func_args = dict(func_args)
    
    time_str = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    savedir = f"outputs/{Path(args.config).stem}-{time_str}"
    os.makedirs(savedir)

    config  = OmegaConf.load(args.config)
    samples = []
    
    sample_idx = 0

    # set global seed
    set_seed(42)

    for model_idx, (config_key, model_config) in enumerate(list(config.items())):
        
        motion_modules = model_config.motion_module
        motion_modules = [motion_modules] if isinstance(motion_modules, str) else list(motion_modules)
        for motion_module in motion_modules:
            inference_config = OmegaConf.load(model_config.get("inference_config", args.inference_config))

            ### >>> create validation pipeline >>> ###
            tokenizer    = CLIPTokenizer.from_pretrained(args.pretrained_model_path, subfolder="tokenizer")
            text_encoder = CLIPTextModel.from_pretrained(args.pretrained_model_path, subfolder="text_encoder")
            vae          = AutoencoderKL.from_pretrained(args.pretrained_model_path, subfolder="vae")            
            unet         = UNet3DConditionModel.from_pretrained_2d(args.pretrained_model_path, subfolder="unet", unet_additional_kwargs=OmegaConf.to_container(inference_config.unet_additional_kwargs))

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
                width               = args.W,
                height              = args.H,
                video_length        = args.L,
                filter_params       = model_config.filter_params,
            )
            # -------------------------------------------------------------------------------

            prompts = list(model_config.prompt) * args.repeat_times if len(model_config.prompt) == 1 else model_config.prompt
            n_prompts    = list(model_config.n_prompt) * len(prompts) if len(model_config.n_prompt) == 1 else model_config.n_prompt
            
            random_seeds = model_config.get("seed", [-1])
            random_seeds = [random_seeds] if isinstance(random_seeds, int) else list(random_seeds)
            random_seeds = random_seeds * len(prompts) if len(random_seeds) == 1 else random_seeds
            
            config[config_key].random_seed = []
            for prompt_idx, (prompt, n_prompt, random_seed) in enumerate(zip(prompts, n_prompts, random_seeds)):
                
                # manually set random seed for reproduction
                # if random_seed != -1: torch.manual_seed(random_seed)
                if random_seed != -1: set_seed(random_seed)
                else: torch.seed()
                config[config_key].random_seed.append(torch.initial_seed())
                
                print(f"current seed: {torch.initial_seed()}")
                print(f"sampling {prompt} ...")
                save_prompt = "-".join((prompt.replace("/", "").split(" ")[:10]))
                
                sample = pipeline(
                    prompt,
                    negative_prompt     = n_prompt,
                    num_inference_steps = model_config.steps,
                    guidance_scale      = model_config.guidance_scale,
                    width               = args.W,
                    height              = args.H,
                    video_length        = args.L,
                    num_iters = args.num_iters,
                    use_fast_sampling = args.use_fast_sampling,
                    save_intermediate = args.save_intermediate,
                    save_dir = f"{savedir}/sample/intermediate",
                    save_name = f"{sample_idx}-{save_prompt}",
                    use_fp16            = args.use_fp16
                ).videos
                samples.append(sample)

                save_videos_grid(sample, f"{savedir}/sample/{sample_idx}-{save_prompt}.gif")
                print(f"save to {savedir}/sample/{save_prompt}.gif")
                
                sample_idx += 1

    samples = torch.concat(samples)
    save_videos_grid(samples, f"{savedir}/sample.gif", n_rows=4)

    OmegaConf.save(config, f"{savedir}/config.yaml")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--pretrained_model_path", type=str, default="models/StableDiffusion/stable-diffusion-v1-5",)
    parser.add_argument("--pretrained_model_path", type=str, default="/data1/wtanae/AnimateDiff/models/StableDiffusion/stable-diffusion-v1-5",)
    parser.add_argument("--inference_config",      type=str, default="configs/inference/inference-v1.yaml")    
    parser.add_argument("--config",                type=str, required=True)
    
    parser.add_argument("--L", type=int, default=16 )
    parser.add_argument("--W", type=int, default=512)
    parser.add_argument("--H", type=int, default=512)

    parser.add_argument("--repeat_times", type=int, default=10)

    parser.add_argument("--num_iters", type=int, default=5, help="number of sampling iterations, no freeinit when num_iters=1")
    parser.add_argument("--use_fast_sampling", action='store_true')
    parser.add_argument("--save_intermediate", action='store_true')

    parser.add_argument("--use_fp16", action='store_true')

    args = parser.parse_args()
    main(args)
