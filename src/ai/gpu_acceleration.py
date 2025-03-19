#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU acceleration support for RebelSCRIBE.

This module provides functionality for detecting and utilizing GPU acceleration
across different hardware platforms (NVIDIA with CUDA, AMD with ROCm, and Apple with Metal).
It integrates with the local_models module and other model-specific support modules.
"""

import os
import logging
import platform
import subprocess
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union, Callable

# Import optional dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import transformers
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Try to import CUDA-specific libraries
try:
    import torch.cuda
    CUDA_AVAILABLE = TORCH_AVAILABLE and torch.cuda.is_available()
except ImportError:
    CUDA_AVAILABLE = False

# Try to import ROCm-specific libraries
try:
    # Check if PyTorch was built with ROCm support
    ROCM_AVAILABLE = TORCH_AVAILABLE and hasattr(torch, 'hip') and torch.hip.is_available()
except (ImportError, AttributeError):
    ROCM_AVAILABLE = False

# Try to import Metal-specific libraries (for Apple Silicon)
try:
    import torch.mps
    MPS_AVAILABLE = TORCH_AVAILABLE and torch.backends.mps.is_available()
except (ImportError, AttributeError):
    MPS_AVAILABLE = False

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class GPUType(Enum):
    """Enum representing different GPU types."""
    NVIDIA = "nvidia"
    AMD = "amd"
    APPLE = "apple"
    NONE = "none"


class GPUAccelerationManager:
    """
    Manager class for GPU acceleration.
    
    This class provides methods for detecting available GPU hardware,
    configuring models for optimal performance, and managing GPU resources.
    """
    
    def __init__(self):
        """Initialize the GPU acceleration manager."""
        self._gpu_type = self._detect_gpu_type()
        self._gpu_count = self._detect_gpu_count()
        self._gpu_memory = self._detect_gpu_memory()
        self._initialized = True
        
        logger.info(f"GPU Acceleration Manager initialized: {self.get_gpu_info()}")
    
    def _detect_gpu_type(self) -> GPUType:
        """
        Detect the type of GPU available on the system.
        
        Returns:
            GPUType: The type of GPU available.
        """
        if CUDA_AVAILABLE:
            return GPUType.NVIDIA
        elif ROCM_AVAILABLE:
            return GPUType.AMD
        elif MPS_AVAILABLE:
            return GPUType.APPLE
        else:
            return GPUType.NONE
    
    def _detect_gpu_count(self) -> int:
        """
        Detect the number of GPUs available on the system.
        
        Returns:
            int: The number of GPUs available.
        """
        if self._gpu_type == GPUType.NVIDIA and CUDA_AVAILABLE:
            return torch.cuda.device_count()
        elif self._gpu_type == GPUType.AMD and ROCM_AVAILABLE:
            # For ROCm, we can use the same CUDA API
            return torch.cuda.device_count()
        elif self._gpu_type == GPUType.APPLE and MPS_AVAILABLE:
            # Apple Silicon has only one GPU
            return 1
        else:
            return 0
    
    def _detect_gpu_memory(self) -> List[int]:
        """
        Detect the memory of each GPU available on the system.
        
        Returns:
            List[int]: The memory of each GPU in MB.
        """
        memory_list = []
        
        if self._gpu_type == GPUType.NVIDIA and CUDA_AVAILABLE:
            for i in range(self._gpu_count):
                try:
                    # Get memory information for the current device
                    torch.cuda.set_device(i)
                    memory_info = torch.cuda.get_device_properties(i).total_memory
                    memory_list.append(memory_info // (1024 * 1024))  # Convert to MB
                except Exception as e:
                    logger.error(f"Error getting memory for NVIDIA GPU {i}: {e}")
                    memory_list.append(0)
        
        elif self._gpu_type == GPUType.AMD and ROCM_AVAILABLE:
            for i in range(self._gpu_count):
                try:
                    # For ROCm, we can use the same CUDA API
                    torch.cuda.set_device(i)
                    memory_info = torch.cuda.get_device_properties(i).total_memory
                    memory_list.append(memory_info // (1024 * 1024))  # Convert to MB
                except Exception as e:
                    logger.error(f"Error getting memory for AMD GPU {i}: {e}")
                    memory_list.append(0)
        
        elif self._gpu_type == GPUType.APPLE and MPS_AVAILABLE:
            # For Apple Silicon, we need to use system commands to get memory
            try:
                if platform.system() == "Darwin":
                    # Use system_profiler on macOS to get GPU memory
                    cmd = ["system_profiler", "SPDisplaysDataType"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        output = result.stdout
                        # Parse the output to find GPU memory
                        for line in output.split('\n'):
                            if "VRAM" in line or "Memory" in line:
                                try:
                                    # Extract the memory value
                                    memory_str = line.split(':')[1].strip()
                                    if "GB" in memory_str:
                                        memory_val = float(memory_str.replace("GB", "").strip())
                                        memory_list.append(int(memory_val * 1024))  # Convert GB to MB
                                    elif "MB" in memory_str:
                                        memory_val = float(memory_str.replace("MB", "").strip())
                                        memory_list.append(int(memory_val))
                                except Exception as e:
                                    logger.error(f"Error parsing Apple GPU memory: {e}")
                                    memory_list.append(0)
                                break
                    
                    if not memory_list:
                        # Fallback: use a reasonable default for Apple Silicon
                        # M1: 8GB or 16GB shared memory, M2: 8GB, 16GB, or 24GB shared memory
                        memory_list.append(8 * 1024)  # Assume 8GB as a conservative default
            
            except Exception as e:
                logger.error(f"Error getting memory for Apple GPU: {e}")
                memory_list.append(0)
        
        return memory_list
    
    def is_available(self) -> bool:
        """
        Check if GPU acceleration is available.
        
        Returns:
            bool: True if GPU acceleration is available, False otherwise.
        """
        return self._gpu_type != GPUType.NONE
    
    def get_gpu_type(self) -> GPUType:
        """
        Get the type of GPU available.
        
        Returns:
            GPUType: The type of GPU available.
        """
        return self._gpu_type
    
    def get_gpu_count(self) -> int:
        """
        Get the number of GPUs available.
        
        Returns:
            int: The number of GPUs available.
        """
        return self._gpu_count
    
    def get_gpu_memory(self) -> List[int]:
        """
        Get the memory of each GPU available.
        
        Returns:
            List[int]: The memory of each GPU in MB.
        """
        return self._gpu_memory
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """
        Get information about the available GPUs.
        
        Returns:
            Dict[str, Any]: Information about the available GPUs.
        """
        return {
            "type": self._gpu_type.value,
            "count": self._gpu_count,
            "memory": self._gpu_memory,
            "cuda_available": CUDA_AVAILABLE,
            "rocm_available": ROCM_AVAILABLE,
            "mps_available": MPS_AVAILABLE
        }
    
    def get_optimal_device_map(self, model_size_gb: float) -> Union[str, Dict[str, int]]:
        """
        Get the optimal device map for a model of the given size.
        
        Args:
            model_size_gb: The size of the model in GB.
            
        Returns:
            Union[str, Dict[str, int]]: The device map to use for the model.
                This can be "auto", "cpu", or a dictionary mapping model parts to devices.
        """
        if not self.is_available():
            return "cpu"
        
        # Convert model size to MB for comparison with GPU memory
        model_size_mb = model_size_gb * 1024
        
        # If we have a single GPU with enough memory, use "auto"
        if self._gpu_count == 1 and self._gpu_memory[0] >= model_size_mb:
            return "auto"
        
        # If we have multiple GPUs, check if they have enough combined memory
        if self._gpu_count > 1:
            total_memory = sum(self._gpu_memory)
            if total_memory >= model_size_mb:
                # Use "auto" for multi-GPU setups
                return "auto"
        
        # If we don't have enough GPU memory, use CPU
        return "cpu"
    
    def get_optimal_dtype(self) -> torch.dtype:
        """
        Get the optimal data type for the available GPU.
        
        Returns:
            torch.dtype: The optimal data type for the GPU.
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is not available")
        
        if self._gpu_type == GPUType.NVIDIA:
            # For NVIDIA GPUs, use float16 or bfloat16 if available
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
            else:
                return torch.float16
        
        elif self._gpu_type == GPUType.AMD:
            # For AMD GPUs, use float16
            return torch.float16
        
        elif self._gpu_type == GPUType.APPLE:
            # For Apple Silicon, use float16
            return torch.float16
        
        else:
            # For CPU, use float32
            return torch.float32
    
    def get_optimal_quantization(self, model_size_gb: float) -> Optional[str]:
        """
        Get the optimal quantization method for a model of the given size.
        
        Args:
            model_size_gb: The size of the model in GB.
            
        Returns:
            Optional[str]: The optimal quantization method, or None if no quantization is needed.
        """
        if not self.is_available():
            # For CPU, recommend 8-bit quantization for models > 1GB
            return "8bit" if model_size_gb > 1 else None
        
        # Convert model size to MB for comparison with GPU memory
        model_size_mb = model_size_gb * 1024
        
        # Check if we have enough GPU memory
        if self._gpu_count > 0:
            max_gpu_memory = max(self._gpu_memory)
            
            # If the model is too large for the GPU, recommend quantization
            if model_size_mb > max_gpu_memory:
                # For very large models, recommend 4-bit quantization
                if model_size_mb > max_gpu_memory * 2:
                    return "4bit"
                # For moderately large models, recommend 8-bit quantization
                else:
                    return "8bit"
        
        # If we have enough memory or no GPU, no quantization needed
        return None
    
    def optimize_for_inference(self, model: Any) -> Any:
        """
        Optimize a model for inference on the available GPU.
        
        Args:
            model: The model to optimize.
            
        Returns:
            Any: The optimized model.
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch is not available, cannot optimize model")
            return model
        
        if not self.is_available():
            logger.info("No GPU available, using CPU for inference")
            return model
        
        try:
            # Move model to the appropriate device
            if self._gpu_type == GPUType.NVIDIA:
                model = model.cuda()
            elif self._gpu_type == GPUType.AMD:
                model = model.cuda()
            elif self._gpu_type == GPUType.APPLE:
                model = model.to("mps")
            
            # Set model to evaluation mode
            model.eval()
            
            # Apply optimizations based on GPU type
            if hasattr(model, "half") and self._gpu_type != GPUType.APPLE:
                # Half precision for NVIDIA and AMD
                model = model.half()
            
            return model
        
        except Exception as e:
            logger.error(f"Error optimizing model for inference: {e}")
            # Return the original model if optimization fails
            return model
    
    def get_transformers_config(self, model_size_gb: float) -> Dict[str, Any]:
        """
        Get the optimal configuration for loading a Transformers model.
        
        Args:
            model_size_gb: The size of the model in GB.
            
        Returns:
            Dict[str, Any]: The configuration to use for loading the model.
        """
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers is not available")
            return {}
        
        config = {}
        
        # Set device map
        device_map = self.get_optimal_device_map(model_size_gb)
        config["device_map"] = device_map
        
        # Set data type
        if self.is_available():
            config["torch_dtype"] = self.get_optimal_dtype()
        
        # Set quantization
        quantization = self.get_optimal_quantization(model_size_gb)
        if quantization == "8bit":
            config["load_in_8bit"] = True
        elif quantization == "4bit":
            config["load_in_4bit"] = True
            config["bnb_4bit_compute_dtype"] = self.get_optimal_dtype()
            config["bnb_4bit_use_double_quant"] = True
            config["bnb_4bit_quant_type"] = "nf4"
        
        return config


# Create a singleton instance
_gpu_manager = None

def get_gpu_manager() -> GPUAccelerationManager:
    """
    Get the GPU acceleration manager instance.
    
    Returns:
        GPUAccelerationManager: The GPU acceleration manager instance.
    """
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUAccelerationManager()
    return _gpu_manager


def is_gpu_available() -> bool:
    """
    Check if GPU acceleration is available.
    
    Returns:
        bool: True if GPU acceleration is available, False otherwise.
    """
    return get_gpu_manager().is_available()


def get_gpu_info() -> Dict[str, Any]:
    """
    Get information about the available GPUs.
    
    Returns:
        Dict[str, Any]: Information about the available GPUs.
    """
    return get_gpu_manager().get_gpu_info()


def get_optimal_device_map(model_size_gb: float) -> Union[str, Dict[str, int]]:
    """
    Get the optimal device map for a model of the given size.
    
    Args:
        model_size_gb: The size of the model in GB.
        
    Returns:
        Union[str, Dict[str, int]]: The device map to use for the model.
    """
    return get_gpu_manager().get_optimal_device_map(model_size_gb)


def get_optimal_dtype() -> torch.dtype:
    """
    Get the optimal data type for the available GPU.
    
    Returns:
        torch.dtype: The optimal data type for the GPU.
    """
    return get_gpu_manager().get_optimal_dtype()


def get_optimal_quantization(model_size_gb: float) -> Optional[str]:
    """
    Get the optimal quantization method for a model of the given size.
    
    Args:
        model_size_gb: The size of the model in GB.
        
    Returns:
        Optional[str]: The optimal quantization method, or None if no quantization is needed.
    """
    return get_gpu_manager().get_optimal_quantization(model_size_gb)


def optimize_for_inference(model: Any) -> Any:
    """
    Optimize a model for inference on the available GPU.
    
    Args:
        model: The model to optimize.
        
    Returns:
        Any: The optimized model.
    """
    return get_gpu_manager().optimize_for_inference(model)


def get_transformers_config(model_size_gb: float) -> Dict[str, Any]:
    """
    Get the optimal configuration for loading a Transformers model.
    
    Args:
        model_size_gb: The size of the model in GB.
        
    Returns:
        Dict[str, Any]: The configuration to use for loading the model.
    """
    return get_gpu_manager().get_transformers_config(model_size_gb)
