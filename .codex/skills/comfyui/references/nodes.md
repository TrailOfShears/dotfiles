# ComfyUI Common Node Types

## Loaders
| Node | Key Inputs | Outputs |
|------|-----------|---------|
| CheckpointLoaderSimple | ckpt_name | MODEL, CLIP, VAE |
| LoraLoader | model, clip, lora_name, strength_model, strength_clip | MODEL, CLIP |
| VAELoader | vae_name | VAE |
| CLIPLoader | clip_name | CLIP |
| ControlNetLoader | control_net_name | CONTROL_NET |

## Conditioning
| Node | Key Inputs | Outputs |
|------|-----------|---------|
| CLIPTextEncode | text, clip | CONDITIONING |
| ControlNetApply | conditioning, control_net, image, strength | CONDITIONING |

## Latent
| Node | Key Inputs | Outputs |
|------|-----------|---------|
| EmptyLatentImage | width, height, batch_size | LATENT |
| VAEEncode | pixels, vae | LATENT |
| VAEDecode | samples, vae | IMAGE |
| LatentUpscale | samples, upscale_method, width, height, crop | LATENT |

## Samplers
| Node | Key Inputs |
|------|-----------|
| KSampler | model, positive, negative, latent_image, seed, steps, cfg, sampler_name, scheduler, denoise |
| KSamplerAdvanced | add_noise, noise_seed, steps, cfg, sampler_name, scheduler, start_at_step, end_at_step |

## Image
| Node | Key Inputs | Outputs |
|------|-----------|---------|
| LoadImage | image | IMAGE, MASK |
| SaveImage | images, filename_prefix | — |
| ImageScale | image, upscale_method, width, height, crop | IMAGE |
| ImageUpscaleWithModel | upscale_model, image | IMAGE |

## Sampler Names
`euler`, `euler_ancestral`, `heun`, `dpm_2`, `dpm_2_ancestral`, `lms`, `dpm_fast`, `dpm_adaptive`, `dpmpp_2s_ancestral`, `dpmpp_sde`, `dpmpp_2m`, `dpmpp_2m_sde`, `ddim`, `uni_pc`

## Schedulers
`normal`, `karras`, `exponential`, `sgm_uniform`, `simple`, `ddim_uniform`
