#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the dataset preparation module.
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add src directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ai.dataset_preparation import DatasetPreparation


class TestDatasetPreparation(unittest.TestCase):
    """Test cases for the dataset preparation module."""
    
    def setUp(self):
        """Set up the test case."""
        self.dataset_preparation = DatasetPreparation()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
    
    def tearDown(self):
        """Tear down the test case."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_load_json_dataset(self):
        """Test loading a dataset from a JSON file."""
        # Create a test JSON file
        test_data = [
            {"prompt": "What is Python?", "completion": "Python is a programming language."},
            {"prompt": "What is TensorFlow?", "completion": "TensorFlow is a machine learning framework."}
        ]
        
        test_file = os.path.join(self.test_dir, "test_dataset.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Load the dataset
        dataset = self.dataset_preparation.load_dataset(test_file, "JSON")
        
        # Check the dataset
        self.assertEqual(dataset["format"], "instruction")
        self.assertEqual(len(dataset["data"]), 2)
        self.assertEqual(dataset["data"][0]["prompt"], "What is Python?")
        self.assertEqual(dataset["data"][0]["completion"], "Python is a programming language.")
    
    def test_load_csv_dataset(self):
        """Test loading a dataset from a CSV file."""
        # Create a test CSV file
        test_file = os.path.join(self.test_dir, "test_dataset.csv")
        with open(test_file, 'w', encoding='utf-8', newline='') as f:
            f.write("prompt,completion\n")
            f.write("What is Python?,Python is a programming language.\n")
            f.write("What is TensorFlow?,TensorFlow is a machine learning framework.\n")
        
        # Load the dataset
        dataset = self.dataset_preparation.load_dataset(test_file, "CSV")
        
        # Check the dataset
        self.assertEqual(dataset["format"], "instruction")
        self.assertEqual(len(dataset["data"]), 2)
        self.assertEqual(dataset["data"][0]["prompt"], "What is Python?")
        self.assertEqual(dataset["data"][0]["completion"], "Python is a programming language.")
    
    def test_load_jsonl_dataset(self):
        """Test loading a dataset from a JSONL file."""
        # Create a test JSONL file
        test_file = os.path.join(self.test_dir, "test_dataset.jsonl")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('{"prompt": "What is Python?", "completion": "Python is a programming language."}\n')
            f.write('{"prompt": "What is TensorFlow?", "completion": "TensorFlow is a machine learning framework."}\n')
        
        # Load the dataset
        dataset = self.dataset_preparation.load_dataset(test_file, "JSONL")
        
        # Check the dataset
        self.assertEqual(dataset["format"], "instruction")
        self.assertEqual(len(dataset["data"]), 2)
        self.assertEqual(dataset["data"][0]["prompt"], "What is Python?")
        self.assertEqual(dataset["data"][0]["completion"], "Python is a programming language.")
    
    def test_load_txt_dataset(self):
        """Test loading a dataset from a text file."""
        # Create a test text file
        test_file = os.path.join(self.test_dir, "test_dataset.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("This is the first sample.\n\n")
            f.write("This is the second sample.\n\n")
            f.write("This is the third sample.")
        
        # Load the dataset
        dataset = self.dataset_preparation.load_dataset(test_file, "TXT")
        
        # Check the dataset
        self.assertEqual(dataset["format"], "text")
        self.assertEqual(len(dataset["data"]), 3)
        self.assertEqual(dataset["data"][0]["text"], "This is the first sample.")
        self.assertEqual(dataset["data"][1]["text"], "This is the second sample.")
        self.assertEqual(dataset["data"][2]["text"], "This is the third sample.")
    
    def test_detect_dataset_format(self):
        """Test detecting the format of a dataset."""
        # Test instruction format
        data = [
            {"prompt": "What is Python?", "completion": "Python is a programming language."},
            {"prompt": "What is TensorFlow?", "completion": "TensorFlow is a machine learning framework."}
        ]
        self.assertEqual(self.dataset_preparation._detect_dataset_format(data), "instruction")
        
        # Test text format
        data = [
            {"text": "This is the first sample."},
            {"text": "This is the second sample."}
        ]
        self.assertEqual(self.dataset_preparation._detect_dataset_format(data), "text")
        
        # Test conversation format
        data = [
            {"messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."}
            ]},
            {"messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is TensorFlow?"},
                {"role": "assistant", "content": "TensorFlow is a machine learning framework."}
            ]}
        ]
        self.assertEqual(self.dataset_preparation._detect_dataset_format(data), "conversation")
        
        # Test OpenAI conversation format
        data = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."}
        ]
        self.assertEqual(self.dataset_preparation._detect_dataset_format(data), "conversation")
    
    def test_preprocess_text_dataset(self):
        """Test preprocessing a text dataset."""
        # Create a test dataset
        data = [
            {"text": "This is a short sample."},
            {"text": "This is a longer sample that exceeds the maximum length." * 10},
            {"text": ""}  # Empty sample should be skipped
        ]
        
        # Preprocess the dataset
        processed_data = self.dataset_preparation._preprocess_text_dataset(data, max_length=20)
        
        # Check the processed dataset
        self.assertEqual(len(processed_data), 2)  # Empty sample should be skipped
        self.assertEqual(processed_data[0]["text"], "This is a short sample.")
        self.assertTrue(len(processed_data[1]["text"]) <= 20 * 4)  # Should be truncated
    
    def test_preprocess_instruction_dataset(self):
        """Test preprocessing an instruction dataset."""
        # Create a test dataset
        data = [
            {"prompt": "What is Python?", "completion": "Python is a programming language."},
            {"prompt": "What is TensorFlow?" * 10, "completion": "TensorFlow is a machine learning framework." * 10},
            {"prompt": "", "completion": "This should be skipped."},
            {"prompt": "This should be skipped.", "completion": ""}
        ]
        
        # Preprocess the dataset
        processed_data = self.dataset_preparation._preprocess_instruction_dataset(data, max_length=20)
        
        # Check the processed dataset
        self.assertEqual(len(processed_data), 2)  # Empty samples should be skipped
        self.assertEqual(processed_data[0]["prompt"], "What is Python?")
        self.assertEqual(processed_data[0]["completion"], "Python is a programming language.")
        self.assertTrue(len(processed_data[1]["prompt"]) <= 20 * 4 // 3)  # Should be truncated
        self.assertTrue(len(processed_data[1]["completion"]) <= 20 * 4 * 2 // 3)  # Should be truncated
    
    def test_preprocess_conversation_dataset(self):
        """Test preprocessing a conversation dataset."""
        # Create a test dataset
        data = [
            {"messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."}
            ]},
            {"messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is TensorFlow?" * 10},
                {"role": "assistant", "content": "TensorFlow is a machine learning framework." * 10}
            ]},
            {"messages": []}  # Empty conversation should be skipped
        ]
        
        # Preprocess the dataset
        processed_data = self.dataset_preparation._preprocess_conversation_dataset(data, max_length=20)
        
        # Check the processed dataset
        self.assertEqual(len(processed_data), 2)  # Empty conversation should be skipped
        self.assertEqual(len(processed_data[0]["messages"]), 3)
        self.assertEqual(processed_data[0]["messages"][0]["role"], "system")
        self.assertEqual(processed_data[0]["messages"][0]["content"], "You are a helpful assistant.")
        
        # The second conversation should be truncated
        total_length = sum(len(m["content"]) for m in processed_data[1]["messages"])
        self.assertTrue(total_length <= 20 * 4)
    
    def test_remove_duplicates(self):
        """Test removing duplicates from a dataset."""
        # Test text format
        data = [
            {"text": "This is a sample."},
            {"text": "This is a sample."},  # Duplicate
            {"text": "This is another sample."}
        ]
        unique_data = self.dataset_preparation._remove_duplicates(data, "text")
        self.assertEqual(len(unique_data), 2)
        
        # Test instruction format
        data = [
            {"prompt": "What is Python?", "completion": "Python is a programming language."},
            {"prompt": "What is Python?", "completion": "Python is a programming language."},  # Duplicate
            {"prompt": "What is TensorFlow?", "completion": "TensorFlow is a machine learning framework."}
        ]
        unique_data = self.dataset_preparation._remove_duplicates(data, "instruction")
        self.assertEqual(len(unique_data), 2)
        
        # Test conversation format
        data = [
            {"messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."}
            ]},
            {"messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."}
            ]},  # Duplicate
            {"messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is TensorFlow?"},
                {"role": "assistant", "content": "TensorFlow is a machine learning framework."}
            ]}
        ]
        unique_data = self.dataset_preparation._remove_duplicates(data, "conversation")
        self.assertEqual(len(unique_data), 2)
    
    def test_format_for_training(self):
        """Test formatting a dataset for training."""
        # Create a test dataset
        dataset = {
            "format": "instruction",
            "train_data": [
                {"prompt": "What is Python?", "completion": "Python is a programming language."}
            ],
            "eval_data": [
                {"prompt": "What is TensorFlow?", "completion": "TensorFlow is a machine learning framework."}
            ]
        }
        
        # Format for LoRA
        lora_dataset = self.dataset_preparation.format_for_training(dataset, "lora")
        self.assertEqual(lora_dataset["format"], "instruction")
        self.assertEqual(lora_dataset["adapter_type"], "lora")
        self.assertEqual(lora_dataset["train_data"][0]["prompt"], "What is Python?")
        self.assertEqual(lora_dataset["train_data"][0]["completion"], "Python is a programming language.")
        
        # Format for QLoRA
        qlora_dataset = self.dataset_preparation.format_for_training(dataset, "qlora")
        self.assertEqual(qlora_dataset["format"], "instruction")
        self.assertEqual(qlora_dataset["adapter_type"], "qlora")
        self.assertEqual(qlora_dataset["train_data"][0]["prompt"], "What is Python?")
        self.assertEqual(qlora_dataset["train_data"][0]["completion"], "Python is a programming language.")
        
        # Format for Prefix Tuning
        prefix_dataset = self.dataset_preparation.format_for_training(dataset, "prefix_tuning")
        self.assertEqual(prefix_dataset["format"], "instruction")
        self.assertEqual(prefix_dataset["adapter_type"], "prefix_tuning")
        self.assertEqual(prefix_dataset["train_data"][0]["prompt"], "<|prefix|> What is Python?")
        self.assertEqual(prefix_dataset["train_data"][0]["completion"], "Python is a programming language.")
    
    def test_save_dataset(self):
        """Test saving a dataset to disk."""
        # Create a test dataset
        dataset = {
            "format": "instruction",
            "adapter_type": "lora",
            "train_data": [
                {"prompt": "What is Python?", "completion": "Python is a programming language."}
            ],
            "eval_data": [
                {"prompt": "What is TensorFlow?", "completion": "TensorFlow is a machine learning framework."}
            ]
        }
        
        # Save the dataset
        output_dir = os.path.join(self.test_dir, "output")
        paths = self.dataset_preparation.save_dataset(dataset, output_dir)
        
        # Check that the files were created
        self.assertTrue(os.path.exists(paths["train_path"]))
        self.assertTrue(os.path.exists(paths["eval_path"]))
        self.assertTrue(os.path.exists(paths["metadata_path"]))
        
        # Check the content of the files
        with open(paths["train_path"], 'r', encoding='utf-8') as f:
            train_data = [json.loads(line) for line in f]
        self.assertEqual(len(train_data), 1)
        self.assertEqual(train_data[0]["prompt"], "What is Python?")
        self.assertEqual(train_data[0]["completion"], "Python is a programming language.")
        
        with open(paths["eval_path"], 'r', encoding='utf-8') as f:
            eval_data = [json.loads(line) for line in f]
        self.assertEqual(len(eval_data), 1)
        self.assertEqual(eval_data[0]["prompt"], "What is TensorFlow?")
        self.assertEqual(eval_data[0]["completion"], "TensorFlow is a machine learning framework.")
        
        with open(paths["metadata_path"], 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        self.assertEqual(metadata["format"], "instruction")
        self.assertEqual(metadata["adapter_type"], "lora")
        self.assertEqual(metadata["train_samples"], 1)
        self.assertEqual(metadata["eval_samples"], 1)
    
    def test_analyze_dataset(self):
        """Test analyzing a dataset."""
        # Create a test dataset
        dataset = {
            "format": "instruction",
            "train_data": [
                {"prompt": "What is Python?", "completion": "Python is a programming language."},
                {"prompt": "What is TensorFlow?", "completion": "TensorFlow is a machine learning framework."}
            ],
            "eval_data": [
                {"prompt": "What is PyTorch?", "completion": "PyTorch is a machine learning framework."}
            ]
        }
        
        # Analyze the dataset
        stats = self.dataset_preparation.analyze_dataset(dataset)
        
        # Check the statistics
        self.assertEqual(stats["format"], "instruction")
        self.assertEqual(stats["total_samples"], 3)
        self.assertEqual(stats["train_samples"], 2)
        self.assertEqual(stats["eval_samples"], 1)
        self.assertAlmostEqual(stats["train_eval_ratio"], 2/3)
        
        # Check instruction-specific statistics
        self.assertTrue("avg_prompt_length" in stats)
        self.assertTrue("avg_completion_length" in stats)
        self.assertTrue("total_prompt_tokens" in stats)
        self.assertTrue("total_completion_tokens" in stats)
        self.assertTrue("total_tokens" in stats)
    
    def test_preprocess_dataset(self):
        """Test preprocessing a dataset."""
        # Create a test dataset
        dataset = {
            "format": "instruction",
            "data": [
                {"prompt": "What is Python?", "completion": "Python is a programming language."},
                {"prompt": "What is TensorFlow?", "completion": "TensorFlow is a machine learning framework."},
                {"prompt": "What is PyTorch?", "completion": "PyTorch is a machine learning framework."},
                {"prompt": "What is Keras?", "completion": "Keras is a high-level neural networks API."}
            ]
        }
        
        # Preprocess the dataset
        preprocessed = self.dataset_preparation.preprocess_dataset(
            dataset,
            max_length=512,
            remove_duplicates=True,
            shuffle=False,  # Disable shuffling for deterministic testing
            train_split=0.75
        )
        
        # Check the preprocessed dataset
        self.assertEqual(preprocessed["format"], "instruction")
        self.assertEqual(len(preprocessed["train_data"]), 3)
        self.assertEqual(len(preprocessed["eval_data"]), 1)
        
        # Check that the data was split correctly
        self.assertEqual(preprocessed["train_data"][0]["prompt"], "What is Python?")
        self.assertEqual(preprocessed["train_data"][0]["completion"], "Python is a programming language.")
        self.assertEqual(preprocessed["eval_data"][0]["prompt"], "What is Keras?")
        self.assertEqual(preprocessed["eval_data"][0]["completion"], "Keras is a high-level neural networks API.")


if __name__ == '__main__':
    unittest.main()
