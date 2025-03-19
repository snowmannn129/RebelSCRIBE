#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Llama model support for RebelSCRIBE.

This module provides functionality for loading and using Llama models,
optimizing inference, and integrating with the local_models module.
"""

import os
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from pathlib import Path
import threading

# Import optional dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer, 
        LlamaForCausalLM, LlamaTokenizer,
        BitsAndBytesConfig
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import bitsandbytes as bnb
    BITSANDBYTES_AVAILABLE = True
except ImportError:
    BITSANDBYTES_AVAILABLE = False

try:
    from accelerate import init_empty_weights, load_checkpoint_and_dispatch
    ACCELERATE_AVAILABLE = True
except ImportError:
    ACCELERATE_AVAILABLE = False

from src.utils.logging_utils import get_logger
from src.utils.file_utils import ensure_directory
from src.ai.local_models import (
    get_models_directory, ModelNotAvailableError, 
    ModelLoadError, InferenceError, MODEL_LOCK
)

logger = get_logger(__name__)

# Default Llama model configurations
DEFAULT_LLAMA_MODELS = {
    "llama2-7b": {
        "name": "meta-llama/Llama-2-7b-hf",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Llama 2 7B model for text generation"
    },
    "llama2-13b": {
        "name": "meta-llama/Llama-2-13b-hf",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Llama 2 13B model for text generation"
    },
    "llama2-70b": {
        "name": "meta-llama/Llama-2-70b-hf",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Llama 2 70B model for text generation"
    },
    "llama3-8b": {
        "name": "meta-llama/Llama-3-8b-hf",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Llama 3 8B model for text generation"
    },
    "llama3-70b": {
        "name": "meta-llama/Llama-3-70b-hf",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Llama 3 70B model for text generation"
    }
}


def check_llama_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies for Llama models are available.
    
    Returns:
        Dict[str, bool]: A dictionary mapping dependency names to availability.
    """
    return {
        "torch": TORCH_AVAILABLE,
        "transformers": TRANSFORMERS_AVAILABLE,
        "bitsandbytes": BITSANDBYTES_AVAILABLE,
        "accelerate": ACCELERATE_AVAILABLE
    }


def is_llama_available() -> bool:
    """
    Check if Llama models functionality is available.
    
    Returns:
        bool: True if Llama models can be used, False otherwise.
    """
    deps = check_llama_dependencies()
    # We need at least torch and transformers
    return deps["torch"] and deps["transformers"]


def get_available_llama_models() -> List[Dict[str, Any]]:
    """
    Get a list of available Llama models.
    
    Returns:
        List[Dict[str, Any]]: A list of available Llama models with their metadata.
    """
    if not is_llama_available():
        logger.warning("Llama models are not available due to missing dependencies.")
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
                
                # Check if it's a Llama model
                if "llama" in model_dir.lower() or (
                    "name" in metadata and "llama" in metadata["name"].lower()
                ):
                    # Add the model path to the metadata
                    metadata["path"] = model_path
                    available_models.append(metadata)
            
            except Exception as e:
                logger.error(f"Error loading model metadata from {metadata_path}: {e}")
    
    return available_models


