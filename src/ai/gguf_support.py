#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GGUF model support for RebelSCRIBE.

This module provides functionality for loading and using GGUF format models,
which are commonly used for efficient inference with LLaMA, Mistral, and other
large language models. GGUF (GPT-Generated Unified Format) is a newer format
that has replaced GGML in many applications.

Example usage:
    ```python
    from src.ai.gguf_support import (
        load_gguf_model, generate_text, generate_text_stream,
        chat_completion, chat_completion_stream
    )
    
    # Load a GGUF model
    model = load_gguf_model("path/to/model.gguf")
    
    # Generate text
    response = generate_text(model, "Once upon a time")
    print(response)
    
    # Generate text with streaming
    for chunk in generate_text_stream(model, "Tell me a story about"):
        print(chunk, end="", flush=True)
    
    # Chat completion
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, who are you?"}
    ]
    response = chat_completion(model, messages)
    print(response)
    
    # Chat completion with streaming
    for chunk in chat_completion_stream(model, messages):
        print(chunk, end="", flush=True)
    
    # Unload the model when done
    unload_gguf_model(model)
    ```
"""

import os
import logging
import json
import time
import threading
import queue
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, Generator, Iterator

# Import optional dependencies
try:
    from llama_cpp import Llama, LlamaGrammar
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

from src.utils.logging_utils import get_logger
from src.utils.file_utils import ensure_directory
from src.ai.progress_callbacks import (
    OperationType, ProgressStatus, ProgressInfo, ProgressCallback,
    create_operation, start_operation, update_progress,
    complete_operation, fail_operation, cancel_operation
)

logger = get_logger(__name__)

# Model cache for loaded models
MODEL_CACHE = {}

# Lock for thread-safe model loading
MODEL_LOCK = threading.Lock()

# Inference queue for background processing
INFERENCE_QUEUE = queue.Queue()
INFERENCE_THREAD = None
INFERENCE_RUNNING = False


class GgufModelNotAvailableError(Exception):
    """Exception raised when GGUF model support is not available."""
    pass


class GgufModelLoadError(Exception):
    """Exception raised when a GGUF model fails to load."""
    pass


class GgufInferenceError(Exception):
    """Exception raised when inference with a GGUF model fails."""
    pass


def is_gguf_available() -> bool:
    """
    Check if GGUF model support is available.
    
    Returns:
        bool: True if GGUF models can be used, False otherwise.
    """
    return LLAMA_CPP_AVAILABLE


def check_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies for GGUF models are available.
    
    Returns:
        Dict[str, bool]: A dictionary mapping dependency names to availability.
    """
    return {
        "llama_cpp": LLAMA_CPP_AVAILABLE
    }


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


def load_gguf_model(model_path: str, 
                   n_ctx: int = 2048,
                   n_batch: int = 512,
                   n_gpu_layers: int = 0,
                   use_mlock: bool = False,
                   use_mmap: bool = True,
                   verbose: bool = False,
                   use_cache: bool = True) -> Any:
    """
    Load a GGUF model.
    
    Args:
        model_path: Path to the GGUF model file.
        n_ctx: Context size (in tokens) for the model.
        n_batch: Batch size for prompt processing.
        n_gpu_layers: Number of layers to offload to GPU (0 = CPU only).
        use_mlock: Lock the model in memory.
        use_mmap: Use memory mapping for the model.
        verbose: Enable verbose logging.
        use_cache: Whether to use the model cache.
        
    Returns:
        Any: The loaded model.
        
    Raises:
        GgufModelNotAvailableError: If GGUF model support is not available.
        GgufModelLoadError: If the model fails to load.
    """
    if not is_gguf_available():
        raise GgufModelNotAvailableError("GGUF model support is not available. Please install llama-cpp-python.")
    
    # Check if the model is already in the cache
    cache_key = model_path
    if use_cache and cache_key in MODEL_CACHE:
        logger.debug(f"Using cached GGUF model for {model_path}")
        return MODEL_CACHE[cache_key]
    
    try:
        with MODEL_LOCK:
            # Check again in case another thread loaded the model while we were waiting
            if use_cache and cache_key in MODEL_CACHE:
                return MODEL_CACHE[cache_key]
            
            logger.info(f"Loading GGUF model from {model_path}...")
            
            # Check if the model file exists
            if not os.path.exists(model_path):
                raise GgufModelLoadError(f"Model file not found: {model_path}")
            
            # Load the model
            model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_batch=n_batch,
                n_gpu_layers=n_gpu_layers,
                use_mlock=use_mlock,
                use_mmap=use_mmap,
                verbose=verbose
            )
            
            # Add to cache
            if use_cache:
                MODEL_CACHE[cache_key] = model
            
            logger.info(f"GGUF model loaded successfully from {model_path}")
            return model
    
    except Exception as e:
        logger.error(f"Error loading GGUF model from {model_path}: {e}", exc_info=True)
        raise GgufModelLoadError(f"Failed to load GGUF model: {str(e)}")


