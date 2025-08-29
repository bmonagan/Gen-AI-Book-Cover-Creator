from diffusers import DDPMPipeline
import torch

import os
import datetime


date_str = datetime.datetime.now().strftime("%Y-%m-%d")
model_name: str = "epoch-49-step-15300-2025-08-28"
model_path = os.path.join("data", "Generated", "romantasy_bookcovers", "models", model_name)
print(f"Loading model from: {model_path}")
pipe = DDPMPipeline.from_pretrained(model_path, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

# Generate a set of images unconditionally.
num_images = 16
images = pipe(batch_size=num_images).images

eval_dir = "src/evaluation/created_images"
os.makedirs(eval_dir, exist_ok=True)
eval_dir = os.path.join(eval_dir, date_str)
os.makedirs(eval_dir, exist_ok=True)


# Save the generated images for qualitative evaluation.
for i, image in enumerate(images):
    image.save(f"{eval_dir}/{i}.png")
