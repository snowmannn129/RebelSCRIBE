#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local AI models for RebelSCRIBE.

This module provides functionality for loading and using local AI models,
optimizing inference, managing models, implementing fallback mechanisms,
and fine-tuning models.
"""

import os
import logging
import json
import shutil
import tempfile
import time
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from pathlib import Path
import threading
import queue
import hashlib
import requests
from tqdm import tqdm

from src.ai.progress_callbacks import (
    OperationType, ProgressStatus, ProgressInfo, ProgressCallback,
    create_operation, start_operation, update_progress,
    complete_operation, fail_operation, cancel_operation
)

# Import optional dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer, 
        AutoModelForSeq2SeqLM, pipeline,
        TrainingArguments, Trainer
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import optimum
    from optimum.onnxruntime import ORTModelForCausalLM
    OPTIMUM_AVAILABLE = True
except ImportError:
    OPTIMUM_AVAILABLE = False

from src.utils.logging_utils import get_logger
from src.utils.file_utils import ensure_directory

logger = get_logger(__name__)

# Default model configurations
DEFAULT_MODELS = {
    "text-generation": {
        "name": "gpt2",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "GPT-2 small model for text generation"
    },
    "summarization": {
        "name": "t5-small",
        "type": "seq2seq",
        "task": "summarization",
        "quantized": False,
        "description": "T5 small model for summarization"
    },
    "grammar-correction": {
        "name": "t5-small",
        "type": "seq2seq",
        "task": "text2text-generation",
        "quantized": False,
        "description": "T5 small model for grammar correction"
    }
}

# Model cache for loaded models
MODEL_CACHE = {}

# Lock for thread-safe model loading
MODEL_LOCK = threading.Lock()

# Inference queue for background processing
INFERENCE_QUEUE = queue.Queue()
INFERENCE_THREAD = None
INFERENCE_RUNNING = False


class ModelNotAvailableError(Exception):
    """Exception raised when a model is not available."""
    pass


class ModelLoadError(Exception):
    """Exception raised when a model fails to load."""
    pass


class InferenceError(Exception):
    """Exception raised when inference fails."""
    pass


def check_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies for local models are available.
    
    Returns:
        Dict[str, bool]: A dictionary mapping dependency names to availability.
    """
    return {
        "torch": TORCH_AVAILABLE,
        "transformers": TRANSFORMERS_AVAILABLE,
        "onnx": ONNX_AVAILABLE,
        "optimum": OPTIMUM_AVAILABLE
    }


def is_local_models_available() -> bool:
    """
    Check if local models functionality is available.
    
    Returns:
        bool: True if local models can be used, False otherwise.
    """
    deps = check_dependencies()
    # We need at least torch and transformers
    return deps["torch"] and deps["transformers"]


def get_models_directory() -> str:
    """
    Get the directory where models are stored.
    
    Returns:
        str: The path to the models directory.
    """
    # Get the models directory from environment or use default
    models_dir = os.environ.get(
        "REBELSCRIBE_MODELS_DIR", 
        os.path.join(os.path.expanduser("~"), ".rebelscribe", "models")
    )
    
    # Ensure the directory exists
    ensure_directory(models_dir)
    
    return models_dir


def get_available_models() -> List[Dict[str, Any]]:
    """
    Get a list of available local models.
    
    Returns:
        List[Dict[str, Any]]: A list of available models with their metadata.
    """
    if not is_local_models_available():
        logger.warning("Local models are not available due to missing dependencies.")
        return []
    
    models_dir = get_models_directory()
    available_models = []
    
    # Check for model metadata files
    for model_dir in os.listdir(models_dir):
        model_path = os.path.join(models_dir, model_dir)
        
        if not os.path.isdir(model_path):
            continue
        
        metadata_path = os.path.join(model_path, "metadata.json")
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                
                # Add the model path to the metadata
                metadata["path"] = model_path
                available_models.append(metadata)
            
            except Exception as e:
                logger.error(f"Error loading model metadata from {metadata_path}: {e}")
    
    return available_models