def download_llama_model(model_name: str, quantization: Optional[str] = None, 
                        force: bool = False) -> Optional[str]:
    """
    Download a Llama model from the Hugging Face Hub.
    
    Args:
        model_name: The name of the model to download.
        quantization: The quantization method to use (None, '4bit', or '8bit').
        force: Whether to force re-download if the model already exists.
        
    Returns:
        Optional[str]: The path to the downloaded model, or None if download failed.
    """
    if not is_llama_available():
        logger.error("Cannot download Llama model: required dependencies are not available.")
        return None
    
    try:
        models_dir = get_models_directory()
        
        # Create a safe directory name from the model name
        safe_name = model_name.replace("/", "_")
        if quantization:
            safe_name = f"{safe_name}_{quantization}"
        
        model_dir = os.path.join(models_dir, safe_name)
        
        # Check if model already exists
        if os.path.exists(model_dir) and not force:
            logger.info(f"Model {model_name} already exists at {model_dir}")
            return model_dir
        
        # Ensure the model directory exists
        ensure_directory(model_dir)
        
        logger.info(f"Downloading Llama model {model_name}...")
        
        # Set up quantization config if needed
        quantization_config = None
        if quantization == "4bit" and BITSANDBYTES_AVAILABLE:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        elif quantization == "8bit" and BITSANDBYTES_AVAILABLE:
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True
            )
        
        # Download the model and tokenizer
        if "llama" in model_name.lower():
            # Use specific Llama classes if available
            try:
                tokenizer = LlamaTokenizer.from_pretrained(model_name)
            except:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Download model with quantization if specified
            if quantization_config:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=quantization_config,
                    device_map="auto"
                )
            else:
                # For large models, use accelerate if available
                if ACCELERATE_AVAILABLE and "70b" in model_name.lower():
                    with init_empty_weights():
                        model = AutoModelForCausalLM.from_pretrained(
                            model_name, 
                            torch_dtype=torch.float16
                        )
                    model = load_checkpoint_and_dispatch(
                        model, 
                        model_name, 
                        device_map="auto",
                        no_split_module_classes=["LlamaDecoderLayer"]
                    )
                else:
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=torch.float16,
                        device_map="auto"
                    )
        else:
            # Fallback to standard AutoModel classes
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            if quantization_config:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=quantization_config,
                    device_map="auto"
                )
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
        
        # Save the model and tokenizer
        model.save_pretrained(model_dir)
        tokenizer.save_pretrained(model_dir)
        
        # Create metadata file
        metadata = {
            "name": model_name,
            "task": "text-generation",
            "quantized": quantization is not None,
            "quantization": quantization,
            "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "description": f"Llama model {model_name} for text generation",
            "model_type": "llama"
        }
        
        with open(os.path.join(model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Llama model {model_name} downloaded successfully to {model_dir}")
        return model_dir
    
    except Exception as e:
        logger.error(f"Error downloading Llama model {model_name}: {e}", exc_info=True)
        return None


def load_llama_model(model_name_or_path: str, quantization: Optional[str] = None) -> Tuple[Any, Any]:
    """
    Load a Llama model and tokenizer.
    
    Args:
        model_name_or_path: The name or path of the model to load.
        quantization: The quantization method to use (None, '4bit', or '8bit').
        
    Returns:
        Tuple[Any, Any]: The loaded model and tokenizer.
        
    Raises:
        ModelNotAvailableError: If Llama models are not available.
        ModelLoadError: If the model fails to load.
    """
    if not is_llama_available():
        raise ModelNotAvailableError("Llama models are not available due to missing dependencies.")
    
    try:
        with MODEL_LOCK:
            logger.info(f"Loading Llama model {model_name_or_path}...")
            
            # Check if the model is a path or a name
            if os.path.exists(model_name_or_path):
                model_path = model_name_or_path
            else:
                # Check if the model is in the models directory
                models_dir = get_models_directory()
                safe_name = model_name_or_path.replace("/", "_")
                if quantization:
                    safe_name = f"{safe_name}_{quantization}"
                
                model_path = os.path.join(models_dir, safe_name)
                
                if not os.path.exists(model_path):
                    # Try to download the model
                    model_path = download_llama_model(model_name_or_path, quantization)
                    
                    if not model_path:
                        raise ModelLoadError(f"Llama model {model_name_or_path} not found and could not be downloaded.")
            
            # Set up quantization config if needed
            quantization_config = None
            if quantization == "4bit" and BITSANDBYTES_AVAILABLE:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            elif quantization == "8bit" and BITSANDBYTES_AVAILABLE:
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True
                )
            
            # Load the model and tokenizer
            if "llama" in model_path.lower():
                # Use specific Llama classes if available
                try:
                    tokenizer = LlamaTokenizer.from_pretrained(model_path)
                except:
                    tokenizer = AutoTokenizer.from_pretrained(model_path)
                
                # Load model with quantization if specified
                if quantization_config:
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        quantization_config=quantization_config,
                        device_map="auto"
                    )
                else:
                    # For large models, use accelerate if available
                    if ACCELERATE_AVAILABLE and "70b" in model_path.lower():
                        with init_empty_weights():
                            model = AutoModelForCausalLM.from_pretrained(
                                model_path, 
                                torch_dtype=torch.float16
                            )
                        model = load_checkpoint_and_dispatch(
                            model, 
                            model_path, 
                            device_map="auto",
                            no_split_module_classes=["LlamaDecoderLayer"]
                        )
                    else:
                        model = AutoModelForCausalLM.from_pretrained(
                            model_path,
                            torch_dtype=torch.float16,
                            device_map="auto"
                        )
            else:
                # Fallback to standard AutoModel classes
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                
                if quantization_config:
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        quantization_config=quantization_config,
                        device_map="auto"
                    )
                else:
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        torch_dtype=torch.float16,
                        device_map="auto"
                    )
            
            logger.info(f"Llama model {model_name_or_path} loaded successfully")
            return (model, tokenizer)
    
    except Exception as e:
        logger.error(f"Error loading Llama model {model_name_or_path}: {e}", exc_info=True)
        raise ModelLoadError(f"Failed to load Llama model {model_name_or_path}: {str(e)}")


