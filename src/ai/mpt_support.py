#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MPT model support for RebelSCRIBE.

This module provides support for MPT (MosaicML Pretrained Transformer) models,
including loading, text generation, and optimization.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Callable, Any

# Set up logging
logger = logging.getLogger(__name__)

# Check for required dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. MPT support will be limited.")

try:
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. MPT support will be disabled.")

# Constants
DEFAULT_MODEL = "mosaicml/mpt-7b"
DEFAULT_INSTRUCT_MODEL = "mosaicml/mpt-7b-instruct"
DEFAULT_CHAT_MODEL = "mosaicml/mpt-7b-chat"
DEFAULT_MAX_LENGTH = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_REPETITION_PENALTY = 1.1

# Global variables
MODEL_CACHE = {}
MODEL_LOCK = asyncio.Lock()


class MPTModelError(Exception):
    """Base exception for MPT model errors."""
    pass


class MPTModelNotAvailableError(MPTModelError):
    """Exception raised when MPT models are not available."""
    pass


class MPTModelLoadError(MPTModelError):
    """Exception raised when an MPT model fails to load."""
    pass


class MPTInferenceError(MPTModelError):
    """Exception raised when inference with an MPT model fails."""
    pass


def is_mpt_available() -> bool:
    """
    Check if MPT models are available.

    Returns:
        bool: True if MPT models are available, False otherwise.
    """
    return TORCH_AVAILABLE and TRANSFORMERS_AVAILABLE


def check_dependencies() -> Dict[str, bool]:
    """
    Check if all dependencies for MPT models are available.

    Returns:
        Dict[str, bool]: Dictionary of dependencies and their availability.
    """
    return {
        "torch": TORCH_AVAILABLE,
        "transformers": TRANSFORMERS_AVAILABLE
    }


def get_available_models() -> List[Dict[str, str]]:
    """
    Get a list of available MPT models.

    Returns:
        List[Dict[str, str]]: List of available models with metadata.
    """
    if not is_mpt_available():
        logger.warning("MPT models are not available due to missing dependencies.")
        return []

    # Return a list of recommended MPT models
    return [
        {
            "name": "mpt-7b",
            "path": "mosaicml/mpt-7b",
            "description": "MPT-7B base model (7 billion parameters)",
            "type": "base"
        },
        {
            "name": "mpt-7b-instruct",
            "path": "mosaicml/mpt-7b-instruct",
            "description": "MPT-7B instruction-tuned model",
            "type": "instruct"
        },
        {
            "name": "mpt-7b-chat",
            "path": "mosaicml/mpt-7b-chat",
            "description": "MPT-7B chat-tuned model",
            "type": "chat"
        },
        {
            "name": "mpt-30b",
            "path": "mosaicml/mpt-30b",
            "description": "MPT-30B base model (30 billion parameters)",
            "type": "base"
        },
        {
            "name": "mpt-30b-instruct",
            "path": "mosaicml/mpt-30b-instruct",
            "description": "MPT-30B instruction-tuned model",
            "type": "instruct"
        },
        {
            "name": "mpt-30b-chat",
            "path": "mosaicml/mpt-30b-chat",
            "description": "MPT-30B chat-tuned model",
            "type": "chat"
        }
    ]


async def load_model(
    model_name_or_path: str = DEFAULT_INSTRUCT_MODEL,
    device: str = "auto",
    quantization: Optional[str] = "4bit",
    use_cache: bool = True
) -> Tuple[Any, Any]:
    """
    Load an MPT model and tokenizer.

    Args:
        model_name_or_path (str): The name or path of the model to load.
        device (str): The device to load the model on ("cpu", "cuda", "auto").
        quantization (Optional[str]): Quantization level ("4bit", "8bit", None).
        use_cache (bool): Whether to use the model cache.

    Returns:
        Tuple[Any, Any]: The loaded model and tokenizer.

    Raises:
        MPTModelNotAvailableError: If MPT models are not available.
        MPTModelLoadError: If the model fails to load.
    """
    if not is_mpt_available():
        raise MPTModelNotAvailableError("MPT models are not available due to missing dependencies.")

    # Check if the model is already in the cache
    cache_key = f"{model_name_or_path}_{device}_{quantization}"
    if use_cache and cache_key in MODEL_CACHE:
        logger.info(f"Using cached MPT model: {model_name_or_path}")
        return MODEL_CACHE[cache_key]

    try:
        logger.info(f"Loading MPT model: {model_name_or_path}")

        # Determine the device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Set up quantization parameters
        quantization_config = None
        if quantization == "4bit":
            quantization_config = transformers.BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True
            )
        elif quantization == "8bit":
            quantization_config = transformers.BitsAndBytesConfig(
                load_in_8bit=True
            )

        # Load the model
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            device_map=device,
            quantization_config=quantization_config,
            trust_remote_code=True
        )

        # Load the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True
        )

        # Cache the model and tokenizer
        if use_cache:
            async with MODEL_LOCK:
                MODEL_CACHE[cache_key] = (model, tokenizer)

        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load MPT model: {e}")
        raise MPTModelLoadError(f"Failed to load MPT model: {e}")


