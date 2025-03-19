#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the GPU acceleration module.

This module contains tests for the GPU acceleration functionality,
including hardware detection, configuration generation, and model optimization.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from enum import Enum
from typing import Dict, List, Any

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.ai.gpu_acceleration import (
    GPUType, GPUAccelerationManager, get_gpu_manager,
    is_gpu_available, get_gpu_info, get_optimal_device_map,
    get_optimal_dtype, get_optimal_quantization,
    optimize_for_inference, get_transformers_config
)


class TestGPUAcceleration(unittest.TestCase):
    """Test case for the GPU acceleration module."""
    
    def setUp(self):
        """Set up the test case."""
        # Create patches for torch and related modules
        self.torch_patch = patch('src.ai.gpu_acceleration.torch', autospec=True)
        self.transformers_patch = patch('src.ai.gpu_acceleration.transformers', autospec=True)
        self.cuda_available_patch = patch('src.ai.gpu_acceleration.CUDA_AVAILABLE', True)
        self.rocm_available_patch = patch('src.ai.gpu_acceleration.ROCM_AVAILABLE', False)
        self.mps_available_patch = patch('src.ai.gpu_acceleration.MPS_AVAILABLE', False)
        
        # Start the patches
        self.mock_torch = self.torch_patch.start()
        self.mock_transformers = self.transformers_patch.start()
        self.cuda_available_patch.start()
        self.rocm_available_patch.start()
        self.mps_available_patch.start()
        
        # Configure the torch mock
        self.mock_torch.cuda.is_available.return_value = True
        self.mock_torch.cuda.device_count.return_value = 1
        
        # Create a mock device properties object
        device_props = MagicMock()
        device_props.total_memory = 8 * 1024 * 1024 * 1024  # 8 GB
        self.mock_torch.cuda.get_device_properties.return_value = device_props
        
        # Set up dtype attributes
        self.mock_torch.float16 = 'float16'
        self.mock_torch.float32 = 'float32'
        self.mock_torch.bfloat16 = 'bfloat16'
        
        # Configure CUDA capabilities
        self.mock_torch.cuda.is_bf16_supported.return_value = True
        
        # Reset the singleton instance
        from src.ai import gpu_acceleration
        gpu_acceleration._gpu_manager = None
    
    def tearDown(self):
        """Tear down the test case."""
        # Stop all patches
        self.torch_patch.stop()
        self.transformers_patch.stop()
        self.cuda_available_patch.stop()
        self.rocm_available_patch.stop()
        self.mps_available_patch.stop()
        
        # Reset the singleton instance
        from src.ai import gpu_acceleration
        gpu_acceleration._gpu_manager = None
    
    def test_gpu_type_enum(self):
        """Test the GPUType enum."""
        self.assertEqual(GPUType.NVIDIA.value, "nvidia")
        self.assertEqual(GPUType.AMD.value, "amd")
        self.assertEqual(GPUType.APPLE.value, "apple")
        self.assertEqual(GPUType.NONE.value, "none")
    
    def test_gpu_manager_initialization(self):
        """Test initialization of the GPU acceleration manager."""
        manager = GPUAccelerationManager()
        
        # Check that the manager detected NVIDIA GPU
        self.assertEqual(manager._gpu_type, GPUType.NVIDIA)
        self.assertEqual(manager._gpu_count, 1)
        self.assertEqual(manager._gpu_memory, [8 * 1024])  # 8 GB in MB
    
    def test_gpu_manager_is_available(self):
        """Test the is_available method."""
        manager = GPUAccelerationManager()
        self.assertTrue(manager.is_available())
        
        # Test with no GPU
        with patch('src.ai.gpu_acceleration.CUDA_AVAILABLE', False):
            with patch('src.ai.gpu_acceleration.ROCM_AVAILABLE', False):
                with patch('src.ai.gpu_acceleration.MPS_AVAILABLE', False):
                    # Reset the singleton instance
                    from src.ai import gpu_acceleration
                    gpu_acceleration._gpu_manager = None
                    
                    manager = GPUAccelerationManager()
                    self.assertFalse(manager.is_available())
    
    def test_get_gpu_info(self):
        """Test the get_gpu_info method."""
        manager = GPUAccelerationManager()
        info = manager.get_gpu_info()
        
        self.assertEqual(info["type"], "nvidia")
        self.assertEqual(info["count"], 1)
        self.assertEqual(info["memory"], [8 * 1024])
        self.assertTrue(info["cuda_available"])
        self.assertFalse(info["rocm_available"])
        self.assertFalse(info["mps_available"])
    
    def test_get_optimal_device_map(self):
        """Test the get_optimal_device_map method."""
        manager = GPUAccelerationManager()
        
        # Test with a small model that fits in GPU memory
        device_map = manager.get_optimal_device_map(4.0)  # 4 GB model
        self.assertEqual(device_map, "auto")
        
        # Test with a large model that doesn't fit in GPU memory
        device_map = manager.get_optimal_device_map(16.0)  # 16 GB model
        self.assertEqual(device_map, "cpu")
        
        # Test with no GPU
        with patch.object(manager, 'is_available', return_value=False):
            device_map = manager.get_optimal_device_map(4.0)
            self.assertEqual(device_map, "cpu")
    
    def test_get_optimal_dtype(self):
        """Test the get_optimal_dtype method."""
        manager = GPUAccelerationManager()
        
        # Test with NVIDIA GPU with bfloat16 support
        dtype = manager.get_optimal_dtype()
        self.assertEqual(dtype, 'bfloat16')
        
        # Test with NVIDIA GPU without bfloat16 support
        self.mock_torch.cuda.is_bf16_supported.return_value = False
        dtype = manager.get_optimal_dtype()
        self.assertEqual(dtype, 'float16')
        
        # Test with AMD GPU
        with patch.object(manager, '_gpu_type', GPUType.AMD):
            dtype = manager.get_optimal_dtype()
            self.assertEqual(dtype, 'float16')
        
        # Test with Apple GPU
        with patch.object(manager, '_gpu_type', GPUType.APPLE):
            dtype = manager.get_optimal_dtype()
            self.assertEqual(dtype, 'float16')
        
        # Test with no GPU
        with patch.object(manager, '_gpu_type', GPUType.NONE):
            dtype = manager.get_optimal_dtype()
            self.assertEqual(dtype, 'float32')
    
    def test_get_optimal_quantization(self):
        """Test the get_optimal_quantization method."""
        manager = GPUAccelerationManager()
        
        # Test with a small model that fits in GPU memory
        quantization = manager.get_optimal_quantization(4.0)  # 4 GB model
        self.assertIsNone(quantization)
        
        # Test with a large model that doesn't fit in GPU memory
        quantization = manager.get_optimal_quantization(12.0)  # 12 GB model
        self.assertEqual(quantization, "8bit")
        
        # Test with a very large model
        quantization = manager.get_optimal_quantization(24.0)  # 24 GB model
        self.assertEqual(quantization, "4bit")
        
        # Test with no GPU
        with patch.object(manager, 'is_available', return_value=False):
            # Small model on CPU
            quantization = manager.get_optimal_quantization(0.5)
            self.assertIsNone(quantization)
            
            # Large model on CPU
            quantization = manager.get_optimal_quantization(2.0)
            self.assertEqual(quantization, "8bit")
    
    def test_optimize_for_inference(self):
        """Test the optimize_for_inference method."""
        manager = GPUAccelerationManager()
        
        # Create a mock model
        mock_model = MagicMock()
        mock_model.cuda.return_value = mock_model
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model
        mock_model.half.return_value = mock_model
        
        # Test with NVIDIA GPU
        optimized_model = manager.optimize_for_inference(mock_model)
        mock_model.cuda.assert_called_once()
        mock_model.eval.assert_called_once()
        mock_model.half.assert_called_once()
        
        # Test with AMD GPU
        mock_model.reset_mock()
        with patch.object(manager, '_gpu_type', GPUType.AMD):
            optimized_model = manager.optimize_for_inference(mock_model)
            mock_model.cuda.assert_called_once()
            mock_model.eval.assert_called_once()
            mock_model.half.assert_called_once()
        
        # Test with Apple GPU
        mock_model.reset_mock()
        with patch.object(manager, '_gpu_type', GPUType.APPLE):
            optimized_model = manager.optimize_for_inference(mock_model)
            mock_model.to.assert_called_once_with("mps")
            mock_model.eval.assert_called_once()
            mock_model.half.assert_not_called()  # half() not called for Apple
        
        # Test with no GPU
        mock_model.reset_mock()
        with patch.object(manager, 'is_available', return_value=False):
            optimized_model = manager.optimize_for_inference(mock_model)
            mock_model.cuda.assert_not_called()
            mock_model.to.assert_not_called()
            mock_model.eval.assert_not_called()
    
    def test_get_transformers_config(self):
        """Test the get_transformers_config method."""
        manager = GPUAccelerationManager()
        
        # Test with a small model that fits in GPU memory
        config = manager.get_transformers_config(4.0)  # 4 GB model
        self.assertEqual(config["device_map"], "auto")
        self.assertEqual(config["torch_dtype"], 'bfloat16')
        self.assertNotIn("load_in_8bit", config)
        self.assertNotIn("load_in_4bit", config)
        
        # Test with a large model that doesn't fit in GPU memory
        config = manager.get_transformers_config(12.0)  # 12 GB model
        self.assertEqual(config["device_map"], "cpu")
        self.assertEqual(config["torch_dtype"], 'bfloat16')
        self.assertTrue(config["load_in_8bit"])
        
        # Test with a very large model
        config = manager.get_transformers_config(24.0)  # 24 GB model
        self.assertEqual(config["device_map"], "cpu")
        self.assertEqual(config["torch_dtype"], 'bfloat16')
        self.assertTrue(config["load_in_4bit"])
        self.assertEqual(config["bnb_4bit_compute_dtype"], 'bfloat16')
        self.assertTrue(config["bnb_4bit_use_double_quant"])
        self.assertEqual(config["bnb_4bit_quant_type"], "nf4")
    
    def test_singleton_functions(self):
        """Test the singleton accessor functions."""
        # Test is_gpu_available
        self.assertTrue(is_gpu_available())
        
        # Test get_gpu_info
        info = get_gpu_info()
        self.assertEqual(info["type"], "nvidia")
        
        # Test get_optimal_device_map
        device_map = get_optimal_device_map(4.0)
        self.assertEqual(device_map, "auto")
        
        # Test get_optimal_dtype
        dtype = get_optimal_dtype()
        self.assertEqual(dtype, 'bfloat16')
        
        # Test get_optimal_quantization
        quantization = get_optimal_quantization(4.0)
        self.assertIsNone(quantization)
        
        # Test optimize_for_inference
        mock_model = MagicMock()
        mock_model.cuda.return_value = mock_model
        mock_model.eval.return_value = mock_model
        mock_model.half.return_value = mock_model
        
        optimized_model = optimize_for_inference(mock_model)
        mock_model.cuda.assert_called_once()
        
        # Test get_transformers_config
        config = get_transformers_config(4.0)
        self.assertEqual(config["device_map"], "auto")