def download_model(model_name: str, task: str = "text-generation", 
                  quantized: bool = False, force: bool = False,
                  progress_callback: Optional[ProgressCallback] = None) -> Optional[str]:
    """
    Download a model from the Hugging Face Hub.
    
    Args:
        model_name: The name of the model to download.
        task: The task the model is used for.
        quantized: Whether to download a quantized version of the model.
        force: Whether to force re-download if the model already exists.
        progress_callback: Optional callback for tracking download progress.
        
    Returns:
        Optional[str]: The path to the downloaded model, or None if download failed.
    """
    if not is_local_models_available():
        logger.error("Cannot download model: required dependencies are not available.")
        return None
    
    # Create operation for tracking progress
    operation_id, progress_info = create_operation(
        OperationType.DOWNLOAD, 
        operation_id=f"download_{model_name.replace('/', '_')}_{task}",
        callback=progress_callback
    )
    
    try:
        # Start the operation
        start_operation(operation_id, f"Downloading model {model_name} for task {task}")
        
        models_dir = get_models_directory()
        
        # Create a safe directory name from the model name
        safe_name = model_name.replace("/", "_")
        model_dir = os.path.join(models_dir, safe_name)
        
        # Check if model already exists
        if os.path.exists(model_dir) and not force:
            logger.info(f"Model {model_name} already exists at {model_dir}")
            complete_operation(operation_id, model_dir, f"Model {model_name} already exists at {model_dir}")
            return model_dir
        
        # Ensure the model directory exists
        ensure_directory(model_dir)
        
        logger.info(f"Downloading model {model_name} for task {task}...")
        update_progress(operation_id, 0.1, f"Preparing to download model {model_name}")
        
        # Custom download function with progress tracking for Hugging Face models
        def download_with_progress(repo_id, local_dir, task_type):
            """Download model files with progress tracking."""
            try:
                # Get model info from Hugging Face API
                api_url = f"https://huggingface.co/api/models/{repo_id}"
                response = requests.get(api_url)
                if response.status_code != 200:
                    logger.error(f"Failed to get model info for {repo_id}: {response.status_code}")
                    return False
                
                # Update progress
                update_progress(operation_id, 0.2, f"Retrieved model information for {repo_id}")
                
                # For simplicity, we'll use the transformers library's from_pretrained method
                # but we'll update progress at key points
                update_progress(operation_id, 0.3, f"Downloading model files for {repo_id}")
                
                return True
            except Exception as e:
                logger.error(f"Error in download_with_progress: {e}")
                return False
        
        # Download the model and tokenizer
        if task == "text-generation" or task == "text2text-generation":
            # Update progress
            update_progress(operation_id, 0.3, f"Downloading model weights for {model_name}")
            
            if quantized and OPTIMUM_AVAILABLE:
                # Download quantized model
                model = ORTModelForCausalLM.from_pretrained(
                    model_name, 
                    export=True, 
                    provider="CPUExecutionProvider"
                )
                update_progress(operation_id, 0.7, f"Downloaded model weights, now downloading tokenizer")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
            else:
                # Download regular model
                if "t5" in model_name.lower():
                    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                else:
                    model = AutoModelForCausalLM.from_pretrained(model_name)
                update_progress(operation_id, 0.7, f"Downloaded model weights, now downloading tokenizer")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Save the model and tokenizer
            update_progress(operation_id, 0.8, f"Saving model to disk at {model_dir}")
            model.save_pretrained(model_dir)
            tokenizer.save_pretrained(model_dir)
        
        else:
            # Use the pipeline API for other tasks
            update_progress(operation_id, 0.4, f"Downloading pipeline for task {task}")
            pipe = pipeline(task, model=model_name)
            update_progress(operation_id, 0.8, f"Saving pipeline to disk at {model_dir}")
            pipe.save_pretrained(model_dir)
        
        # Create metadata file
        update_progress(operation_id, 0.9, "Creating metadata file")
        metadata = {
            "name": model_name,
            "task": task,
            "quantized": quantized,
            "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "description": f"{model_name} for {task}"
        }
        
        with open(os.path.join(model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Model {model_name} downloaded successfully to {model_dir}")
        complete_operation(operation_id, model_dir, f"Model {model_name} downloaded successfully to {model_dir}")
        return model_dir
    
    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {e}", exc_info=True)
        fail_operation(operation_id, str(e), f"Failed to download model {model_name}")
        return None


def load_model(model_name_or_path: str, task: str = "text-generation", 
              use_cache: bool = True) -> Tuple[Any, Any]:
    """
    Load a model and tokenizer.
    
    Args:
        model_name_or_path: The name or path of the model to load.
        task: The task the model is used for.
        use_cache: Whether to use the model cache.
        
    Returns:
        Tuple[Any, Any]: The loaded model and tokenizer.
        
    Raises:
        ModelNotAvailableError: If local models are not available.
        ModelLoadError: If the model fails to load.
    """
    if not is_local_models_available():
        raise ModelNotAvailableError("Local models are not available due to missing dependencies.")
    
    # Check if the model is already in the cache
    cache_key = f"{model_name_or_path}_{task}"
    if use_cache and cache_key in MODEL_CACHE:
        logger.debug(f"Using cached model for {model_name_or_path}")
        return MODEL_CACHE[cache_key]
    
    try:
        with MODEL_LOCK:
            # Check again in case another thread loaded the model while we were waiting
            if use_cache and cache_key in MODEL_CACHE:
                return MODEL_CACHE[cache_key]
            
            logger.info(f"Loading model {model_name_or_path} for task {task}...")
            
            # Check if the model is a path or a name
            if os.path.exists(model_name_or_path):
                model_path = model_name_or_path
            else:
                # Check if the model is in the models directory
                models_dir = get_models_directory()
                safe_name = model_name_or_path.replace("/", "_")
                model_path = os.path.join(models_dir, safe_name)
                
                if not os.path.exists(model_path):
                    # Try to download the model
                    model_path = download_model(model_name_or_path, task)
                    
                    if not model_path:
                        raise ModelLoadError(f"Model {model_name_or_path} not found and could not be downloaded.")
            
            # Check for ONNX model
            onnx_path = os.path.join(model_path, "model.onnx")
            if os.path.exists(onnx_path) and ONNX_AVAILABLE:
                # Load ONNX model
                model = ort.InferenceSession(onnx_path)
                tokenizer = AutoTokenizer.from_pretrained(model_path)
            else:
                # Load regular model
                if task == "text-generation":
                    model = AutoModelForCausalLM.from_pretrained(model_path)
                    tokenizer = AutoTokenizer.from_pretrained(model_path)
                elif task == "text2text-generation" or task == "summarization":
                    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
                    tokenizer = AutoTokenizer.from_pretrained(model_path)
                else:
                    # Use pipeline for other tasks
                    pipe = pipeline(task, model=model_path)
                    return (pipe, None)
            
            # Add to cache
            if use_cache:
                MODEL_CACHE[cache_key] = (model, tokenizer)
            
            logger.info(f"Model {model_name_or_path} loaded successfully")
            return (model, tokenizer)
    
    except Exception as e:
        logger.error(f"Error loading model {model_name_or_path}: {e}", exc_info=True)
        raise ModelLoadError(f"Failed to load model {model_name_or_path}: {str(e)}")


def unload_model(model_name_or_path: str, task: str = "text-generation") -> bool:
    """
    Unload a model from the cache.
    
    Args:
        model_name_or_path: The name or path of the model to unload.
        task: The task the model is used for.
        
    Returns:
        bool: True if the model was unloaded, False otherwise.
    """
    cache_key = f"{model_name_or_path}_{task}"
    
    with MODEL_LOCK:
        if cache_key in MODEL_CACHE:
            del MODEL_CACHE[cache_key]
            logger.info(f"Unloaded model {model_name_or_path} from cache")
            return True
    
    return False


def clear_model_cache() -> None:
    """Clear the model cache."""
    with MODEL_LOCK:
        MODEL_CACHE.clear()
    logger.info("Model cache cleared")


def optimize_model(model_path: str, optimization_level: str = "O1") -> Optional[str]:
    """
    Optimize a model for faster inference.
    
    Args:
        model_path: The path to the model to optimize.
        optimization_level: The optimization level (O1, O2, O3).
        
    Returns:
        Optional[str]: The path to the optimized model, or None if optimization failed.
    """
    if not ONNX_AVAILABLE or not OPTIMUM_AVAILABLE:
        logger.error("Cannot optimize model: ONNX and Optimum are required.")
        return None
    
    try:
        logger.info(f"Optimizing model at {model_path}...")
        
        # Create a directory for the optimized model
        optimized_path = os.path.join(os.path.dirname(model_path), f"{os.path.basename(model_path)}_optimized")
        ensure_directory(optimized_path)
        
        # Load the model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Check if it's a causal or seq2seq model
        if os.path.exists(os.path.join(model_path, "decoder_model.onnx")):
            # It's a seq2seq model
            model = ORTModelForCausalLM.from_pretrained(
                model_path,
                export=False,
                provider="CPUExecutionProvider"
            )
        else:
            # Assume it's a causal model
            model = ORTModelForCausalLM.from_pretrained(
                model_path,
                export=True,
                provider="CPUExecutionProvider",
                optimization_level=optimization_level
            )
        
        # Save the optimized model
        model.save_pretrained(optimized_path)
        tokenizer.save_pretrained(optimized_path)
        
        # Copy metadata if it exists
        metadata_path = os.path.join(model_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Update metadata
            metadata["optimized"] = True
            metadata["optimization_level"] = optimization_level
            
            with open(os.path.join(optimized_path, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        
        logger.info(f"Model optimized successfully to {optimized_path}")
        return optimized_path
    
    except Exception as e:
        logger.error(f"Error optimizing model: {e}", exc_info=True)
        return None


def quantize_model(model_path: str, bits: int = 8) -> Optional[str]:
    """
    Quantize a model to reduce its size and improve inference speed.
    
    Args:
        model_path: The path to the model to quantize.
        bits: The number of bits to quantize to (8 or 4).
        
    Returns:
        Optional[str]: The path to the quantized model, or None if quantization failed.
    """
    if not TORCH_AVAILABLE or not TRANSFORMERS_AVAILABLE:
        logger.error("Cannot quantize model: PyTorch and Transformers are required.")
        return None
    
    try:
        logger.info(f"Quantizing model at {model_path} to {bits} bits...")
        
        # Create a directory for the quantized model
        quantized_path = os.path.join(os.path.dirname(model_path), f"{os.path.basename(model_path)}_quantized_{bits}bit")
        ensure_directory(quantized_path)
        
        # Load the model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Check if it's a causal or seq2seq model
        if os.path.exists(os.path.join(model_path, "decoder_model.pt")):
            # It's a seq2seq model
            model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        else:
            # Assume it's a causal model
            model = AutoModelForCausalLM.from_pretrained(model_path)
        
        # Quantize the model
        if bits == 8:
            # 8-bit quantization
            model = torch.quantization.quantize_dynamic(
                model, {torch.nn.Linear}, dtype=torch.qint8
            )
        elif bits == 4 and hasattr(torch, "quantization") and hasattr(torch.quantization, "quantize_per_tensor"):
            # 4-bit quantization (only available in newer PyTorch versions)
            model = torch.quantization.quantize_per_tensor(
                model, 0.01, 0, torch.quint4x2
            )
        else:
            logger.warning(f"Quantization to {bits} bits is not supported. Using 8-bit quantization.")
            model = torch.quantization.quantize_dynamic(
                model, {torch.nn.Linear}, dtype=torch.qint8
            )
        
        # Save the quantized model
        model.save_pretrained(quantized_path)
        tokenizer.save_pretrained(quantized_path)
        
        # Copy metadata if it exists
        metadata_path = os.path.join(model_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Update metadata
            metadata["quantized"] = True
            metadata["quantization_bits"] = bits
            
            with open(os.path.join(quantized_path, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        
        logger.info(f"Model quantized successfully to {quantized_path}")
        return quantized_path
    
    except Exception as e:
        logger.error(f"Error quantizing model: {e}", exc_info=True)
        return None


def generate_text(prompt: str, model_name_or_path: str = None, 
                 max_length: int = 100, temperature: float = 0.7,
                 top_p: float = 0.9, top_k: int = 50,
                 num_return_sequences: int = 1) -> List[str]:
    """
    Generate text using a local model.
    
    Args:
        prompt: The prompt to generate text from.
        model_name_or_path: The name or path of the model to use.
                           If None, the default text generation model will be used.
        max_length: The maximum length of the generated text.
        temperature: The temperature for sampling.
        top_p: The top-p value for nucleus sampling.
        top_k: The top-k value for top-k sampling.
        num_return_sequences: The number of sequences to return.
        
    Returns:
        List[str]: The generated text sequences.
        
    Raises:
        ModelNotAvailableError: If local models are not available.
        ModelLoadError: If the model fails to load.
        InferenceError: If inference fails.
    """
    if not is_local_models_available():
        raise ModelNotAvailableError("Local models are not available due to missing dependencies.")
    
    try:
        # Use default model if none specified
        if model_name_or_path is None:
            model_name_or_path = DEFAULT_MODELS["text-generation"]["name"]
        
        # Load the model and tokenizer
        model, tokenizer = load_model(model_name_or_path, "text-generation")
        
        # Prepare inputs
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Generate text
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                num_return_sequences=num_return_sequences,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode the generated text
        generated_texts = []
        for output in outputs:
            text = tokenizer.decode(output, skip_special_tokens=True)
            generated_texts.append(text)
        
        return generated_texts
    
    except Exception as e:
        logger.error(f"Error generating text: {e}", exc_info=True)
        raise InferenceError(f"Failed to generate text: {str(e)}")


def summarize_text(text: str, model_name_or_path: str = None, 
                  max_length: int = 100, min_length: int = 30) -> str:
    """
    Summarize text using a local model.
    
    Args:
        text: The text to summarize.
        model_name_or_path: The name or path of the model to use.
                           If None, the default summarization model will be used.
        max_length: The maximum length of the summary.
        min_length: The minimum length of the summary.
        
    Returns:
        str: The generated summary.
        
    Raises:
        ModelNotAvailableError: If local models are not available.
        ModelLoadError: If the model fails to load.
        InferenceError: If inference fails.
    """
    if not is_local_models_available():
        raise ModelNotAvailableError("Local models are not available due to missing dependencies.")
    
    try:
        # Use default model if none specified
        if model_name_or_path is None:
            model_name_or_path = DEFAULT_MODELS["summarization"]["name"]
        
        # Load the model and tokenizer
        model, tokenizer = load_model(model_name_or_path, "summarization")
        
        # Prepare inputs
        inputs = tokenizer("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
        
        # Generate summary
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
        
        # Decode the summary
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return summary
    
    except Exception as e:
        logger.error(f"Error summarizing text: {e}", exc_info=True)
        raise InferenceError(f"Failed to summarize text: {str(e)}")


def correct_grammar(text: str, model_name_or_path: str = None) -> str:
    """
    Correct grammar in text using a local model.
    
    Args:
        text: The text to correct.
        model_name_or_path: The name or path of the model to use.
                           If None, the default grammar correction model will be used.
        
    Returns:
        str: The corrected text.
        
    Raises:
        ModelNotAvailableError: If local models are not available.
        ModelLoadError: If the model fails to load.
        InferenceError: If inference fails.
    """
    if not is_local_models_available():
        raise ModelNotAvailableError("Local models are not available due to missing dependencies.")
    
    try:
        # Use default model if none specified
        if model_name_or_path is None:
            model_name_or_path = DEFAULT_MODELS["grammar-correction"]["name"]
        
        # Load the model and tokenizer
        model, tokenizer = load_model(model_name_or_path, "text2text-generation")
        
        # Prepare inputs
        inputs = tokenizer("grammar: " + text, return_tensors="pt", max_length=1024, truncation=True)
        
        # Generate corrected text
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_length=1024,
                num_beams=4,
                early_stopping=True
            )
        
        # Decode the corrected text
        corrected = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return corrected
    
    except Exception as e:
        logger.error(f"Error correcting grammar: {e}", exc_info=True)
        raise InferenceError(f"Failed to correct grammar: {str(e)}")


def start_inference_thread() -> None:
    """Start the background inference thread."""
    global INFERENCE_THREAD, INFERENCE_RUNNING
    
    if INFERENCE_RUNNING:
        logger.debug("Inference thread is already running")
        return
    
    INFERENCE_RUNNING = True
    INFERENCE_THREAD = threading.Thread(target=_inference_worker, daemon=True)
    INFERENCE_THREAD.start()
    logger.debug("Started inference thread")


def stop_inference_thread() -> None:
    """Stop the background inference thread."""
    global INFERENCE_RUNNING
    
    if not INFERENCE_RUNNING:
        logger.debug("Inference thread is not running")
        return
    
    INFERENCE_RUNNING = False
    
    # Add a sentinel value to the queue to wake up the thread
    INFERENCE_QUEUE.put(None)
    
    if INFERENCE_THREAD:
        INFERENCE_THREAD.join(timeout=2.0)
        logger.debug("Stopped inference thread")


def _inference_worker() -> None:
    """Worker function for the inference thread."""
    logger.debug("Inference worker thread started")
    
    while INFERENCE_RUNNING:
        try:
            # Get a task from the queue
            task = INFERENCE_QUEUE.get(timeout=1.0)
            
            # Check for sentinel value
            if task is None:
                INFERENCE_QUEUE.task_done()
                break
            
            # Unpack the task
            func, args, kwargs, callback = task
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
                error = None
            except Exception as e:
                logger.error(f"Error in inference task: {e}", exc_info=True)
                result = None
                error = str(e)
            
            # Call the callback with the result
            if callback:
                try:
                    callback(result, error)
                except Exception as e:
                    logger.error(f"Error in inference callback: {e}", exc_info=True)
            
            # Mark the task as done
            INFERENCE_QUEUE.task_done()
        
        except queue.Empty:
            # No tasks in the queue, continue
            pass
        
        except Exception as e:
            logger.error(f"Error in inference worker: {e}", exc_info=True)
    
    logger.debug("Inference worker thread stopped")


def async_generate_text(prompt: str, callback: Callable[[List[str], Optional[str]], None],
                       model_name_or_path: str = None, **kwargs) -> None:
    """
    Generate text asynchronously using a local model.
    
    Args:
        prompt: The prompt to generate text from.
        callback: A function to call with the result.
                 The function should take two arguments: result and error.
        model_name_or_path: The name or path of the model to use.
        **kwargs: Additional arguments to pass to generate_text.
    """
    # Start the inference thread if it's not running
    if not INFERENCE_RUNNING:
        start_inference_thread()
    
    # Add the task to the queue
    INFERENCE_QUEUE.put((generate_text, (prompt, model_name_or_path), kwargs, callback))


def async_summarize_text(text: str, callback: Callable[[str, Optional[str]], None],
                        model_name_or_path: str = None, **kwargs) -> None:
    """
    Summarize text asynchronously using a local model.
    
    Args:
        text: The text to summarize.
        callback: A function to call with the result.
                 The function should take two arguments: result and error.
        model_name_or_path: The name or path of the model to use.
        **kwargs: Additional arguments to pass to summarize_text.
    """
    # Start the inference thread if it's not running
    if not INFERENCE_RUNNING:
        start_inference_thread()
    
    # Add the task to the queue
    INFERENCE_QUEUE.put((summarize_text, (text, model_name_or_path), kwargs, callback))


def async_correct_grammar(text: str, callback: Callable[[str, Optional[str]], None],
                         model_name_or_path: str = None, **kwargs) -> None:
    """
    Correct grammar asynchronously using a local model.
    
    Args:
        text: The text to correct.
        callback: A function to call with the result.
                 The function should take two arguments: result and error.
        model_name_or_path: The name or path of the model to use.
        **kwargs: Additional arguments to pass to correct_grammar.
    """
    # Start the inference thread if it's not running
    if not INFERENCE_RUNNING:
        start_inference_thread()
    
    # Add the task to the queue
    INFERENCE_QUEUE.put((correct_grammar, (text, model_name_or_path), kwargs, callback))


def fine_tune_model(model_name_or_path: str, training_data: List[Dict[str, str]],
                   output_dir: str, task: str = "text-generation",
                   num_train_epochs: int = 3, learning_rate: float = 5e-5,
                   batch_size: int = 8, 
                   progress_callback: Optional[ProgressCallback] = None) -> Optional[str]:
    """
    Fine-tune a model on custom training data.
    
    Args:
        model_name_or_path: The name or path of the model to fine-tune.
        training_data: A list of dictionaries containing training examples.
                      For text generation, each dictionary should have 'prompt' and 'completion' keys.
                      For summarization, each dictionary should have 'text' and 'summary' keys.
        output_dir: The directory to save the fine-tuned model.
        task: The task to fine-tune for (e.g., "text-generation", "summarization").
        num_train_epochs: The number of training epochs.
        learning_rate: The learning rate for training.
        batch_size: The batch size for training.
        progress_callback: Optional callback for tracking fine-tuning progress.
        
    Returns:
        Optional[str]: The path to the fine-tuned model, or None if fine-tuning failed.
    """
    if not is_local_models_available() or not TRANSFORMERS_AVAILABLE:
        logger.error("Cannot fine-tune model: required dependencies are not available.")
        return None
    
    # Create operation for tracking progress
    operation_id, progress_info = create_operation(
        OperationType.FINE_TUNING, 
        operation_id=f"finetune_{model_name_or_path.replace('/', '_')}_{task}",
        callback=progress_callback
    )
    
    try:
        # Start the operation
        start_operation(operation_id, f"Fine-tuning model {model_name_or_path} for task {task}")
        
        logger.info(f"Fine-tuning model {model_name_or_path} for task {task}...")
        
        # Ensure the output directory exists
        ensure_directory(output_dir)
        
        # Load the model and tokenizer
        update_progress(operation_id, 0.1, f"Loading base model {model_name_or_path}")
        model, tokenizer = load_model(model_name_or_path, task, use_cache=False)
        
        # Prepare the dataset
        update_progress(operation_id, 0.2, "Preparing training dataset")
        if task == "text-generation":
            # Prepare text generation dataset
            train_texts = []
            for example in training_data:
                if "prompt" in example and "completion" in example:
                    prompt = example["prompt"]
                    completion = example["completion"]
                    train_texts.append(f"{prompt} {completion}")
            
            # Tokenize the dataset
            def tokenize_function(examples):
                return tokenizer(examples["text"], padding="max_length", truncation=True)
            
            from datasets import Dataset
            dataset = Dataset.from_dict({"text": train_texts})
            update_progress(operation_id, 0.3, "Tokenizing dataset")
            tokenized_dataset = dataset.map(tokenize_function, batched=True)
            
        elif task == "summarization" or task == "text2text-generation":
            # Prepare summarization dataset
            train_texts = []
            train_summaries = []
            for example in training_data:
                if "text" in example and "summary" in example:
                    train_texts.append(example["text"])
                    train_summaries.append(example["summary"])
            
            # Tokenize the dataset
            def tokenize_function(examples):
                model_inputs = tokenizer(examples["text"], padding="max_length", truncation=True)
                labels = tokenizer(examples["summary"], padding="max_length", truncation=True)
                model_inputs["labels"] = labels["input_ids"]
                return model_inputs
            
            from datasets import Dataset
            dataset = Dataset.from_dict({"text": train_texts, "summary": train_summaries})
            update_progress(operation_id, 0.3, "Tokenizing dataset")
            tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        else:
            logger.error(f"Unsupported task for fine-tuning: {task}")
            fail_operation(operation_id, f"Unsupported task: {task}", f"Task {task} is not supported for fine-tuning")
            return None
        
        # Set up training arguments
        update_progress(operation_id, 0.4, "Setting up training configuration")
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir=os.path.join(output_dir, "logs"),
            logging_steps=10,
            learning_rate=learning_rate,
            save_strategy="epoch",
            evaluation_strategy="epoch"
        )
        
        # Create a custom callback to track training progress
        class ProgressTrackingCallback(TrainingArguments):
            def on_epoch_begin(self, args, state, control, **kwargs):
                epoch = state.epoch
                total_epochs = args.num_train_epochs
                progress = 0.4 + (epoch / total_epochs) * 0.5  # 40% to 90% during training
                update_progress(operation_id, progress, f"Training epoch {epoch+1}/{total_epochs}")
                
            def on_epoch_end(self, args, state, control, **kwargs):
                epoch = state.epoch
                total_epochs = args.num_train_epochs
                progress = 0.4 + ((epoch+1) / total_epochs) * 0.5  # 40% to 90% during training
                update_progress(operation_id, progress, f"Completed epoch {epoch+1}/{total_epochs}")
        
        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            tokenizer=tokenizer,
            callbacks=[ProgressTrackingCallback]
        )
        
        # Train the model
        update_progress(operation_id, 0.5, f"Starting training for {num_train_epochs} epochs")
        trainer.train()
        
        # Save the fine-tuned model
        update_progress(operation_id, 0.9, "Saving fine-tuned model")
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        # Create metadata file
        metadata = {
            "name": f"fine-tuned-{os.path.basename(model_name_or_path)}",
            "base_model": model_name_or_path,
            "task": task,
            "fine_tuned": True,
            "fine_tune_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "num_train_epochs": num_train_epochs,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "training_examples": len(training_data),
            "description": f"Fine-tuned {model_name_or_path} for {task}"
        }
        
        with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Model fine-tuned successfully and saved to {output_dir}")
        complete_operation(operation_id, output_dir, f"Model fine-tuned successfully and saved to {output_dir}")
        return output_dir
    
    except Exception as e:
        logger.error(f"Error fine-tuning model: {e}", exc_info=True)
        fail_operation(operation_id, str(e), f"Failed to fine-tune model {model_name_or_path}")
        return None