async def unload_model(
    model_name_or_path: str = DEFAULT_INSTRUCT_MODEL,
    device: str = "auto",
    quantization: Optional[str] = "4bit"
) -> bool:
    """
    Unload an MPT model from the cache.

    Args:
        model_name_or_path (str): The name or path of the model to unload.
        device (str): The device the model was loaded on.
        quantization (Optional[str]): Quantization level used.

    Returns:
        bool: True if the model was unloaded, False otherwise.
    """
    cache_key = f"{model_name_or_path}_{device}_{quantization}"
    
    async with MODEL_LOCK:
        if cache_key in MODEL_CACHE:
            del MODEL_CACHE[cache_key]
            logger.info(f"Unloaded MPT model: {model_name_or_path}")
            return True
        else:
            logger.warning(f"MPT model not found in cache: {model_name_or_path}")
            return False


async def clear_model_cache() -> None:
    """
    Clear the MPT model cache.

    Returns:
        None
    """
    async with MODEL_LOCK:
        MODEL_CACHE.clear()
    logger.info("Cleared MPT model cache")


async def generate_text(
    prompt: str,
    model_name_or_path: str = DEFAULT_INSTRUCT_MODEL,
    max_length: int = DEFAULT_MAX_LENGTH,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    repetition_penalty: float = DEFAULT_REPETITION_PENALTY,
    device: str = "auto",
    quantization: Optional[str] = "4bit",
    use_cache: bool = True
) -> str:
    """
    Generate text using an MPT model.

    Args:
        prompt (str): The prompt to generate text from.
        model_name_or_path (str): The name or path of the model to use.
        max_length (int): The maximum length of the generated text.
        temperature (float): The temperature for sampling.
        top_p (float): The top-p value for nucleus sampling.
        repetition_penalty (float): The repetition penalty.
        device (str): The device to use for inference.
        quantization (Optional[str]): Quantization level to use.
        use_cache (bool): Whether to use the model cache.

    Returns:
        str: The generated text.

    Raises:
        MPTModelNotAvailableError: If MPT models are not available.
        MPTInferenceError: If inference fails.
    """
    if not is_mpt_available():
        raise MPTModelNotAvailableError("MPT models are not available due to missing dependencies.")

    try:
        # Load the model and tokenizer
        model, tokenizer = await load_model(
            model_name_or_path=model_name_or_path,
            device=device,
            quantization=quantization,
            use_cache=use_cache
        )

        # Format the prompt based on model type
        if "instruct" in model_name_or_path.lower():
            formatted_prompt = f"Below is an instruction. Write a response that appropriately completes the request.\n\n### Instruction:\n{prompt}\n\n### Response:"
        elif "chat" in model_name_or_path.lower():
            formatted_prompt = f"<human>: {prompt}\n<bot>:"
        else:
            formatted_prompt = prompt

        # Tokenize the prompt
        inputs = tokenizer(formatted_prompt, return_tensors="pt")
        
        # Move inputs to the appropriate device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if device != "cpu":
            inputs = {k: v.to(device) for k, v in inputs.items()}

        # Generate text
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode the generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract the assistant's response
        if "instruct" in model_name_or_path.lower():
            if "### Response:" in generated_text:
                generated_text = generated_text.split("### Response:", 1)[1].strip()
        elif "chat" in model_name_or_path.lower():
            if "<bot>:" in generated_text:
                generated_text = generated_text.split("<bot>:", 1)[1].strip()

        return generated_text

    except Exception as e:
        logger.error(f"MPT inference error: {e}")
        raise MPTInferenceError(f"MPT inference error: {e}")


