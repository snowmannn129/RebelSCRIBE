"""
AWQ (Activation-aware Weight Quantization) support for RebelSCRIBE.

This module provides support for loading and using models quantized with AWQ,
which offers better quality than standard quantization methods while maintaining
high performance.

AWQ analyzes activation patterns during quantization to preserve the most important
weights, resulting in better quality at the same bit-width compared to other methods.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Union, Callable, Tuple, Any
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoConfig, TextIteratorStreamer
from concurrent.futures import ThreadPoolExecutor

from .progress_callbacks import (
    ProgressTracker, 
    create_progress_operation, 
    update_progress_operation
)

# Configure logger
logger = logging.getLogger(__name__)

class AWQModelManager:
    """
    Manager for AWQ quantized models.
    
    This class handles loading, unloading, and inference with AWQ quantized models.
    AWQ (Activation-aware Weight Quantization) is an advanced quantization method
    that analyzes activation patterns to preserve the most important weights.
    """
    
    def __init__(self):
        """Initialize the AWQ model manager."""
        self.loaded_models = {}
        self.tokenizers = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._check_dependencies()
    
    def _check_dependencies(self) -> bool:
        """
        Check if the required dependencies for AWQ are installed.
        
        Returns:
            bool: True if all dependencies are installed, False otherwise.
        """
        try:
            import autoawq
            logger.info("AWQ dependencies are installed.")
            return True
        except ImportError:
            logger.warning(
                "AWQ dependencies not found. Please install them with: "
                "pip install autoawq"
            )
            return False
    
    def is_available(self) -> bool:
        """
        Check if AWQ support is available.
        
        Returns:
            bool: True if AWQ support is available, False otherwise.
        """
        try:
            import autoawq
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def load_model(
        self, 
        model_name_or_path: str, 
        device: str = "auto", 
        device_map: Optional[Union[str, Dict[str, str]]] = None,
        **kwargs
    ) -> Tuple[Any, Any]:
        """
        Load an AWQ quantized model.
        
        Args:
            model_name_or_path: The name or path of the model to load.
            device: The device to load the model on. Default is "auto".
            device_map: The device map for model placement. Default is None.
            **kwargs: Additional arguments to pass to the model loading function.
            
        Returns:
            Tuple[Any, Any]: The loaded model and tokenizer.
            
        Raises:
            ImportError: If the required dependencies are not installed.
            RuntimeError: If the model cannot be loaded.
        """
        try:
            import autoawq
            from autoawq import AutoAWQForCausalLM
        except ImportError:
            raise ImportError(
                "AWQ dependencies not found. Please install them with: "
                "pip install autoawq"
            )
        
        # Create a progress operation
        operation_id = create_progress_operation(
            f"Loading AWQ model: {os.path.basename(model_name_or_path)}",
            "Initializing..."
        )
        
        try:
            update_progress_operation(operation_id, "Loading tokenizer...", 0.1)
            tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
            
            # Determine device map if not provided
            if device_map is None:
                if device == "auto":
                    if torch.cuda.is_available():
                        device_map = "auto"
                    else:
                        device_map = "cpu"
                else:
                    device_map = device
            
            update_progress_operation(operation_id, "Loading model configuration...", 0.3)
            
            # Load the model
            update_progress_operation(operation_id, "Loading AWQ model...", 0.5)
            model = AutoAWQForCausalLM.from_quantized(
                model_name_or_path,
                device_map=device_map,
                **kwargs
            )
            
            update_progress_operation(operation_id, "Finalizing model setup...", 0.9)
            
            # Store the model and tokenizer
            model_id = model_name_or_path
            self.loaded_models[model_id] = model
            self.tokenizers[model_id] = tokenizer
            
            update_progress_operation(
                operation_id, 
                f"Model {os.path.basename(model_name_or_path)} loaded successfully", 
                1.0,
                is_complete=True
            )
            
            return model, tokenizer
            
        except Exception as e:
            update_progress_operation(
                operation_id,
                f"Error loading model: {str(e)}",
                1.0,
                is_complete=True,
                is_error=True
            )
            logger.error(f"Error loading AWQ model: {str(e)}")
            raise RuntimeError(f"Failed to load AWQ model: {str(e)}")
    
    def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_id: The ID of the model to unload.
            
        Returns:
            bool: True if the model was unloaded, False otherwise.
        """
        if model_id in self.loaded_models:
            # Remove references to the model and tokenizer
            del self.loaded_models[model_id]
            if model_id in self.tokenizers:
                del self.tokenizers[model_id]
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Model {model_id} unloaded successfully")
            return True
        else:
            logger.warning(f"Model {model_id} not found, cannot unload")
            return False
    
    def generate_text(
        self,
        model_id: str,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        **kwargs
    ) -> str:
        """
        Generate text using an AWQ quantized model.
        
        Args:
            model_id: The ID of the model to use.
            prompt: The prompt to generate text from.
            max_new_tokens: The maximum number of tokens to generate.
            temperature: The temperature for sampling.
            top_p: The top-p value for nucleus sampling.
            top_k: The top-k value for top-k sampling.
            repetition_penalty: The penalty for repetition.
            **kwargs: Additional arguments to pass to the generate method.
            
        Returns:
            str: The generated text.
            
        Raises:
            ValueError: If the model is not loaded.
        """
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
        
        model = self.loaded_models[model_id]
        tokenizer = self.tokenizers[model_id]
        
        # Tokenize the prompt
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs.input_ids.to(model.device)
        
        # Generate text
        with torch.no_grad():
            output_ids = model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                do_sample=temperature > 0,
                **kwargs
            )
        
        # Decode the output
        output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        # Return only the newly generated text if needed
        if kwargs.get("return_full_text", False) is False:
            # Try to find where the prompt ends and the generated text begins
            # This is an approximation and might not work perfectly for all tokenizers
            prompt_tokens = len(input_ids[0])
            generated_ids = output_ids[0][prompt_tokens:]
            output_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return output_text
    
    async def generate_text_async(
        self,
        model_id: str,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        **kwargs
    ) -> str:
        """
        Generate text asynchronously using an AWQ quantized model.
        
        Args:
            model_id: The ID of the model to use.
            prompt: The prompt to generate text from.
            max_new_tokens: The maximum number of tokens to generate.
            temperature: The temperature for sampling.
            top_p: The top-p value for nucleus sampling.
            top_k: The top-k value for top-k sampling.
            repetition_penalty: The penalty for repetition.
            **kwargs: Additional arguments to pass to the generate method.
            
        Returns:
            str: The generated text.
            
        Raises:
            ValueError: If the model is not loaded.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: self.generate_text(
                model_id,
                prompt,
                max_new_tokens,
                temperature,
                top_p,
                top_k,
                repetition_penalty,
                **kwargs
            )
        )
    
    def generate_text_stream(
        self,
        model_id: str,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> TextIteratorStreamer:
        """
        Generate text using an AWQ quantized model with streaming output.
        
        Args:
            model_id: The ID of the model to use.
            prompt: The prompt to generate text from.
            max_new_tokens: The maximum number of tokens to generate.
            temperature: The temperature for sampling.
            top_p: The top-p value for nucleus sampling.
            top_k: The top-k value for top-k sampling.
            repetition_penalty: The penalty for repetition.
            callback: Optional callback function to call with each generated token.
            **kwargs: Additional arguments to pass to the generate method.
            
        Returns:
            TextIteratorStreamer: A streamer object that yields generated text.
            
        Raises:
            ValueError: If the model is not loaded.
        """
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
        
        model = self.loaded_models[model_id]
        tokenizer = self.tokenizers[model_id]
        
        # Tokenize the prompt
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs.input_ids.to(model.device)
        
        # Create a streamer
        streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True)
        
        # Generate text in a separate thread
        generation_kwargs = dict(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            do_sample=temperature > 0,
            streamer=streamer,
            **kwargs
        )
        
        self.executor.submit(model.generate, **generation_kwargs)
        
        # If a callback is provided, start a thread to process the streamer
        if callback:
            def process_stream():
                for text in streamer:
                    callback(text)
            
            import threading
            threading.Thread(target=process_stream).start()
        
        return streamer
    
    def chat_completion(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        **kwargs
    ) -> str:
        """
        Generate a chat completion using an AWQ quantized model.
        
        Args:
            model_id: The ID of the model to use.
            messages: A list of message dictionaries with 'role' and 'content' keys.
            max_new_tokens: The maximum number of tokens to generate.
            temperature: The temperature for sampling.
            top_p: The top-p value for nucleus sampling.
            top_k: The top-k value for top-k sampling.
            repetition_penalty: The penalty for repetition.
            **kwargs: Additional arguments to pass to the generate method.
            
        Returns:
            str: The generated chat completion.
            
        Raises:
            ValueError: If the model is not loaded or the messages format is invalid.
        """
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
        
        # Format the messages into a prompt
        prompt = self._format_chat_prompt(messages)
        
        # Generate the completion
        completion = self.generate_text(
            model_id,
            prompt,
            max_new_tokens,
            temperature,
            top_p,
            top_k,
            repetition_penalty,
            **kwargs
        )
        
        return completion
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Format a list of chat messages into a prompt string.
        
        Args:
            messages: A list of message dictionaries with 'role' and 'content' keys.
            
        Returns:
            str: The formatted prompt string.
            
        Raises:
            ValueError: If the messages format is invalid.
        """
        prompt = ""
        
        for message in messages:
            if 'role' not in message or 'content' not in message:
                raise ValueError("Each message must have 'role' and 'content' keys")
            
            role = message['role'].lower()
            content = message['content']
            
            if role == 'system':
                prompt += f"<|system|>\n{content}\n"
            elif role == 'user':
                prompt += f"<|user|>\n{content}\n"
            elif role == 'assistant':
                prompt += f"<|assistant|>\n{content}\n"
            else:
                prompt += f"<|{role}|>\n{content}\n"
        
        # Add the final assistant prompt
        prompt += "<|assistant|>\n"
        
        return prompt
    
    def close(self):
        """
        Close the AWQ model manager and release resources.
        """
        # Unload all models
        for model_id in list(self.loaded_models.keys()):
            self.unload_model(model_id)
        
        # Shutdown the executor
        self.executor.shutdown(wait=True)
        
        logger.info("AWQ model manager closed")


# Create a singleton instance
_awq_manager = None

def get_awq_manager() -> AWQModelManager:
    """
    Get the singleton AWQ model manager instance.
    
    Returns:
        AWQModelManager: The AWQ model manager instance.
    """
    global _awq_manager
    if _awq_manager is None:
        _awq_manager = AWQModelManager()
    return _awq_manager