def unload_gguf_model(model: Any) -> bool:
    """
    Unload a GGUF model from memory and remove it from the cache.
    
    Args:
        model: The model to unload.
        
    Returns:
        bool: True if the model was unloaded, False otherwise.
    """
    if not is_gguf_available():
        logger.warning("GGUF model support is not available.")
        return False
    
    with MODEL_LOCK:
        # Find the model in the cache
        for key, cached_model in list(MODEL_CACHE.items()):
            if cached_model is model:
                # Remove from cache
                del MODEL_CACHE[key]
                logger.info(f"Unloaded GGUF model from cache: {key}")
                
                # Free resources
                try:
                    del model
                except Exception as e:
                    logger.warning(f"Error while deleting model: {e}")
                
                return True
    
    return False


def clear_gguf_model_cache() -> None:
    """Clear the GGUF model cache."""
    with MODEL_LOCK:
        for key, model in list(MODEL_CACHE.items()):
            try:
                del model
            except Exception as e:
                logger.warning(f"Error while deleting model {key}: {e}")
        
        MODEL_CACHE.clear()
    
    logger.info("GGUF model cache cleared")


def generate_text(model: Any, prompt: str, 
                 max_tokens: int = 512,
                 temperature: float = 0.7,
                 top_p: float = 0.9,
                 top_k: int = 40,
                 repeat_penalty: float = 1.1,
                 stop: Optional[List[str]] = None) -> str:
    """
    Generate text using a GGUF model.
    
    Args:
        model: The GGUF model to use.
        prompt: The prompt to generate text from.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature (higher = more creative, lower = more deterministic).
        top_p: Nucleus sampling parameter.
        top_k: Top-k sampling parameter.
        repeat_penalty: Penalty for repeating tokens.
        stop: List of strings that stop generation when encountered.
        
    Returns:
        str: The generated text.
        
    Raises:
        GgufModelNotAvailableError: If GGUF model support is not available.
        GgufInferenceError: If inference fails.
    """
    if not is_gguf_available():
        raise GgufModelNotAvailableError("GGUF model support is not available.")
    
    try:
        # Set up stop sequences
        stop_sequences = stop or []
        
        # Generate text
        output = model(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            stop=stop_sequences
        )
        
        # Extract the generated text
        if isinstance(output, dict) and "choices" in output:
            # API-like output format
            generated_text = output["choices"][0]["text"]
        else:
            # Direct output
            generated_text = output
        
        return generated_text
    
    except Exception as e:
        logger.error(f"Error generating text with GGUF model: {e}", exc_info=True)
        raise GgufInferenceError(f"Failed to generate text: {str(e)}")


def generate_text_stream(model: Any, prompt: str, 
                        max_tokens: int = 512,
                        temperature: float = 0.7,
                        top_p: float = 0.9,
                        top_k: int = 40,
                        repeat_penalty: float = 1.1,
                        stop: Optional[List[str]] = None) -> Generator[str, None, None]:
    """
    Generate text using a GGUF model with streaming output.
    
    Args:
        model: The GGUF model to use.
        prompt: The prompt to generate text from.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature (higher = more creative, lower = more deterministic).
        top_p: Nucleus sampling parameter.
        top_k: Top-k sampling parameter.
        repeat_penalty: Penalty for repeating tokens.
        stop: List of strings that stop generation when encountered.
        
    Yields:
        str: Chunks of generated text as they become available.
        
    Raises:
        GgufModelNotAvailableError: If GGUF model support is not available.
        GgufInferenceError: If inference fails.
    """
    if not is_gguf_available():
        raise GgufModelNotAvailableError("GGUF model support is not available.")
    
    try:
        # Set up stop sequences
        stop_sequences = stop or []
        
        # Generate text with streaming
        for chunk in model(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            stop=stop_sequences,
            stream=True
        ):
            # Extract the generated text chunk
            if isinstance(chunk, dict) and "choices" in chunk:
                # API-like output format
                text_chunk = chunk["choices"][0]["text"]
            else:
                # Direct output
                text_chunk = chunk
            
            yield text_chunk
    
    except Exception as e:
        logger.error(f"Error generating text stream with GGUF model: {e}", exc_info=True)
        raise GgufInferenceError(f"Failed to generate text stream: {str(e)}")