async def generate_text_streaming(
    prompt: str,
    callback: Callable[[str, Optional[str]], None],
    model_name_or_path: str = DEFAULT_INSTRUCT_MODEL,
    max_length: int = DEFAULT_MAX_LENGTH,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    repetition_penalty: float = DEFAULT_REPETITION_PENALTY,
    device: str = "auto",
    quantization: Optional[str] = "4bit",
    use_cache: bool = True
) -> None:
    """
    Generate text using an MPT model with streaming output.

    Args:
        prompt (str): The prompt to generate text from.
        callback (Callable[[str, Optional[str]], None]): Callback function for streaming output.
            The first argument is the generated text chunk, the second is an error message (if any).
        model_name_or_path (str): The name or path of the model to use.
        max_length (int): The maximum length of the generated text.
        temperature (float): The temperature for sampling.
        top_p (float): The top-p value for nucleus sampling.
        repetition_penalty (float): The repetition penalty.
        device (str): The device to use for inference.
        quantization (Optional[str]): Quantization level to use.
        use_cache (bool): Whether to use the model cache.

    Returns:
        None

    Raises:
        MPTModelNotAvailableError: If MPT models are not available.
        MPTInferenceError: If inference fails.
    """
    if not is_mpt_available():
        raise MPTModelNotAvailableError("MPT models are not available due to missing dependencies.")

    try:
        # Load the model and tokenizer
        model, tokenizer = await load_model(
            model_name_or_path=model_name_or_path,
            device=device,
            quantization=quantization,
            use_cache=use_cache
        )

        # Format the prompt based on model type
        if "instruct" in model_name_or_path.lower():
            formatted_prompt = f"Below is an instruction. Write a response that appropriately completes the request.\n\n### Instruction:\n{prompt}\n\n### Response:"
        elif "chat" in model_name_or_path.lower():
            formatted_prompt = f"<human>: {prompt}\n<bot>:"
        else:
            formatted_prompt = prompt

        # Tokenize the prompt
        inputs = tokenizer(formatted_prompt, return_tensors="pt")
        
        # Move inputs to the appropriate device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if device != "cpu":
            inputs = {k: v.to(device) for k, v in inputs.items()}

        # Create a streamer
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

        # Generate text in a separate thread
        generation_kwargs = {
            **inputs,
            "max_length": max_length,
            "temperature": temperature,
            "top_p": top_p,
            "repetition_penalty": repetition_penalty,
            "do_sample": temperature > 0,
            "pad_token_id": tokenizer.eos_token_id,
            "streamer": streamer
        }

        # Start generation in a separate thread
        import threading
        thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        # Stream the output
        generated_text = ""
        for text in streamer:
            generated_text += text
            callback(text, None)

        # Wait for the thread to finish
        thread.join()

    except Exception as e:
        logger.error(f"MPT streaming inference error: {e}")
        callback("", str(e))
        raise MPTInferenceError(f"MPT streaming inference error: {e}")


async def chat_completion(
    messages: List[Dict[str, str]],
    model_name_or_path: str = DEFAULT_CHAT_MODEL,
    max_length: int = DEFAULT_MAX_LENGTH,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    repetition_penalty: float = DEFAULT_REPETITION_PENALTY,
    device: str = "auto",
    quantization: Optional[str] = "4bit",
    use_cache: bool = True
) -> str:
    """
    Generate a chat completion using an MPT model.

    Args:
        messages (List[Dict[str, str]]): List of message dictionaries with "role" and "content" keys.
        model_name_or_path (str): The name or path of the model to use.
        max_length (int): The maximum length of the generated text.
        temperature (float): The temperature for sampling.
        top_p (float): The top-p value for nucleus sampling.
        repetition_penalty (float): The repetition penalty.
        device (str): The device to use for inference.
        quantization (Optional[str]): Quantization level to use.
        use_cache (bool): Whether to use the model cache.

    Returns:
        str: The generated response.

    Raises:
        MPTModelNotAvailableError: If MPT models are not available.
        MPTInferenceError: If inference fails.
    """
    if not is_mpt_available():
        raise MPTModelNotAvailableError("MPT models are not available due to missing dependencies.")

    try:
        # Format the messages into a prompt
        prompt = ""
        
        # Check if we're using a chat model
        is_chat_model = "chat" in model_name_or_path.lower()
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if is_chat_model:
                if role == "system":
                    # For chat models, prepend system message as a special instruction
                    prompt += f"<system>: {content}\n"
                elif role == "user":
                    prompt += f"<human>: {content}\n"
                elif role == "assistant":
                    prompt += f"<bot>: {content}\n"
            else:
                # For instruct models, format as instruction
                if role == "system":
                    prompt += f"System: {content}\n"
                elif role == "user":
                    prompt += f"User: {content}\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n"
        
        # Add the final prompt token
        if is_chat_model:
            prompt += "<bot>:"
        else:
            prompt += "Assistant:"

        # Generate the response
        response = await generate_text(
            prompt=prompt,
            model_name_or_path=model_name_or_path,
            max_length=max_length,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            device=device,
            quantization=quantization,
            use_cache=use_cache
        )

        return response

    except Exception as e:
        logger.error(f"MPT chat completion error: {e}")
        raise MPTInferenceError(f"MPT chat completion error: {e}")


