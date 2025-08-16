from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TrainingConfig:
    """
    Configuration class for training a generative model.
    Attributes:
        image_size (int): The resolution of the generated images.
        train_batch_size (int): Batch size used during training.
        eval_batch_size (int): Batch size used during evaluation.
        num_epochs (int): Number of training epochs.
        gradient_accumulation_steps (int): Number of steps to accumulate gradients before updating.
        learning_rate (float): Initial learning rate for the optimizer.
        lr_warmup_steps (int): Number of steps for learning rate warmup.
        save_image_epochs (int): Frequency (in epochs) to save generated images.
        save_model_epochs (int): Frequency (in epochs) to save model checkpoints.
        mixed_precision (str): Mixed precision training mode ("no", "fp16", etc.).
        output_dir (str): Directory to save outputs (images, models, logs).
        gpu_ids (str): Comma-separated list of GPU IDs to use.
        seed (int): Random seed for reproducibility.
        num_workers (int): Number of worker processes for data loading.
        push_to_hub (bool): Whether to push the model to the Hugging Face Hub.
        hub_model_id (str): Model ID for Hugging Face Hub.
        hub_private_repo (Optional[bool]): Whether the Hugging Face repo is private.
        overwrite_output_dir (bool): Whether to overwrite the output directory.
        early_stopping_patience (Optional[int]): Number of epochs with no improvement to wait before stopping.
        resume_from_checkpoint (Optional[str]): Path to a checkpoint to resume training from.
        log_interval (int): Number of steps between logging training metrics.
        optimizer (str): Optimizer to use (e.g., "adamw").
        weight_decay (float): Weight decay (L2 penalty) for the optimizer.
    """
    image_size: int = 256  # the generated image resolution
    train_batch_size: int = 4  # lowered for OOM safety; adjust as needed
    eval_batch_size: int = 4   # lowered for OOM safety; adjust as needed
    num_epochs: int = 200
    gradient_accumulation_steps: int = 1
    learning_rate: float = 1e-4
    lr_warmup_steps: int = 3000
    save_image_epochs: int = 50
    save_model_epochs: int = 75

    mixed_precision: str = "no"
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