def format_chat_prompt(messages: List[Dict[str, str]], 
                      system_template: str = "<<SYS>>\n{system}\n<</SYS>>\n\n",
                      user_template: str = "{user}",
                      assistant_template: str = "{assistant}",
                      default_system_message: str = "You are a helpful assistant.") -> str:
    """
    Format a list of chat messages into a prompt string for the model.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys.
        system_template: Template for system messages.
        user_template: Template for user messages.
        assistant_template: Template for assistant messages.
        default_system_message: Default system message if none is provided.
        
    Returns:
        str: Formatted prompt string.
    """
    prompt = ""
    has_system = False
    
    # Process messages
    for message in messages:
        role = message.get("role", "").lower()
        content = message.get("content", "")
        
        if role == "system":
            # Add system message (only the first one)
            if not has_system:
                prompt += system_template.format(system=content)
                has_system = True
        elif role == "user":
            # Add user message
            if prompt:
                prompt += "\n\n"
            prompt += user_template.format(user=content)
        elif role == "assistant":
            # Add assistant message
            if prompt:
                prompt += "\n\n"
            prompt += assistant_template.format(assistant=content)
    
    # Add default system message if none was provided
    if not has_system and default_system_message:
        system_prompt = system_template.format(system=default_system_message)
        prompt = system_prompt + prompt
    
    return prompt


def chat_completion(model: Any, messages: List[Dict[str, str]],
                   max_tokens: int = 512,
                   temperature: float = 0.7,
                   top_p: float = 0.9,
                   top_k: int = 40,
                   repeat_penalty: float = 1.1,
                   stop: Optional[List[str]] = None,
                   system_template: str = "<<SYS>>\n{system}\n<</SYS>>\n\n",
                   user_template: str = "{user}",
                   assistant_template: str = "{assistant}",
                   default_system_message: str = "You are a helpful assistant.") -> Dict[str, Any]:
    """
    Generate a chat completion using a GGUF model.
    
    Args:
        model: The GGUF model to use.
        messages: List of message dictionaries with 'role' and 'content' keys.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature (higher = more creative, lower = more deterministic).
        top_p: Nucleus sampling parameter.
        top_k: Top-k sampling parameter.
        repeat_penalty: Penalty for repeating tokens.
        stop: List of strings that stop generation when encountered.
        system_template: Template for system messages.
        user_template: Template for user messages.
        assistant_template: Template for assistant messages.
        default_system_message: Default system message if none is provided.
        
    Returns:
        Dict[str, Any]: Chat completion response in a format similar to OpenAI's API.
        
    Raises:
        GgufModelNotAvailableError: If GGUF model support is not available.
        GgufInferenceError: If inference fails.
    """
    if not is_gguf_available():
        raise GgufModelNotAvailableError("GGUF model support is not available.")
    
    try:
        # Format the prompt
        prompt = format_chat_prompt(
            messages=messages,
            system_template=system_template,
            user_template=user_template,
            assistant_template=assistant_template,
            default_system_message=default_system_message
        )
        
        # Generate text
        output = model(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            stop=stop
        )
        
        # Extract the generated text
        if isinstance(output, dict) and "choices" in output:
            # API-like output format
            generated_text = output["choices"][0]["text"]
        else:
            # Direct output
            generated_text = output
        
        # Format the response
        response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "gguf",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": -1,  # Not available
                "completion_tokens": -1,  # Not available
                "total_tokens": -1  # Not available
            }
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating chat completion with GGUF model: {e}", exc_info=True)
        raise GgufInferenceError(f"Failed to generate chat completion: {str(e)}")