async def chat_completion_streaming(
    messages: List[Dict[str, str]],
    callback: Callable[[str, Optional[str]], None],
    model_name_or_path: str = DEFAULT_CHAT_MODEL,
    max_length: int = DEFAULT_MAX_LENGTH,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    repetition_penalty: float = DEFAULT_REPETITION_PENALTY,
    device: str = "auto",
    quantization: Optional[str] = "4bit",
    use_cache: bool = True
) -> None:
    """
    Generate a chat completion using an MPT model with streaming output.

    Args:
        messages (List[Dict[str, str]]): List of message dictionaries with "role" and "content" keys.
        callback (Callable[[str, Optional[str]], None]): Callback function for streaming output.
            The first argument is the generated text chunk, the second is an error message (if any).
        model_name_or_path (str): The name or path of the model to use.
        max_length (int): The maximum length of the generated text.
        temperature (float): The temperature for sampling.
        top_p (float): The top-p value for nucleus sampling.
        repetition_penalty (float): The repetition penalty.
        device (str): The device to use for inference.
        quantization (Optional[str]): Quantization level to use.
        use_cache (bool): Whether to use the model cache.

    Returns:
        None

    Raises:
        MPTModelNotAvailableError: If MPT models are not available.
        MPTInferenceError: If inference fails.
    """
    if not is_mpt_available():
        raise MPTModelNotAvailableError("MPT models are not available due to missing dependencies.")

    try:
        # Format the messages into a prompt
        prompt = ""
        
        # Check if we're using a chat model
        is_chat_model = "chat" in model_name_or_path.lower()
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if is_chat_model:
                if role == "system":
                    # For chat models, prepend system message as a special instruction
                    prompt += f"<system>: {content}\n"
                elif role == "user":
                    prompt += f"<human>: {content}\n"
                elif role == "assistant":
                    prompt += f"<bot>: {content}\n"
            else:
                # For instruct models, format as instruction
                if role == "system":
                    prompt += f"System: {content}\n"
                elif role == "user":
                    prompt += f"User: {content}\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n"
        
        # Add the final prompt token
        if is_chat_model:
            prompt += "<bot>:"
        else:
            prompt += "Assistant:"

        # Generate the response with streaming
        await generate_text_streaming(
            prompt=prompt,
            callback=callback,
            model_name_or_path=model_name_or_path,
            max_length=max_length,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            device=device,
            quantization=quantization,
            use_cache=use_cache
        )

    except Exception as e:
        logger.error(f"MPT streaming chat completion error: {e}")
        callback("", str(e))
        raise MPTInferenceError(f"MPT streaming chat completion error: {e}")


async def optimize_model(
    model_name_or_path: str,
    output_dir: Optional[str] = None,
    quantization: Optional[str] = "4bit"
) -> Optional[str]:
    """
    Optimize an MPT model for inference.

    Args:
        model_name_or_path (str): The name or path of the model to optimize.
        output_dir (Optional[str]): The directory to save the optimized model to.
        quantization (Optional[str]): Quantization level to use.

    Returns:
        Optional[str]: The path to the optimized model, or None if optimization failed.
    """
    if not is_mpt_available():
        logger.warning("MPT models are not available due to missing dependencies.")
        return None

    try:
        # Create output directory if it doesn't exist
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(model_name_or_path), "optimized")
        
        os.makedirs(output_dir, exist_ok=True)

        # Load the model with quantization
        model, tokenizer = await load_model(
            model_name_or_path=model_name_or_path,
            quantization=quantization,
            use_cache=False
        )

        # Save the optimized model
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

        logger.info(f"Optimized MPT model saved to: {output_dir}")
        return output_dir

    except Exception as e:
        logger.error(f"Failed to optimize MPT model: {e}")
        return None