class TestGPUAccelerationAMD(unittest.TestCase):
    """Test case for the GPU acceleration module with AMD GPU."""
    
    def setUp(self):
        """Set up the test case."""
        # Create patches for torch and related modules
        self.torch_patch = patch('src.ai.gpu_acceleration.torch', autospec=True)
        self.transformers_patch = patch('src.ai.gpu_acceleration.transformers', autospec=True)
        self.cuda_available_patch = patch('src.ai.gpu_acceleration.CUDA_AVAILABLE', False)
        self.rocm_available_patch = patch('src.ai.gpu_acceleration.ROCM_AVAILABLE', True)
        self.mps_available_patch = patch('src.ai.gpu_acceleration.MPS_AVAILABLE', False)
        
        # Start the patches
        self.mock_torch = self.torch_patch.start()
        self.mock_transformers = self.transformers_patch.start()
        self.cuda_available_patch.start()
        self.rocm_available_patch.start()
        self.mps_available_patch.start()
        
        # Configure the torch mock for ROCm
        self.mock_torch.hip = MagicMock()
        self.mock_torch.hip.is_available.return_value = True
        self.mock_torch.cuda.device_count.return_value = 1
        
        # Create a mock device properties object
        device_props = MagicMock()
        device_props.total_memory = 16 * 1024 * 1024 * 1024  # 16 GB
        self.mock_torch.cuda.get_device_properties.return_value = device_props
        
        # Set up dtype attributes
        self.mock_torch.float16 = 'float16'
        self.mock_torch.float32 = 'float32'
        self.mock_torch.bfloat16 = 'bfloat16'
        
        # Reset the singleton instance
        from src.ai import gpu_acceleration
        gpu_acceleration._gpu_manager = None
    
    def tearDown(self):
        """Tear down the test case."""
        # Stop all patches
        self.torch_patch.stop()
        self.transformers_patch.stop()
        self.cuda_available_patch.stop()
        self.rocm_available_patch.stop()
        self.mps_available_patch.stop()
        
        # Reset the singleton instance
        from src.ai import gpu_acceleration
        gpu_acceleration._gpu_manager = None
    
    def test_amd_gpu_detection(self):
        """Test detection of AMD GPU."""
        manager = GPUAccelerationManager()
        
        # Check that the manager detected AMD GPU
        self.assertEqual(manager._gpu_type, GPUType.AMD)
        self.assertEqual(manager._gpu_count, 1)
        self.assertEqual(manager._gpu_memory, [16 * 1024])  # 16 GB in MB
        
        # Check GPU info
        info = manager.get_gpu_info()
        self.assertEqual(info["type"], "amd")
        self.assertTrue(info["rocm_available"])
        self.assertFalse(info["cuda_available"])
    
    def test_amd_optimal_dtype(self):
        """Test optimal dtype for AMD GPU."""
        manager = GPUAccelerationManager()
        dtype = manager.get_optimal_dtype()
        self.assertEqual(dtype, 'float16')


