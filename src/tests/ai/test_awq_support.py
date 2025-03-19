"""
Tests for the AWQ support module.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import asyncio
import os
import sys
import torch
import pytest

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ai.awq_support import AWQModelManager, get_awq_manager


class TestAWQModelManager(unittest.TestCase):
    """Test the AWQModelManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a fresh instance for each test
        self.manager = AWQModelManager()
        
        # Mock the autoawq module
        self.autoawq_mock = MagicMock()
        self.autoawq_for_causal_lm_mock = MagicMock()
        
        # Set up patches
        self.autoawq_patch = patch.dict('sys.modules', {'autoawq': self.autoawq_mock})
        
        # Start patches
        self.autoawq_patch.start()
        
        # Set up the AutoAWQForCausalLM mock
        self.autoawq_mock.AutoAWQForCausalLM = self.autoawq_for_causal_lm_mock
        
        # Mock torch.cuda.is_available
        self.cuda_available_patch = patch('torch.cuda.is_available', return_value=True)
        self.cuda_available_patch.start()
        
        # Mock progress_callbacks
        self.create_progress_operation_mock = MagicMock(return_value='op_id')
        self.update_progress_operation_mock = MagicMock()
        
        self.create_progress_patch = patch(
            'ai.awq_support.create_progress_operation', 
            self.create_progress_operation_mock
        )
        self.update_progress_patch = patch(
            'ai.awq_support.update_progress_operation', 
            self.update_progress_operation_mock
        )
        
        self.create_progress_patch.start()
        self.update_progress_patch.start()
        
        # Mock AutoTokenizer
        self.tokenizer_mock = MagicMock()
        self.auto_tokenizer_mock = MagicMock(return_value=self.tokenizer_mock)
        self.auto_tokenizer_patch = patch(
            'ai.awq_support.AutoTokenizer.from_pretrained', 
            self.auto_tokenizer_mock
        )
        self.auto_tokenizer_patch.start()
    
    def tearDown(self):
        """Tear down the test environment."""
        # Stop all patches
        self.autoawq_patch.stop()
        self.cuda_available_patch.stop()
        self.create_progress_patch.stop()
        self.update_progress_patch.stop()
        self.auto_tokenizer_patch.stop()
    
    def test_check_dependencies(self):
        """Test the _check_dependencies method."""
        # Test with dependencies available
        result = self.manager._check_dependencies()
        self.assertTrue(result)
        
        # Test with dependencies not available
        self.autoawq_patch.stop()
        with patch.dict('sys.modules', {'autoawq': None}):
            with patch('ai.awq_support.logger') as logger_mock:
                result = self.manager._check_dependencies()
                self.assertFalse(result)
                logger_mock.warning.assert_called_once()
        
        # Restart the patch for other tests
        self.autoawq_patch.start()
    
    def test_is_available(self):
        """Test the is_available method."""
        # Test with dependencies and CUDA available
        result = self.manager.is_available()
        self.assertTrue(result)
        
        # Test with CUDA not available
        self.cuda_available_patch.stop()
        with patch('torch.cuda.is_available', return_value=False):
            result = self.manager.is_available()
            self.assertFalse(result)
        
        # Restart the patch for other tests
        self.cuda_available_patch.start()
        
        # Test with dependencies not available
        self.autoawq_patch.stop()
        with patch.dict('sys.modules', {'autoawq': None}):
            result = self.manager.is_available()
            self.assertFalse(result)
        
        # Restart the patch for other tests
        self.autoawq_patch.start()
    
    def test_load_model(self):
        """Test the load_model method."""
        # Mock the model
        model_mock = MagicMock()
        self.autoawq_for_causal_lm_mock.from_quantized.return_value = model_mock
        
        # Test loading a model
        model, tokenizer = self.manager.load_model('test_model')
        
        # Check that the model was loaded correctly
        self.assertEqual(model, model_mock)
        self.assertEqual(tokenizer, self.tokenizer_mock)
        
        # Check that the model was stored correctly
        self.assertEqual(self.manager.loaded_models['test_model'], model_mock)
        self.assertEqual(self.manager.tokenizers['test_model'], self.tokenizer_mock)
        
        # Check that the progress operations were called correctly
        self.create_progress_operation_mock.assert_called_once()
        self.assertEqual(self.update_progress_operation_mock.call_count, 5)
        
        # Check that the model loading function was called correctly
        self.autoawq_for_causal_lm_mock.from_quantized.assert_called_once_with(
            'test_model',
            device_map='auto'
        )
    
    def test_load_model_with_device(self):
        """Test the load_model method with a specific device."""
        # Mock the model
        model_mock = MagicMock()
        self.autoawq_for_causal_lm_mock.from_quantized.return_value = model_mock
        
        # Test loading a model with a specific device
        model, tokenizer = self.manager.load_model('test_model', device='cpu')
        
        # Check that the model loading function was called correctly
        self.autoawq_for_causal_lm_mock.from_quantized.assert_called_once_with(
            'test_model',
            device_map='cpu'
        )
    
    def test_load_model_with_device_map(self):
        """Test the load_model method with a specific device map."""
        # Mock the model
        model_mock = MagicMock()
        self.autoawq_for_causal_lm_mock.from_quantized.return_value = model_mock
        
        # Test loading a model with a specific device map
        device_map = {'model.embed_tokens': 0, 'model.layers.0': 0, 'model.layers.1': 1}
        model, tokenizer = self.manager.load_model('test_model', device_map=device_map)
        
        # Check that the model loading function was called correctly
        self.autoawq_for_causal_lm_mock.from_quantized.assert_called_once_with(
            'test_model',
            device_map=device_map
        )
    
    def test_load_model_with_kwargs(self):
        """Test the load_model method with additional kwargs."""
        # Mock the model
        model_mock = MagicMock()
        self.autoawq_for_causal_lm_mock.from_quantized.return_value = model_mock
        
        # Test loading a model with additional kwargs
        model, tokenizer = self.manager.load_model(
            'test_model',
            trust_remote_code=True,
            revision='main'
        )
        
        # Check that the model loading function was called correctly
        self.autoawq_for_causal_lm_mock.from_quantized.assert_called_once_with(
            'test_model',
            device_map='auto',
            trust_remote_code=True,
            revision='main'
        )
    
    def test_load_model_error(self):
        """Test the load_model method with an error."""
        # Mock the model loading function to raise an exception
        self.autoawq_for_causal_lm_mock.from_quantized.side_effect = RuntimeError('Test error')
        
        # Test loading a model with an error
        with self.assertRaises(RuntimeError):
            self.manager.load_model('test_model')
        
        # Check that the progress operations were called correctly
        self.create_progress_operation_mock.assert_called_once()
        self.assertEqual(self.update_progress_operation_mock.call_count, 4)
        
        # Check that the last update_progress_operation call had is_error=True
        last_call = self.update_progress_operation_mock.call_args_list[-1]
        self.assertEqual(last_call[0][0], 'op_id')
        self.assertIn('Error loading model', last_call[0][1])
        self.assertEqual(last_call[0][2], 1.0)
        self.assertEqual(last_call[1]['is_complete'], True)
        self.assertEqual(last_call[1]['is_error'], True)
    
    def test_unload_model(self):
        """Test the unload_model method."""
        # Mock the model
        model_mock = MagicMock()
        tokenizer_mock = MagicMock()
        
        # Add a model to the manager
        self.manager.loaded_models['test_model'] = model_mock
        self.manager.tokenizers['test_model'] = tokenizer_mock
        
        # Test unloading a model
        with patch('gc.collect') as gc_mock, patch('torch.cuda.empty_cache') as empty_cache_mock:
            result = self.manager.unload_model('test_model')
        
        # Check that the model was unloaded correctly
        self.assertTrue(result)
        self.assertNotIn('test_model', self.manager.loaded_models)
        self.assertNotIn('test_model', self.manager.tokenizers)
        
        # Check that the garbage collection was called
        gc_mock.assert_called_once()
        empty_cache_mock.assert_called_once()
    
    def test_unload_model_not_found(self):
        """Test the unload_model method with a model that doesn't exist."""
        # Test unloading a model that doesn't exist
        with patch('ai.awq_support.logger') as logger_mock:
            result = self.manager.unload_model('nonexistent_model')
        
        # Check that the method returned False
        self.assertFalse(result)
        
        # Check that a warning was logged
        logger_mock.warning.assert_called_once()
    
    def test_generate_text(self):
        """Test the generate_text method."""
        # Mock the model and tokenizer
        model_mock = MagicMock()
        tokenizer_mock = MagicMock()
        
        # Mock the generate method
        output_ids_mock = MagicMock()
        model_mock.generate.return_value = output_ids_mock
        
        # Mock the tokenizer
        input_ids_mock = MagicMock()
        inputs_mock = MagicMock()
        inputs_mock.input_ids = input_ids_mock
        tokenizer_mock.return_value = inputs_mock
        
        # Mock the decode method
        tokenizer_mock.decode.return_value = 'Generated text'
        
        # Add the model and tokenizer to the manager
        self.manager.loaded_models['test_model'] = model_mock
        self.manager.tokenizers['test_model'] = tokenizer_mock
        
        # Test generating text
        result = self.manager.generate_text(
            'test_model',
            'Test prompt',
            max_new_tokens=100,
            temperature=0.8,
            top_p=0.9,
            top_k=40,
            repetition_penalty=1.2
        )
        
        # Check that the result is correct
        self.assertEqual(result, 'Generated text')
        
        # Check that the tokenizer was called correctly
        tokenizer_mock.assert_called_once_with('Test prompt', return_tensors='pt')
        
        # Check that the generate method was called correctly
        model_mock.generate.assert_called_once()
        args, kwargs = model_mock.generate.call_args
        self.assertEqual(args[0], input_ids_mock.to.return_value)
        self.assertEqual(kwargs['max_new_tokens'], 100)
        self.assertEqual(kwargs['temperature'], 0.8)
        self.assertEqual(kwargs['top_p'], 0.9)
        self.assertEqual(kwargs['top_k'], 40)
        self.assertEqual(kwargs['repetition_penalty'], 1.2)
        self.assertEqual(kwargs['do_sample'], True)
        
        # Check that the decode method was called correctly
        tokenizer_mock.decode.assert_called_once_with(output_ids_mock[0], skip_special_tokens=True)
    
    def test_generate_text_no_sampling(self):
        """Test the generate_text method with no sampling."""
        # Mock the model and tokenizer
        model_mock = MagicMock()
        tokenizer_mock = MagicMock()
        
        # Mock the generate method
        output_ids_mock = MagicMock()
        model_mock.generate.return_value = output_ids_mock
        
        # Mock the tokenizer
        input_ids_mock = MagicMock()
        inputs_mock = MagicMock()
        inputs_mock.input_ids = input_ids_mock
        tokenizer_mock.return_value = inputs_mock
        
        # Mock the decode method
        tokenizer_mock.decode.return_value = 'Generated text'
        
        # Add the model and tokenizer to the manager
        self.manager.loaded_models['test_model'] = model_mock
        self.manager.tokenizers['test_model'] = tokenizer_mock
        
        # Test generating text with temperature=0 (no sampling)
        result = self.manager.generate_text(
            'test_model',
            'Test prompt',
            temperature=0
        )
        
        # Check that do_sample is False
        args, kwargs = model_mock.generate.call_args
        self.assertEqual(kwargs['do_sample'], False)
    
    def test_generate_text_model_not_loaded(self):
        """Test the generate_text method with a model that isn't loaded."""
        # Test generating text with a model that isn't loaded
        with self.assertRaises(ValueError):
            self.manager.generate_text('nonexistent_model', 'Test prompt')
    
    @pytest.mark.asyncio
    async def test_generate_text_async(self):
        """Test the generate_text_async method."""
        # Mock the generate_text method
        self.manager.generate_text = MagicMock(return_value='Generated text')
        
        # Test generating text asynchronously
        result = await self.manager.generate_text_async(
            'test_model',
            'Test prompt',
            max_new_tokens=100,
            temperature=0.8,
            top_p=0.9,
            top_k=40,
            repetition_penalty=1.2
        )
        
        # Check that the result is correct
        self.assertEqual(result, 'Generated text')
        
        # Check that the generate_text method was called correctly
        self.manager.generate_text.assert_called_once_with(
            'test_model',
            'Test prompt',
            100,
            0.8,
            0.9,
            40,
            1.2
        )
    
    def test_generate_text_stream(self):
        """Test the generate_text_stream method."""
        # Mock the model and tokenizer
        model_mock = MagicMock()
        tokenizer_mock = MagicMock()
        
        # Mock the tokenizer
        input_ids_mock = MagicMock()
        inputs_mock = MagicMock()
        inputs_mock.input_ids = input_ids_mock
        tokenizer_mock.return_value = inputs_mock
        
        # Add the model and tokenizer to the manager
        self.manager.loaded_models['test_model'] = model_mock
        self.manager.tokenizers['test_model'] = tokenizer_mock
        
        # Mock the TextIteratorStreamer
        streamer_mock = MagicMock()
        with patch('ai.awq_support.TextIteratorStreamer', return_value=streamer_mock):
            # Test generating text with streaming
            result = self.manager.generate_text_stream(
                'test_model',
                'Test prompt',
                max_new_tokens=100,
                temperature=0.8,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.2
            )
        
        # Check that the result is correct
        self.assertEqual(result, streamer_mock)
        
        # Check that the tokenizer was called correctly
        tokenizer_mock.assert_called_once_with('Test prompt', return_tensors='pt')
        
        # Check that the executor.submit was called correctly
        self.manager.executor.submit.assert_called_once_with(
            model_mock.generate,
            input_ids=input_ids_mock.to.return_value,
            max_new_tokens=100,
            temperature=0.8,
            top_p=0.9,
            top_k=40,
            repetition_penalty=1.2,
            do_sample=True,
            streamer=streamer_mock
        )
    
    def test_generate_text_stream_with_callback(self):
        """Test the generate_text_stream method with a callback."""
        # Mock the model and tokenizer
        model_mock = MagicMock()
        tokenizer_mock = MagicMock()
        
        # Mock the tokenizer
        input_ids_mock = MagicMock()
        inputs_mock = MagicMock()
        inputs_mock.input_ids = input_ids_mock
        tokenizer_mock.return_value = inputs_mock
        
        # Add the model and tokenizer to the manager
        self.manager.loaded_models['test_model'] = model_mock
        self.manager.tokenizers['test_model'] = tokenizer_mock
        
        # Mock the TextIteratorStreamer
        streamer_mock = MagicMock()
        with patch('ai.awq_support.TextIteratorStreamer', return_value=streamer_mock):
            # Mock threading.Thread
            thread_mock = MagicMock()
            with patch('threading.Thread', return_value=thread_mock) as thread_class_mock:
                # Test generating text with streaming and a callback
                callback_mock = MagicMock()
                result = self.manager.generate_text_stream(
                    'test_model',
                    'Test prompt',
                    callback=callback_mock
                )
                
                # Check that threading.Thread was called correctly
                thread_class_mock.assert_called_once()
                thread_mock.start.assert_called_once()
    
    def test_generate_text_stream_model_not_loaded(self):
        """Test the generate_text_stream method with a model that isn't loaded."""
        # Test generating text with a model that isn't loaded
        with self.assertRaises(ValueError):
            self.manager.generate_text_stream('nonexistent_model', 'Test prompt')
    
    def test_chat_completion(self):
        """Test the chat_completion method."""
        # Mock the generate_text method
        self.manager.generate_text = MagicMock(return_value='Generated completion')
        
        # Mock the _format_chat_prompt method
        self.manager._format_chat_prompt = MagicMock(return_value='Formatted prompt')
        
        # Add a model to the manager
        self.manager.loaded_models['test_model'] = MagicMock()
        
        # Test generating a chat completion
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Hello!'}
        ]
        result = self.manager.chat_completion(
            'test_model',
            messages,
            max_new_tokens=100,
            temperature=0.8,
            top_p=0.9,
            top_k=40,
            repetition_penalty=1.2
        )
        
        # Check that the result is correct
        self.assertEqual(result, 'Generated completion')
        
        # Check that the _format_chat_prompt method was called correctly
        self.manager._format_chat_prompt.assert_called_once_with(messages)
        
        # Check that the generate_text method was called correctly
        self.manager.generate_text.assert_called_once_with(
            'test_model',
            'Formatted prompt',
            100,
            0.8,
            0.9,
            40,
            1.2
        )
    
    def test_chat_completion_model_not_loaded(self):
        """Test the chat_completion method with a model that isn't loaded."""
        # Test generating a chat completion with a model that isn't loaded
        with self.assertRaises(ValueError):
            self.manager.chat_completion('nonexistent_model', [])
    
    def test_format_chat_prompt(self):
        """Test the _format_chat_prompt method."""
        # Test formatting a chat prompt
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Hello!'},
            {'role': 'assistant', 'content': 'Hi there! How can I help you?'},
            {'role': 'user', 'content': 'What is the capital of France?'}
        ]
        result = self.manager._format_chat_prompt(messages)
        
        # Check that the result is correct
        expected = (
            "<|system|>\nYou are a helpful assistant.\n"
            "<|user|>\nHello!\n"
            "<|assistant|>\nHi there! How can I help you?\n"
            "<|user|>\nWhat is the capital of France?\n"
            "<|assistant|>\n"
        )
        self.assertEqual(result, expected)
    
    def test_format_chat_prompt_invalid_message(self):
        """Test the _format_chat_prompt method with an invalid message."""
        # Test formatting a chat prompt with an invalid message
        messages = [{'invalid': 'message'}]
        with self.assertRaises(ValueError):
            self.manager._format_chat_prompt(messages)
    
    def test_close(self):
        """Test the close method."""
        # Mock the unload_model method
        self.manager.unload_model = MagicMock()
        
        # Add some models to the manager
        self.manager.loaded_models = {
            'model1': MagicMock(),
            'model2': MagicMock()
        }
        
        # Test closing the manager
        with patch('ai.awq_support.logger') as logger_mock:
            self.manager.close()
        
        # Check that unload_model was called for each model
        self.manager.unload_model.assert_has_calls([
            call('model1'),
            call('model2')
        ], any_order=True)
        
        # Check that the executor was shut down
        self.manager.executor.shutdown.assert_called_once_with(wait=True)
        
        # Check that a log message was written
        logger_mock.info.assert_called_once()


class TestGetAWQManager(unittest.TestCase):
    """Test the get_awq_manager function."""
    
    def test_get_awq_manager(self):
        """Test the get_awq_manager function."""
        # Reset the singleton
        import ai.awq_support
        ai.awq_support._awq_manager = None
        
        # Test getting the manager
        with patch('ai.awq_support.AWQModelManager') as manager_mock:
            manager1 = get_awq_manager()
            manager2 = get_awq_manager()
            
            # Check that the manager was created once
            manager_mock.assert_called_once()
            
            # Check that the same instance was returned both times
            self.assertEqual(manager1, manager2)


if __name__ == '__main__':
    unittest.main()
