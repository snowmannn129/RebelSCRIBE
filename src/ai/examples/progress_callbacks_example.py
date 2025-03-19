#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of progress callbacks for AI operations.

This module demonstrates how to use progress callbacks to track
long-running AI operations such as model downloading and fine-tuning.
"""

import os
import time
import threading
from typing import Optional

from src.ai.progress_callbacks import (
    OperationType, ProgressStatus, ProgressInfo, ProgressCallback,
    create_operation, start_operation, update_progress,
    complete_operation, fail_operation, cancel_operation,
    get_operation_progress, register_progress_callback,
    register_global_progress_callback
)
from src.ai.local_models import (
    download_model, fine_tune_model, get_models_directory
)
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def print_progress_callback(progress_info: ProgressInfo) -> None:
    """
    Simple callback that prints progress information.
    
    Args:
        progress_info: The progress information.
    """
    if progress_info.status == ProgressStatus.RUNNING:
        # Format progress as percentage
        percent = f"{progress_info.progress:.1%}"
        
        # Format estimated time remaining
        remaining = progress_info.estimated_time_remaining()
        if remaining is not None:
            if remaining < 60:
                time_str = f"{remaining:.1f}s"
            else:
                time_str = f"{remaining/60:.1f}m"
            eta = f"ETA: {time_str}"
        else:
            eta = "ETA: unknown"
        
        # Print progress
        print(f"[{progress_info.operation_type.value}] {percent} - {progress_info.message} ({eta})")
    
    elif progress_info.status == ProgressStatus.COMPLETED:
        print(f"[{progress_info.operation_type.value}] Completed: {progress_info.message}")
    
    elif progress_info.status == ProgressStatus.FAILED:
        print(f"[{progress_info.operation_type.value}] Failed: {progress_info.message}")
    
    elif progress_info.status == ProgressStatus.CANCELED:
        print(f"[{progress_info.operation_type.value}] Canceled: {progress_info.message}")


def progress_bar_callback(progress_info: ProgressInfo) -> None:
    """
    Callback that displays a progress bar.
    
    Args:
        progress_info: The progress information.
    """
    if progress_info.status == ProgressStatus.RUNNING:
        # Create a progress bar
        width = 40
        filled = int(width * progress_info.progress)
        bar = "█" * filled + "░" * (width - filled)
        
        # Format estimated time remaining
        remaining = progress_info.estimated_time_remaining()
        if remaining is not None:
            if remaining < 60:
                time_str = f"{remaining:.1f}s"
            else:
                time_str = f"{remaining/60:.1f}m"
            eta = f"ETA: {time_str}"
        else:
            eta = "ETA: unknown"
        
        # Print progress bar
        print(f"\r[{progress_info.operation_type.value}] [{bar}] {progress_info.progress:.1%} - {progress_info.message} ({eta})", end="")
    
    elif progress_info.status in (ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELED):
        # Print final status with newline
        status = progress_info.status.value.capitalize()
        print(f"\r[{progress_info.operation_type.value}] {status}: {progress_info.message}" + " " * 50)


def download_model_with_progress(model_name: str, task: str = "text-generation") -> Optional[str]:
    """
    Download a model with progress tracking.
    
    Args:
        model_name: The name of the model to download.
        task: The task the model is used for.
        
    Returns:
        Optional[str]: The path to the downloaded model, or None if download failed.
    """
    print(f"Downloading model {model_name} for task {task}...")
    
    # Download the model with progress callback
    model_path = download_model(
        model_name=model_name,
        task=task,
        progress_callback=progress_bar_callback
    )
    
    if model_path:
        print(f"\nModel downloaded successfully to {model_path}")
    else:
        print("\nFailed to download model")
    
    return model_path


def fine_tune_model_with_progress(model_name: str, output_dir: str) -> Optional[str]:
    """
    Fine-tune a model with progress tracking.
    
    Args:
        model_name: The name of the model to fine-tune.
        output_dir: The directory to save the fine-tuned model.
        
    Returns:
        Optional[str]: The path to the fine-tuned model, or None if fine-tuning failed.
    """
    print(f"Fine-tuning model {model_name}...")
    
    # Create some dummy training data
    training_data = [
        {"prompt": "What is Python?", "completion": "Python is a programming language."},
        {"prompt": "What is RebelSCRIBE?", "completion": "RebelSCRIBE is an AI-powered novel writing program."},
        {"prompt": "How to write a novel?", "completion": "Writing a novel involves planning, drafting, and revising."}
    ]
    
    # Fine-tune the model with progress callback
    fine_tuned_path = fine_tune_model(
        model_name_or_path=model_name,
        training_data=training_data,
        output_dir=output_dir,
        num_train_epochs=2,
        batch_size=1,
        progress_callback=progress_bar_callback
    )
    
    if fine_tuned_path:
        print(f"\nModel fine-tuned successfully and saved to {fine_tuned_path}")
    else:
        print("\nFailed to fine-tune model")
    
    return fine_tuned_path


def simulate_long_operation() -> None:
    """Simulate a long-running operation with progress updates."""
    # Create and start operation
    operation_id, _ = create_operation(OperationType.INFERENCE, "simulate_inference")
    register_progress_callback(operation_id, progress_bar_callback)
    
    start_operation(operation_id, "Starting inference")
    
    try:
        # Simulate progress updates
        for i in range(1, 11):
            progress = i / 10.0
            time.sleep(0.5)  # Simulate work
            update_progress(operation_id, progress, f"Processing step {i}/10")
        
        # Complete operation
        complete_operation(operation_id, "Inference result", "Inference completed successfully")
    
    except Exception as e:
        # Handle errors
        fail_operation(operation_id, str(e), f"Inference failed: {e}")


def simulate_cancelable_operation() -> None:
    """Simulate a long-running operation that can be canceled."""
    # Create and start operation
    operation_id, _ = create_operation(OperationType.OPTIMIZATION, "simulate_optimization")
    register_progress_callback(operation_id, progress_bar_callback)
    
    # Flag to control cancellation
    cancel_flag = threading.Event()
    
    # Function to run in a separate thread
    def run_operation():
        start_operation(operation_id, "Starting model optimization")
        
        try:
            # Simulate progress updates
            for i in range(1, 21):
                if cancel_flag.is_set():
                    # Operation was canceled
                    cancel_operation(operation_id, "Optimization canceled by user")
                    return
                
                progress = i / 20.0
                time.sleep(0.3)  # Simulate work
                update_progress(operation_id, progress, f"Optimizing model: step {i}/20")
            
            # Complete operation
            complete_operation(operation_id, "Optimized model", "Model optimization completed successfully")
        
        except Exception as e:
            # Handle errors
            fail_operation(operation_id, str(e), f"Optimization failed: {e}")
    
    # Start the operation in a separate thread
    thread = threading.Thread(target=run_operation)
    thread.start()
    
    # Simulate user canceling the operation after a few seconds
    time.sleep(3)
    print("\nUser requested cancellation...")
    cancel_flag.set()
    
    # Wait for the thread to complete
    thread.join()


def monitor_all_operations() -> None:
    """Monitor all operations with a global callback."""
    # Register a global callback
    register_global_progress_callback(print_progress_callback)
    
    print("Registered global progress callback. All operations will be monitored.")


def main():
    """Run the examples."""
    print("Progress Callbacks Examples")
    print("==========================")
    
    # Monitor all operations
    monitor_all_operations()
    
    # Example 1: Simulate a long-running operation
    print("\nExample 1: Simulating a long-running operation")
    simulate_long_operation()
    
    # Example 2: Simulate a cancelable operation
    print("\nExample 2: Simulating a cancelable operation")
    simulate_cancelable_operation()
    
    # Example 3: Download a model with progress tracking
    print("\nExample 3: Downloading a model with progress tracking")
    # Uncomment to actually download a model (takes time and bandwidth)
    # download_model_with_progress("gpt2", "text-generation")
    
    # Example 4: Fine-tune a model with progress tracking
    print("\nExample 4: Fine-tuning a model with progress tracking")
    # Uncomment to actually fine-tune a model (requires a downloaded model)
    # models_dir = get_models_directory()
    # output_dir = os.path.join(models_dir, "fine-tuned-gpt2")
    # fine_tune_model_with_progress("gpt2", output_dir)
    
    print("\nAll examples completed.")


if __name__ == "__main__":
    main()