def chat_completion_stream(model: Any, messages: List[Dict[str, str]],
                          max_tokens: int = 512,
                          temperature: float = 0.7,
                          top_p: float = 0.9,
                          top_k: int = 40,
                          repeat_penalty: float = 1.1,
                          stop: Optional[List[str]] = None,
                          system_template: str = "<<SYS>>\n{system}\n<</SYS>>\n\n",
                          user_template: str = "{user}",
                          assistant_template: str = "{assistant}",
                          default_system_message: str = "You are a helpful assistant.") -> Generator[Dict[str, Any], None, None]:
    """
    Generate a chat completion using a GGUF model with streaming output.
    
    Args:
        model: The GGUF model to use.
        messages: List of message dictionaries with 'role' and 'content' keys.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature (higher = more creative, lower = more deterministic).
        top_p: Nucleus sampling parameter.
        top_k: Top-k sampling parameter.
        repeat_penalty: Penalty for repeating tokens.
        stop: List of strings that stop generation when encountered.
        system_template: Template for system messages.
        user_template: Template for user messages.
        assistant_template: Template for assistant messages.
        default_system_message: Default system message if none is provided.
        
    Yields:
        Dict[str, Any]: Chunks of the chat completion response in a format similar to OpenAI's API.
        
    Raises:
        GgufModelNotAvailableError: If GGUF model support is not available.
        GgufInferenceError: If inference fails.
    """
    if not is_gguf_available():
        raise GgufModelNotAvailableError("GGUF model support is not available.")
    
    try:
        # Format the prompt
        prompt = format_chat_prompt(
            messages=messages,
            system_template=system_template,
            user_template=user_template,
            assistant_template=assistant_template,
            default_system_message=default_system_message
        )
        
        # Generate text with streaming
        for chunk in model(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            stop=stop,
            stream=True
        ):
            # Extract the generated text chunk
            if isinstance(chunk, dict) and "choices" in chunk:
                # API-like output format
                text_chunk = chunk["choices"][0]["text"]
            else:
                # Direct output
                text_chunk = chunk
            
            # Format the response chunk
            response_chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "gguf",
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": text_chunk
                        },
                        "finish_reason": None
                    }
                ]
            }
            
            yield response_chunk
    
    except Exception as e:
        logger.error(f"Error generating chat completion stream with GGUF model: {e}", exc_info=True)
        raise GgufInferenceError(f"Failed to generate chat completion stream: {str(e)}")


def start_inference_thread() -> None:
    """Start the background inference thread."""
    global INFERENCE_THREAD, INFERENCE_RUNNING
    
    if INFERENCE_RUNNING:
        logger.debug("Inference thread is already running")
        return
    
    INFERENCE_RUNNING = True
    INFERENCE_THREAD = threading.Thread(target=_inference_worker, daemon=True)
    INFERENCE_THREAD.start()
    logger.debug("Started GGUF inference thread")


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
        logger.debug("Stopped GGUF inference thread")


def _inference_worker() -> None:
    """Worker function for the inference thread."""
    logger.debug("GGUF inference worker thread started")
    
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
                logger.error(f"Error in GGUF inference task: {e}", exc_info=True)
                result = None
                error = str(e)
            
            # Call the callback with the result
            if callback:
                try:
                    callback(result, error)
                except Exception as e:
                    logger.error(f"Error in GGUF inference callback: {e}", exc_info=True)
            
            # Mark the task as done
            INFERENCE_QUEUE.task_done()
        
        except queue.Empty:
            # No tasks in the queue, continue
            pass
        
        except Exception as e:
            logger.error(f"Error in GGUF inference worker: {e}", exc_info=True)
    
    logger.debug("GGUF inference worker thread stopped")


def async_generate_text(model: Any, prompt: str, 
                       callback: Callable[[str, Optional[str]], None],
                       **kwargs) -> None:
    """
    Generate text asynchronously using a GGUF model.
    
    Args:
        model: The GGUF model to use.
        prompt: The prompt to generate text from.
        callback: A function to call with the result.
                 The function should take two arguments: result and error.
        **kwargs: Additional arguments to pass to generate_text.
    """
    # Start the inference thread if it's not running
    if not INFERENCE_RUNNING:
        start_inference_thread()
    
    # Add the task to the queue
    INFERENCE_QUEUE.put((generate_text, (model, prompt), kwargs, callback))


