from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TrainingConfig:
    image_size: int = 256  # the generated image resolution
    train_batch_size: int = 4  # lowered for OOM safety; adjust as needed
    eval_batch_size: int = 4   # lowered for OOM safety; adjust as needed
    num_epochs: int = 200
    gradient_accumulation_steps: int = 1
    learning_rate: float = 5e-4
    lr_warmup_steps: int = 500
    save_image_epochs: int = 50
    save_model_epochs: int = 50
    mixed_precision: str = "fp16"  # "no" for float32, "fp16" for mixed precision
    output_dir: str = "data/Generated/romantasy_bookcovers"
    gpu_ids: str = "0"
    seed: int = 42  # more common default for reproducibility
    num_workers: int = 8  # for DataLoader parallelism

    # Optional parameters for Hugging Face Hub
    push_to_hub: bool = False
    hub_model_id: str = "<your-username>/<my-awesome-model>"
    hub_private_repo: Optional[bool] = None
    overwrite_output_dir: bool = False

    # New: Early stopping and checkpointing
    early_stopping_patience: Optional[int] = None  # e.g., 10 for early stopping
    resume_from_checkpoint: Optional[str] = None   # path to checkpoint to resume

    # New: Logging
    log_interval: int = 10  # steps between logging

    # New: Option to change optimizer
    optimizer: str = "adamw"
    weight_decay: float = 0.01


