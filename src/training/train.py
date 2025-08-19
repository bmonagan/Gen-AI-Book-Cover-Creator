"""Main training script for the Goodreads book cover dataset using a diffusion model."""
# Standard library
import os
from pathlib import Path
import datetime

# Third-party libraries
import torch
import torch.nn.functional as F
from PIL import Image
from tqdm.auto import tqdm
from torchvision import transforms
import numpy as np

# Accelerate for distributed training and mixed precision
from accelerate import Accelerator
from accelerate import notebook_launcher

# Hugging Face libraries
from datasets import load_dataset
from diffusers.models.unets.unet_2d import UNet2DModel
from diffusers.schedulers.scheduling_ddpm import DDPMScheduler
from diffusers.pipelines.ddpm.pipeline_ddpm import DDPMPipeline
from diffusers.optimization import get_cosine_schedule_with_warmup
from diffusers.utils.pil_utils import make_image_grid
from huggingface_hub import create_repo, upload_folder

# Import local training configuration
import training_config

# Load the training configuration
config = training_config.TrainingConfig()

# Create a directory for the trained model
model_dir = Path("data/Generated/romantasy_bookcovers/models")
model_dir.mkdir(exist_ok=True)

# For use in naming models and sample images with the current date
date_str = datetime.datetime.now().strftime("%Y-%m-%d")

# Load the local dataset
# Images have been preprocessed and resized to 512x512 pixels(which will change to 128x128 later)
# Also ensured that the images are in RGB format
dataset = load_dataset(
    "imagefolder",
    data_dir="data/goodreads data/goodreads_covers_resized"
)
# Further processing the dataset
# Convert images to tensors and normalize them
preprocess = transforms.Compose(
    [
        transforms.Resize((config.image_size, config.image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5]),
    ]
)

def transform(examples):
    images = [preprocess(image.convert("RGB")) for image in examples["image"]]
    return {"images": images}

dataset.set_transform(transform)
train_dataloader = torch.utils.data.DataLoader(dataset["train"], batch_size=config.train_batch_size, shuffle=True)


resume_dir = model_dir / "epoch-99-step-30600-2025-08-17"

if resume_dir.exists():
    print(f"Resuming from checkpoint: {resume_dir}")
    model = UNet2DModel.from_pretrained(resume_dir / "unet")
else:
    # Common diffusers UNet2DModel configuration
    # This is a simplified version of the UNet2DModel configuration
    model = UNet2DModel(
        sample_size=config.image_size,  # the target image resolution
        in_channels=3,  # the number of input channels, 3 for RGB images
        out_channels=3,  # the number of output channels
        layers_per_block=2,  # how many ResNet layers to use per UNet block
        block_out_channels=(128, 128, 256, 256, 512, 512),  # the number of output channels for each UNet block
        down_block_types=(
            "DownBlock2D",  # a regular ResNet downsampling block
            "DownBlock2D",
            "DownBlock2D",
            "DownBlock2D",
            "AttnDownBlock2D",  # a ResNet downsampling block with spatial self-attention
            "DownBlock2D",
        ),
        up_block_types=(
            "UpBlock2D",  # a regular ResNet upsampling block
            "AttnUpBlock2D",  # a ResNet upsampling block with spatial self-attention
            "UpBlock2D",
            "UpBlock2D",
            "UpBlock2D",
            "UpBlock2D",
        )
    )
sample_image = dataset["train"][0]["images"].unsqueeze(0)

# Initialize the noise scheduler

noise_scheduler = DDPMScheduler(num_train_timesteps=1000)
noise = torch.randn(sample_image.shape)
timesteps = torch.LongTensor([50])
noisy_image = noise_scheduler.add_noise(sample_image, noise, timesteps)

Image.fromarray(((noisy_image.permute(0, 2, 3, 1) + 1.0) * 127.5).type(torch.uint8).numpy()[0])


# Optimizer and learning rate scheduler
optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
lr_scheduler = get_cosine_schedule_with_warmup(
    optimizer=optimizer,
    num_warmup_steps=config.lr_warmup_steps,
    num_training_steps=(len(train_dataloader) * config.num_epochs),
)

