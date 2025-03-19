#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phi model support for RebelSCRIBE.

This module provides functionality for loading and using Microsoft Phi models,
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

# Default Phi model configurations
DEFAULT_PHI_MODELS = {
    "phi-2": {
        "name": "microsoft/phi-2",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Phi-2 model for text generation"
    },
    "phi-3-mini": {
        "name": "microsoft/Phi-3-mini-4k-instruct",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Phi-3 Mini model for text generation"
    },
    "phi-3-small": {
        "name": "microsoft/Phi-3-small-8k-instruct",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Phi-3 Small model for text generation"
    },
    "phi-3-medium": {
        "name": "microsoft/Phi-3-medium-4k-instruct",
        "type": "causal",
        "task": "text-generation",
        "quantized": False,
        "description": "Phi-3 Medium model for text generation"
    }
}


def check_phi_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies for Phi models are available.
    
    Returns:
        Dict[str, bool]: A dictionary mapping dependency names to availability.
    """
    return {
        "torch": TORCH_AVAILABLE,
        "transformers": TRANSFORMERS_AVAILABLE,
        "bitsandbytes": BITSANDBYTES_AVAILABLE,
        "accelerate": ACCELERATE_AVAILABLE
    }


def is_phi_available() -> bool:
    """
    Check if Phi models functionality is available.
    
    Returns:
        bool: True if Phi models can be used, False otherwise.
    """
    deps = check_phi_dependencies()
    # We need at least torch and transformers
    return deps["torch"] and deps["transformers"]


def get_available_phi_models() -> List[Dict[str, Any]]:
    """
    Get a list of available Phi models.
    
    Returns:
        List[Dict[str, Any]]: A list of available Phi models with their metadata.
    """
    if not is_phi_available():
        logger.warning("Phi models are not available due to missing dependencies.")
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
                
                # Check if it's a Phi model
                if "phi" in model_dir.lower() or (
                    "name" in metadata and "phi" in metadata["name"].lower()
                ):
                    # Add the model path to the metadata
                    metadata["path"] = model_path
                    available_models.append(metadata)
            
            except Exception as e:
                logger.error(f"Error loading model metadata from {metadata_path}: {e}")
    
    return available_models


def download_phi_model(model_name: str, quantization: Optional[str] = None, 
                      force: bool = False) -> Optional[str]:
    """
    Download a Phi model from the Hugging Face Hub.
    
    Args:
        model_name: The name of the model to download.
        quantization: The quantization method to use (None, '4bit', or '8bit').
        force: Whether to force re-download if the model already exists.
        
    Returns:
        Optional[str]: The path to the downloaded model, or None if download failed.
    """
    if not is_phi_available():
        logger.error("Cannot download Phi model: required dependencies are not available.")
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
        
        logger.info(f"Downloading Phi model {model_name}...")
        
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
            if ACCELERATE_AVAILABLE and "medium" in model_name.lower():
                with init_empty_weights():
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name, 
                        torch_dtype=torch.float16
                    )
                model = load_checkpoint_and_dispatch(
                    model, 
                    model_name, 
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
            "description": f"Phi model {model_name} for text generation",
            "model_type": "phi"
        }
        
        with open(os.path.join(model_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Phi model {model_name} downloaded successfully to {model_dir}")
        return model_dir
    
    except Exception as e:
        logger.error(f"Error downloading Phi model {model_name}: {e}", exc_info=True)
        return None


def load_phi_model(model_name_or_path: str, quantization: Optional[str] = None) -> Tuple[Any, Any]:
    """
    Load a Phi model and tokenizer.
    
    Args:
        model_name_or_path: The name or path of the model to load.
        quantization: The quantization method to use (None, '4bit', or '8bit').
        
    Returns:
        Tuple[Any, Any]: The loaded model and tokenizer.
        
    Raises:
        ModelNotAvailableError: If Phi models are not available.
        ModelLoadError: If the model fails to load.
    """
    if not is_phi_available():
        raise ModelNotAvailableError("Phi models are not available due to missing dependencies.")
    
    try:
        with MODEL_LOCK:
            logger.info(f"Loading Phi model {model_name_or_path}...")
            
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
                    model_path = download_phi_model(model_name_or_path, quantization)
                    
                    if not model_path:
                        raise ModelLoadError(f"Phi model {model_name_or_path} not found and could not be downloaded.")
            
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
                if ACCELERATE_AVAILABLE and "medium" in model_path.lower():
                    with init_empty_weights():
                        model = AutoModelForCausalLM.from_pretrained(
                            model_path, 
                            torch_dtype=torch.float16
                        )
                    model = load_checkpoint_and_dispatch(
                        model, 
                        model_path, 
                        device_map="auto"
                    )
                else:
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        torch_dtype=torch.float16,
                        device_map="auto"
                    )
            
            logger.info(f"Phi model {model_name_or_path} loaded successfully")
            return (model, tokenizer)
    
    except Exception as e:
        logger.error(f"Error loading Phi model {model_name_or_path}: {e}", exc_info=True)
        raise ModelLoadError(f"Failed to load Phi model {model_name_or_path}: {str(e)}")


def generate_text_with_phi(prompt: str, model_name_or_path: str = None, 
                         max_length: int = 100, temperature: float = 0.7,
                         top_p: float = 0.9, top_k: int = 50,
                         num_return_sequences: int = 1,
                         quantization: Optional[str] = None,
                         stream: bool = False,
                         callback: Optional[Callable[[str], None]] = None) -> Union[List[str], None]:
    """
    Generate text using a Phi model.
    
    Args:
        prompt: The prompt to generate text from.
        model_name_or_path: The name or path of the model to use.
                           If None, the default Phi model will be used.
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
        ModelNotAvailableError: If Phi models are not available.
        ModelLoadError: If the model fails to load.
        InferenceError: If inference fails.
    """
    if not is_phi_available():
        raise ModelNotAvailableError("Phi models are not available due to missing dependencies.")
    
    try:
        # Use default model if none specified
        if model_name_or_path is None:
            model_name_or_path = DEFAULT_PHI_MODELS["phi-2"]["name"]
        
        # Load the model and tokenizer
        model, tokenizer = load_phi_model(model_name_or_path, quantization)
        
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
        logger.error(f"Error generating text with Phi: {e}", exc_info=True)
        raise InferenceError(f"Failed to generate text with Phi: {str(e)}")


def async_generate_text_with_phi(prompt: str, callback: Callable[[List[str], Optional[str]], None],
                               model_name_or_path: str = None, **kwargs) -> None:
    """
    Generate text asynchronously using a Phi model.
    
    Args:
        prompt: The prompt to generate text from.
        callback: A function to call with the result.
                 The function should take two arguments: result and error.
        model_name_or_path: The name or path of the model to use.
        **kwargs: Additional arguments to pass to generate_text_with_phi.
    """
    # Start a new thread for generation
    def _generate_thread():
        try:
            result = generate_text_with_phi(prompt, model_name_or_path, **kwargs)
            callback(result, None)
        except Exception as e:
            logger.error(f"Error in async Phi generation: {e}", exc_info=True)
            callback(None, str(e))
    
    thread = threading.Thread(target=_generate_thread)
    thread.daemon = True
    thread.start()


def format_chat_prompt(messages: List[Dict[str, str]], model_name_or_path: str = None) -> str:
    """
    Format a list of chat messages into a prompt for Phi models.
    
    Args:
        messages: A list of message dictionaries, each with 'role' and 'content' keys.
                 Roles can be 'user', 'assistant', or 'system'.
        model_name_or_path: The name or path of the model to use.
                           Different models may require different formats.
        
    Returns:
        str: The formatted prompt string.
    """
    # Default to Phi-3 format if no model specified
    if model_name_or_path is None:
        model_name_or_path = DEFAULT_PHI_MODELS["phi-3-mini"]["name"]
    
    # Check if it's a Phi-3 model (which supports chat)
    is_phi3 = "phi-3" in model_name_or_path.lower()
    
    # Format based on model type
    formatted_prompt = ""
    
    # Extract system message if present
    system_message = None
    chat_messages = []
    
    for message in messages:
        if message["role"] == "system":
            system_message = message["content"]
        else:
            chat_messages.append(message)
    
    # Format for Phi-3 models (which use instruct format)
    if is_phi3:
        if system_message:
            formatted_prompt += f"<|system|>\n{system_message}\n"
        
        for message in chat_messages:
            if message["role"] == "user":
                formatted_prompt += f"<|user|>\n{message['content']}\n"
            elif message["role"] == "assistant":
                formatted_prompt += f"<|assistant|>\n{message['content']}\n"
        
        # Add final assistant tag for generation
        if chat_messages[-1]["role"] == "user":
            formatted_prompt += "<|assistant|>\n"
    
    # Format for Phi-2 (which doesn't have a specific chat format)
    else:
        if system_message:
            formatted_prompt += f"System: {system_message}\n\n"
        
        for i, message in enumerate(chat_messages):
            if message["role"] == "user":
                formatted_prompt += f"Human: {message['content']}\n"
            elif message["role"] == "assistant":
                formatted_prompt += f"Assistant: {message['content']}\n"
        
        # Add final assistant prompt for generation
        if chat_messages[-1]["role"] == "user":
            formatted_prompt += "Assistant: "
    
    return formatted_prompt


def chat_with_phi(messages: List[Dict[str, str]], model_name_or_path: str = None,
                max_length: int = 100, temperature: float = 0.7,
                top_p: float = 0.9, top_k: int = 50,
                quantization: Optional[str] = None,
                stream: bool = False,
                callback: Optional[Callable[[str], None]] = None) -> Union[str, None]:
    """
    Generate a chat response using a Phi model.
    
    Args:
        messages: A list of message dictionaries, each with 'role' and 'content' keys.
                 Roles can be 'user', 'assistant', or 'system'.
        model_name_or_path: The name or path of the model to use.
                           If None, the default Phi-3 model will be used.
        max_length: The maximum length of the generated response.
        temperature: The temperature for sampling.
        top_p: The top-p value for nucleus sampling.
        top_k: The top-k value for top-k sampling.
        quantization: The quantization method to use (None, '4bit', or '8bit').
        stream: Whether to stream the output token by token.
        callback: A function to call with each token when streaming.
                 Only used when stream=True.
        
    Returns:
        Union[str, None]: The generated response, or None if streaming.
        
    Raises:
        ModelNotAvailableError: If Phi models are not available.
        ModelLoadError: If the model fails to load.
        InferenceError: If inference fails.
    """
    if not is_phi_available():
        raise ModelNotAvailableError("Phi models are not available due to missing dependencies.")
    
    try:
        # Use default model if none specified
        if model_name_or_path is None:
            model_name_or_path = DEFAULT_PHI_MODELS["phi-3-mini"]["name"]
        
        # Format the prompt
        prompt = format_chat_prompt(messages, model_name_or_path)
        
        # Generate text
        result = generate_text_with_phi(
            prompt=prompt,
            model_name_or_path=model_name_or_path,
            max_length=max_length,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            num_return_sequences=1,
            quantization=quantization,
            stream=stream,
            callback=callback
        )
        
        if stream:
            return None
        
        # Extract the assistant's response from the generated text
        response = result[0]
        
        # Clean up the response based on model type
        is_phi3 = "phi-3" in model_name_or_path.lower()
        
        if is_phi3:
            # For Phi-3, extract content between <|assistant|> and the next tag or end
            if "<|assistant|>" in response:
                response = response.split("<|assistant|>")[-1].strip()
                # Remove any following tags
                if "<|" in response:
                    response = response.split("<|")[0].strip()
        else:
            # For Phi-2, extract content after "Assistant: "
            if "Assistant: " in response:
                response = response.split("Assistant: ")[-1].strip()
        
        return response
    
    except Exception as e:
        logger.error(f"Error in chat with Phi: {e}", exc_info=True)
        raise InferenceError(f"Failed to chat with Phi: {str(e)}")


def async_chat_with_phi(messages: List[Dict[str, str]], callback: Callable[[str, Optional[str]], None],
                      model_name_or_path: str = None, **kwargs) -> None:
    """
    Generate a chat response asynchronously using a Phi model.
    
    Args:
        messages: A list of message dictionaries, each with 'role' and 'content' keys.
        callback: A function to call with the result.
                 The function should take two arguments: result and error.
        model_name_or_path: The name or path of the model to use.
        **kwargs: Additional arguments to pass to chat_with_phi.
    """
    # Start a new thread for generation
    def _chat_thread():
        try:
            result = chat_with_phi(messages, model_name_or_path, **kwargs)
            callback(result, None)
        except Exception as e:
            logger.error(f"Error in async Phi chat: {e}", exc_info=True)
            callback(None, str(e))
    
    thread = threading.Thread(target=_chat_thread)
    thread.daemon = True
    thread.start()