class TestGPUAccelerationApple(unittest.TestCase):
    """Test case for the GPU acceleration module with Apple GPU."""
    
    def setUp(self):
        """Set up the test case."""
        # Create patches for torch and related modules
        self.torch_patch = patch('src.ai.gpu_acceleration.torch', autospec=True)
        self.transformers_patch = patch('src.ai.gpu_acceleration.transformers', autospec=True)
        self.cuda_available_patch = patch('src.ai.gpu_acceleration.CUDA_AVAILABLE', False)
        self.rocm_available_patch = patch('src.ai.gpu_acceleration.ROCM_AVAILABLE', False)
        self.mps_available_patch = patch('src.ai.gpu_acceleration.MPS_AVAILABLE', True)
        
        # Start the patches
        self.mock_torch = self.torch_patch.start()
        self.mock_transformers = self.transformers_patch.start()
        self.cuda_available_patch.start()
        self.rocm_available_patch.start()
        self.mps_available_patch.start()
        
        # Configure the torch mock for MPS
        self.mock_torch.backends = MagicMock()
        self.mock_torch.backends.mps.is_available.return_value = True
        
        # Set up dtype attributes
        self.mock_torch.float16 = 'float16'
        self.mock_torch.float32 = 'float32'
        self.mock_torch.bfloat16 = 'bfloat16'
        
        # Mock platform for Apple detection
        self.platform_patch = patch('src.ai.gpu_acceleration.platform', autospec=True)
        self.mock_platform = self.platform_patch.start()
        self.mock_platform.system.return_value = "Darwin"
        
        # Mock subprocess for system_profiler
        self.subprocess_patch = patch('src.ai.gpu_acceleration.subprocess', autospec=True)
        self.mock_subprocess = self.subprocess_patch.start()
        
        # Configure subprocess mock to return GPU memory info
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
        Graphics/Displays:
            Apple M1 Pro:
              Chipset Model: Apple M1 Pro
              Type: GPU
              Bus: Built-In
              VRAM (Dynamic, Max): 16 GB
        """
        self.mock_subprocess.run.return_value = mock_result
        
        # Reset the singleton instance
        from src.ai import gpu_acceleration
        gpu_acceleration._gpu_manager = None
    
    def tearDown(self):
        """Tear down the test case."""
        # Stop all patches
        self.torch_patch.stop()
        self.transformers_patch.stop()
        self.cuda_available_patch.stop()
        self.rocm_available_patch.stop()
        self.mps_available_patch.stop()
        self.platform_patch.stop()
        self.subprocess_patch.stop()
        
        # Reset the singleton instance
        from src.ai import gpu_acceleration
        gpu_acceleration._gpu_manager = None
    
    def test_apple_gpu_detection(self):
        """Test detection of Apple GPU."""
        manager = GPUAccelerationManager()
        
        # Check that the manager detected Apple GPU
        self.assertEqual(manager._gpu_type, GPUType.APPLE)
        self.assertEqual(manager._gpu_count, 1)
        self.assertEqual(manager._gpu_memory, [16 * 1024])  # 16 GB in MB
        
        # Check GPU info
        info = manager.get_gpu_info()
        self.assertEqual(info["type"], "apple")
        self.assertTrue(info["mps_available"])
        self.assertFalse(info["cuda_available"])
        self.assertFalse(info["rocm_available"])
    
    def test_apple_optimal_dtype(self):
        """Test optimal dtype for Apple GPU."""
        manager = GPUAccelerationManager()
        dtype = manager.get_optimal_dtype()
        self.assertEqual(dtype, 'float16')
    
    def test_apple_optimize_for_inference(self):
        """Test optimize_for_inference for Apple GPU."""
        manager = GPUAccelerationManager()
        
        # Create a mock model
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model
        
        # Test with Apple GPU
        optimized_model = manager.optimize_for_inference(mock_model)
        mock_model.to.assert_called_once_with("mps")
        mock_model.eval.assert_called_once()
        # half() should not be called for Apple
        self.assertFalse(hasattr(mock_model, 'half') and mock_model.half.called)


if __name__ == '__main__':
    unittest.main()