def generate_text_with_llama(prompt: str, model_name_or_path: str = None, 
                           max_length: int = 100, temperature: float = 0.7,
                           top_p: float = 0.9, top_k: int = 50,
                           num_return_sequences: int = 1,
                           quantization: Optional[str] = None,
                           stream: bool = False,
                           callback: Optional[Callable[[str], None]] = None) -> Union[List[str], None]:
    """
    Generate text using a Llama model.
    
    Args:
        prompt: The prompt to generate text from.
        model_name_or_path: The name or path of the model to use.
                           If None, the default Llama model will be used.
        max_length: The maximum length of the generated text.
        temperature: The temperature for sampling.
        top_p: The top-p value for nucleus sampling.
        top_k: The top-k value for top-k sampling.
        num_return_sequences: The number of sequences to return.
        quantization: The quantization method to use (None, '4bit', or '8bit').
        stream: Whether to stream the output token by token.
        callback: A function to call with each token when streaming.
                 Only used when stream=True.
        
    Returns:
        Union[List[str], None]: The generated text sequences, or None if streaming.
        
    Raises:
        ModelNotAvailableError: If Llama models are not available.
        ModelLoadError: If the model fails to load.
        InferenceError: If inference fails.
    """
    if not is_llama_available():
        raise ModelNotAvailableError("Llama models are not available due to missing dependencies.")
    
    try:
        # Use default model if none specified
        if model_name_or_path is None:
            model_name_or_path = DEFAULT_LLAMA_MODELS["llama2-7b"]["name"]
        
        # Load the model and tokenizer
        model, tokenizer = load_llama_model(model_name_or_path, quantization)
        
        # Prepare inputs
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(model.device)
        
        # Generate text
        if stream:
            # Streaming generation
            if not callback:
                logger.warning("Streaming generation requested but no callback provided.")
                stream = False
            
            if stream:
                # Generate with streaming
                generated_text = ""
                
                # Initial generation
                outputs = model.generate(
                    input_ids,
                    max_length=len(input_ids[0]) + 1,  # Just one token
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    num_return_sequences=1,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
                
                # Get the new token
                new_token = outputs[0][-1].unsqueeze(0).unsqueeze(0)
                current_text = tokenizer.decode(new_token[0], skip_special_tokens=True)
                generated_text += current_text
                
                # Call the callback with the first token
                callback(current_text)
                
                # Continue generating tokens
                for _ in range(max_length - 1):
                    # Update input_ids with the new token
                    input_ids = torch.cat([input_ids, new_token], dim=1)
                    
                    # Generate next token
                    outputs = model.generate(
                        input_ids,
                        max_length=len(input_ids[0]) + 1,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        num_return_sequences=1,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                    
                    # Get the new token
                    new_token = outputs[0][-1].unsqueeze(0).unsqueeze(0)
                    current_text = tokenizer.decode(new_token[0], skip_special_tokens=True)
                    generated_text += current_text
                    
                    # Call the callback with the new token
                    callback(current_text)
                    
                    # Check for EOS token
                    if new_token[0][0].item() == tokenizer.eos_token_id:
                        break
                
                return None  # No return value for streaming
        
        else:
            # Standard generation
            with torch.no_grad():
                outputs = model.generate(
                    input_ids,
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
        logger.error(f"Error generating text with Llama: {e}", exc_info=True)
        raise InferenceError(f"Failed to generate text with Llama: {str(e)}")


def async_generate_text_with_llama(prompt: str, callback: Callable[[List[str], Optional[str]], None],
                                 model_name_or_path: str = None, **kwargs) -> None:
    """
    Generate text asynchronously using a Llama model.
    
    Args:
        prompt: The prompt to generate text from.
        callback: A function to call with the result.
                 The function should take two arguments: result and error.
        model_name_or_path: The name or path of the model to use.
        **kwargs: Additional arguments to pass to generate_text_with_llama.
    """
    # Start a new thread for generation
    def _generate_thread():
        try:
            result = generate_text_with_llama(prompt, model_name_or_path, **kwargs)
            callback(result, None)
        except Exception as e:
            logger.error(f"Error in async Llama generation: {e}", exc_info=True)
            callback(None, str(e))
    
    thread = threading.Thread(target=_generate_thread)
    thread.daemon = True
    thread.start()