def async_chat_completion(model: Any, messages: List[Dict[str, str]],
                         callback: Callable[[Dict[str, Any], Optional[str]], None],
                         **kwargs) -> None:
    """
    Generate a chat completion asynchronously using a GGUF model.
    
    Args:
        model: The GGUF model to use.
        messages: List of message dictionaries with 'role' and 'content' keys.
        callback: A function to call with the result.
                 The function should take two arguments: result and error.
        **kwargs: Additional arguments to pass to chat_completion.
    """
    # Start the inference thread if it's not running
    if not INFERENCE_RUNNING:
        start_inference_thread()
    
    # Add the task to the queue
    INFERENCE_QUEUE.put((chat_completion, (model, messages), kwargs, callback))


def download_gguf_model(model_url: str, output_path: Optional[str] = None,
                       progress_callback: Optional[ProgressCallback] = None) -> Optional[str]:
    """
    Download a GGUF model from a URL.
    
    Args:
        model_url: URL of the GGUF model to download.
        output_path: Path where the model should be saved.
                    If None, the model will be saved in the models directory.
        progress_callback: Optional callback for tracking download progress.
        
    Returns:
        Optional[str]: The path to the downloaded model, or None if download failed.
    """
    import requests
    from tqdm import tqdm
    
    # Create operation for tracking progress
    operation_id, progress_info = create_operation(
        OperationType.DOWNLOAD, 
        operation_id=f"download_gguf_{os.path.basename(model_url)}",
        callback=progress_callback
    )
    
    try:
        # Start the operation
        start_operation(operation_id, f"Downloading GGUF model from {model_url}")
        
        # Determine output path
        if output_path is None:
            models_dir = get_models_directory()
            output_path = os.path.join(models_dir, os.path.basename(model_url))
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Download the model
        logger.info(f"Downloading GGUF model from {model_url} to {output_path}...")
        update_progress(operation_id, 0.1, "Starting download")
        
        # Make a HEAD request to get the file size
        response = requests.head(model_url, allow_redirects=True)
        file_size = int(response.headers.get("content-length", 0))
        
        # Download the file with progress tracking
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Update progress
                    if file_size > 0:
                        progress = min(0.1 + (downloaded / file_size) * 0.9, 0.99)
                        update_progress(
                            operation_id, 
                            progress, 
                            f"Downloaded {downloaded / (1024 * 1024):.1f} MB of {file_size / (1024 * 1024):.1f} MB"
                        )
        
        logger.info(f"GGUF model downloaded successfully to {output_path}")
        complete_operation(operation_id, output_path, f"GGUF model downloaded successfully to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error downloading GGUF model: {e}", exc_info=True)
        fail_operation(operation_id, str(e), f"Failed to download GGUF model from {model_url}")
        return None


def get_gguf_model_info(model_path: str) -> Dict[str, Any]:
    """
    Get information about a GGUF model.
    
    Args:
        model_path: Path to the GGUF model file.
        
    Returns:
        Dict[str, Any]: Dictionary containing model information.
        
    Raises:
        GgufModelNotAvailableError: If GGUF model support is not available.
        GgufModelLoadError: If the model fails to load.
    """
    if not is_gguf_available():
        raise GgufModelNotAvailableError("GGUF model support is not available.")
    
    try:
        # Check if the model file exists
        if not os.path.exists(model_path):
            raise GgufModelLoadError(f"Model file not found: {model_path}")
        
        # Get basic file information
        file_size = os.path.getsize(model_path)
        file_modified = os.path.getmtime(model_path)
        
        # Try to load the model metadata
        model = load_gguf_model(model_path, use_cache=False)
        
        # Extract model information
        model_info = {
            "path": model_path,
            "file_size": file_size,
            "file_size_mb": file_size / (1024 * 1024),
            "last_modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_modified)),
            "filename": os.path.basename(model_path),
            "format": "GGUF"
        }
        
        # Add model-specific information if available
        if hasattr(model, "metadata"):
            model_info.update(model.metadata)
        
        # Unload the model
        unload_gguf_model(model)
        
        return model_info
        
    except Exception as e:
        logger.error(f"Error getting GGUF model info: {e}", exc_info=True)
        raise GgufModelLoadError(f"Failed to get GGUF model info: {str(e)}")