def evaluate(config, epoch, pipeline):
    # Make sure batch_size matches rows * cols
    num_images = config.eval_batch_size
    rows, cols = 4, 4
    num_images = rows * cols

    images = pipeline(
        batch_size=num_images,
        generator=torch.Generator(device='cpu').manual_seed(config.seed),
    ).images

    image_grid = make_image_grid(images, rows=rows, cols=cols)

    test_dir = os.path.join(config.output_dir, "samples")
    os.makedirs(test_dir, exist_ok=True)
    image_grid.save(f"{test_dir}/{epoch:04d}_{date_str}.png")
    # After generating images (assuming images is a list of PIL Images)
    arr = np.array(images[0])
    print(arr.min(), arr.max())


def train_loop(config, model, noise_scheduler, optimizer, train_dataloader, lr_scheduler):
    # Initialize accelerator and tensorboard logging
    accelerator = Accelerator(
        mixed_precision=config.mixed_precision,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        log_with="tensorboard",
        project_dir=os.path.join(config.output_dir, "logs"),
    )
    if accelerator.is_main_process:
        if config.output_dir is not None:
            os.makedirs(config.output_dir, exist_ok=True)
        if config.push_to_hub:
            repo_id = create_repo(
                repo_id=config.hub_model_id or Path(config.output_dir).name, exist_ok=True
            ).repo_id
        accelerator.init_trackers("train_example")

    # Prepare everything
    # There is no specific order to remember, you just need to unpack the
    # objects in the same order you gave them to the prepare method.
    model, optimizer, train_dataloader, lr_scheduler = accelerator.prepare(
        model, optimizer, train_dataloader, lr_scheduler
    )

    global_step = 0

    # Now you train the model
    for epoch in range(config.num_epochs):
        progress_bar = tqdm(total=len(train_dataloader), disable=not accelerator.is_local_main_process)
        progress_bar.set_description(f"Epoch {epoch}")

        for step, batch in enumerate(train_dataloader):
            clean_images = batch["images"]
            # Sample noise to add to the images
            noise = torch.randn(clean_images.shape, device=clean_images.device)
            bs = clean_images.shape[0]

            # Sample a random timestep for each image
            timesteps = torch.randint(
                0, noise_scheduler.config.num_train_timesteps, (bs,), device=clean_images.device,
                dtype=torch.int64
            )

            # Add noise to the clean images according to the noise magnitude at each timestep
            # (this is the forward diffusion process)
            noisy_images = noise_scheduler.add_noise(clean_images, noise, timesteps)

            with accelerator.accumulate(model):
                # Predict the noise residual
                noise_pred = model(noisy_images, timesteps, return_dict=False)[0]
                loss = F.mse_loss(noise_pred, noise)
                accelerator.backward(loss)

                if not torch.isfinite(loss):
                    print("NaN loss detected! Stopping training.")
                    return

                if accelerator.sync_gradients:
                    accelerator.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                lr_scheduler.step()
                optimizer.zero_grad()

            progress_bar.update(1)
            logs = {
                "loss": loss.detach().item(),
                "lr": lr_scheduler.get_last_lr()[0], 
                "step": global_step,  # A trailing comma is a good practice!
            }
            progress_bar.set_postfix(**logs)
            accelerator.log(logs, step=global_step)
            global_step += 1

        # After each epoch you optionally sample some demo images with evaluate() and save the model
        if accelerator.is_main_process:
            pipeline = DDPMPipeline(unet=accelerator.unwrap_model(model), scheduler=noise_scheduler)

            if (epoch + 1) % config.save_image_epochs == 0 or epoch == config.num_epochs - 1:
                evaluate(config, epoch, pipeline)

            if (epoch + 1) % config.save_model_epochs == 0 or epoch == config.num_epochs - 1:
                if config.push_to_hub:
                    upload_folder(
                        repo_id=repo_id,
                        folder_path=config.output_dir,
                        commit_message=f"Epoch {epoch}",
                        ignore_patterns=["step_*", "epoch_*"],
                    )
                else:
                    
                    pipeline.save_pretrained(model_dir / f"epoch-{epoch}-step-{global_step}-{date_str}")


args = (config, model, noise_scheduler, optimizer, train_dataloader, lr_scheduler)

notebook_launcher(train_loop, args, num_processes=1)
# End-of-file (EOF)