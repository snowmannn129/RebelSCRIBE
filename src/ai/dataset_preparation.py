#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Dataset Preparation Tools

This module provides tools for preparing datasets for model fine-tuning.
It supports various dataset formats and preprocessing operations.
"""

import os
import json
import csv
import logging
import random
from typing import List, Dict, Any, Tuple, Optional, Union, Callable
from pathlib import Path
import re

import numpy as np
from tqdm import tqdm

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class DatasetPreparation:
    """
    Dataset preparation tools for model fine-tuning.
    
    This class provides methods for loading, preprocessing, and formatting
    datasets for model fine-tuning. It supports various dataset formats
    including text, instruction, and conversation formats.
    """
    
    def __init__(self):
        """Initialize the dataset preparation tools."""
        logger.info("Initializing dataset preparation tools")
    
    def load_dataset(self, file_path: str, file_format: str) -> Dict[str, Any]:
        """
        Load a dataset from a file.
        
        Args:
            file_path: Path to the dataset file.
            file_format: Format of the dataset file (JSON, CSV, JSONL, TXT).
            
        Returns:
            A dictionary containing the loaded dataset.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is not supported.
        """
        logger.info(f"Loading dataset from {file_path} with format {file_format}")
        
        if not os.path.exists(file_path):
            logger.error(f"Dataset file not found: {file_path}")
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        try:
            if file_format.upper() == "JSON":
                return self._load_json_dataset(file_path)
            elif file_format.upper() == "CSV":
                return self._load_csv_dataset(file_path)
            elif file_format.upper() == "JSONL":
                return self._load_jsonl_dataset(file_path)
            elif file_format.upper() == "TXT":
                return self._load_txt_dataset(file_path)
            else:
                logger.error(f"Unsupported file format: {file_format}")
                raise ValueError(f"Unsupported file format: {file_format}")
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}", exc_info=True)
            raise
    
    def _load_json_dataset(self, file_path: str) -> Dict[str, Any]:
        """
        Load a dataset from a JSON file.
        
        Args:
            file_path: Path to the JSON file.
            
        Returns:
            A dictionary containing the loaded dataset.
        """
        logger.debug(f"Loading JSON dataset from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine dataset format based on content
            dataset_format = self._detect_dataset_format(data)
            
            return {
                "format": dataset_format,
                "data": data
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {str(e)}")
            raise ValueError(f"Invalid JSON file: {str(e)}")
    
    def _load_csv_dataset(self, file_path: str) -> Dict[str, Any]:
        """
        Load a dataset from a CSV file.
        
        Args:
            file_path: Path to the CSV file.
            
        Returns:
            A dictionary containing the loaded dataset.
        """
        logger.debug(f"Loading CSV dataset from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)
                rows = list(reader)
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                item = {}
                for i, field in enumerate(header):
                    if i < len(row):
                        item[field] = row[i]
                    else:
                        item[field] = ""
                data.append(item)
            
            # Determine dataset format based on header
            dataset_format = "text"  # Default format
            
            if "prompt" in header and "completion" in header:
                dataset_format = "instruction"
            elif "role" in header and "content" in header:
                dataset_format = "conversation"
            
            return {
                "format": dataset_format,
                "data": data
            }
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            raise ValueError(f"Error loading CSV file: {str(e)}")
    
    def _load_jsonl_dataset(self, file_path: str) -> Dict[str, Any]:
        """
        Load a dataset from a JSONL file.
        
        Args:
            file_path: Path to the JSONL file.
            
        Returns:
            A dictionary containing the loaded dataset.
        """
        logger.debug(f"Loading JSONL dataset from {file_path}")
        
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        item = json.loads(line)
                        data.append(item)
            
            # Determine dataset format based on content
            dataset_format = self._detect_dataset_format(data)
            
            return {
                "format": dataset_format,
                "data": data
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSONL file: {str(e)}")
            raise ValueError(f"Invalid JSONL file: {str(e)}")
    
    def _load_txt_dataset(self, file_path: str) -> Dict[str, Any]:
        """
        Load a dataset from a text file.
        
        Args:
            file_path: Path to the text file.
            
        Returns:
            A dictionary containing the loaded dataset.
        """
        logger.debug(f"Loading text dataset from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by double newlines to get separate text samples
            samples = [s.strip() for s in re.split(r'\n\s*\n', content) if s.strip()]
            
            # Convert to list of dictionaries
            data = [{"text": sample} for sample in samples]
            
            return {
                "format": "text",
                "data": data
            }
        except Exception as e:
            logger.error(f"Error loading text file: {str(e)}")
            raise ValueError(f"Error loading text file: {str(e)}")
    
    def _detect_dataset_format(self, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:
        """
        Detect the format of a dataset based on its content.
        
        Args:
            data: The dataset data.
            
        Returns:
            The detected format: "text", "instruction", or "conversation".
        """
        # Check if data is a list
        if isinstance(data, list):
            if len(data) == 0:
                return "text"  # Default to text format for empty lists
            
            # Check first item
            first_item = data[0]
            
            if isinstance(first_item, dict):
                # Check for instruction format
                if "prompt" in first_item and "completion" in first_item:
                    return "instruction"
                
                # Check for conversation format
                if "messages" in first_item and isinstance(first_item["messages"], list):
                    return "conversation"
                
                # Check for OpenAI conversation format
                if "role" in first_item and "content" in first_item:
                    return "conversation"
                
                # Check for text format
                if "text" in first_item:
                    return "text"
        
        # Check if data is a dictionary
        elif isinstance(data, dict):
            # Check for instruction format
            if "prompt" in data and "completion" in data:
                return "instruction"
            
            # Check for conversation format
            if "messages" in data and isinstance(data["messages"], list):
                return "conversation"
            
            # Check for text format
            if "text" in data:
                return "text"
        
        # Default to text format
        return "text"
    
    def preprocess_dataset(self, dataset: Dict[str, Any], 
                           max_length: int = 512,
                           remove_duplicates: bool = True,
                           shuffle: bool = True,
                           train_split: float = 0.9) -> Dict[str, Any]:
        """
        Preprocess a dataset for model fine-tuning.
        
        Args:
            dataset: The dataset to preprocess.
            max_length: Maximum sequence length.
            remove_duplicates: Whether to remove duplicate samples.
            shuffle: Whether to shuffle the dataset.
            train_split: Fraction of data to use for training (rest for evaluation).
            
        Returns:
            A dictionary containing the preprocessed dataset.
        """
        logger.info("Preprocessing dataset")
        
        dataset_format = dataset["format"]
        data = dataset["data"]
        
        # Process based on format
        if dataset_format == "text":
            processed_data = self._preprocess_text_dataset(data, max_length)
        elif dataset_format == "instruction":
            processed_data = self._preprocess_instruction_dataset(data, max_length)
        elif dataset_format == "conversation":
            processed_data = self._preprocess_conversation_dataset(data, max_length)
        else:
            logger.error(f"Unsupported dataset format: {dataset_format}")
            raise ValueError(f"Unsupported dataset format: {dataset_format}")
        
        # Remove duplicates if requested
        if remove_duplicates:
            processed_data = self._remove_duplicates(processed_data, dataset_format)
        
        # Shuffle if requested
        if shuffle:
            random.shuffle(processed_data)
        
        # Split into train and eval sets
        train_size = int(len(processed_data) * train_split)
        train_data = processed_data[:train_size]
        eval_data = processed_data[train_size:]
        
        logger.info(f"Dataset preprocessed: {len(train_data)} training samples, {len(eval_data)} evaluation samples")
        
        return {
            "format": dataset_format,
            "train_data": train_data,
            "eval_data": eval_data
        }
    
    def _preprocess_text_dataset(self, data: List[Dict[str, Any]], max_length: int) -> List[Dict[str, Any]]:
        """
        Preprocess a text dataset.
        
        Args:
            data: The dataset data.
            max_length: Maximum sequence length.
            
        Returns:
            The preprocessed dataset.
        """
        logger.debug("Preprocessing text dataset")
        
        processed_data = []
        
        for item in data:
            text = item.get("text", "")
            
            # Skip empty samples
            if not text.strip():
                continue
            
            # Truncate if necessary
            if len(text) > max_length * 4:  # Rough estimate: 1 token ≈ 4 characters
                text = text[:max_length * 4]
            
            processed_data.append({"text": text})
        
        return processed_data
    
    def _preprocess_instruction_dataset(self, data: List[Dict[str, Any]], max_length: int) -> List[Dict[str, Any]]:
        """
        Preprocess an instruction dataset.
        
        Args:
            data: The dataset data.
            max_length: Maximum sequence length.
            
        Returns:
            The preprocessed dataset.
        """
        logger.debug("Preprocessing instruction dataset")
        
        processed_data = []
        
        for item in data:
            prompt = item.get("prompt", "")
            completion = item.get("completion", "")
            
            # Skip empty samples
            if not prompt.strip() or not completion.strip():
                continue
            
            # Truncate if necessary
            total_length = len(prompt) + len(completion)
            if total_length > max_length * 4:  # Rough estimate: 1 token ≈ 4 characters
                # Allocate 1/3 to prompt and 2/3 to completion
                max_prompt_length = (max_length * 4) // 3
                max_completion_length = (max_length * 4 * 2) // 3
                
                if len(prompt) > max_prompt_length:
                    prompt = prompt[:max_prompt_length]
                
                if len(completion) > max_completion_length:
                    completion = completion[:max_completion_length]
            
            processed_data.append({
                "prompt": prompt,
                "completion": completion
            })
        
        return processed_data
    
    def _preprocess_conversation_dataset(self, data: List[Dict[str, Any]], max_length: int) -> List[Dict[str, Any]]:
        """
        Preprocess a conversation dataset.
        
        Args:
            data: The dataset data.
            max_length: Maximum sequence length.
            
        Returns:
            The preprocessed dataset.
        """
        logger.debug("Preprocessing conversation dataset")
        
        processed_data = []
        
        for item in data:
            # Handle different conversation formats
            messages = []
            
            if "messages" in item and isinstance(item["messages"], list):
                messages = item["messages"]
            elif "role" in item and "content" in item:
                messages = [item]
            
            # Skip empty conversations
            if not messages:
                continue
            
            # Process messages
            processed_messages = []
            total_length = 0
            
            for message in messages:
                role = message.get("role", "")
                content = message.get("content", "")
                
                # Skip empty messages
                if not role or not content.strip():
                    continue
                
                # Add message length
                message_length = len(content)
                total_length += message_length
                
                processed_messages.append({
                    "role": role,
                    "content": content
                })
            
            # Skip empty conversations
            if not processed_messages:
                continue
            
            # Truncate if necessary
            if total_length > max_length * 4:  # Rough estimate: 1 token ≈ 4 characters
                # Instead of removing messages, truncate the content of each message
                # to fit within max_length, preserving all messages
                target_length = max_length * 4
                # Calculate how much to reduce each message
                reduction_factor = target_length / total_length
                
                new_processed_messages = []
                new_total_length = 0
                
                for message in processed_messages:
                    content = message["content"]
                    new_length = int(len(content) * reduction_factor)
                    # Ensure minimum length of 1 character
                    new_length = max(1, new_length)
                    # Truncate content
                    new_content = content[:new_length]
                    new_total_length += len(new_content)
                    
                    new_processed_messages.append({
                        "role": message["role"],
                        "content": new_content
                    })
                
                processed_messages = new_processed_messages
            
            processed_data.append({"messages": processed_messages})
        
        return processed_data
    
    def _remove_duplicates(self, data: List[Dict[str, Any]], dataset_format: str) -> List[Dict[str, Any]]:
        """
        Remove duplicate samples from a dataset.
        
        Args:
            data: The dataset data.
            dataset_format: The format of the dataset.
            
        Returns:
            The dataset with duplicates removed.
        """
        logger.debug("Removing duplicates from dataset")
        
        unique_data = []
        seen = set()
        
        for item in data:
            # Create a hashable representation based on format
            if dataset_format == "text":
                key = item.get("text", "")
            elif dataset_format == "instruction":
                key = f"{item.get('prompt', '')}|{item.get('completion', '')}"
            elif dataset_format == "conversation":
                messages = item.get("messages", [])
                key = "|".join([f"{m.get('role', '')}:{m.get('content', '')}" for m in messages])
            else:
                # If format is unknown, use the string representation of the item
                key = str(item)
            
            # Add to unique data if not seen before
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        logger.debug(f"Removed {len(data) - len(unique_data)} duplicates")
        
        return unique_data
    
    def format_for_training(self, dataset: Dict[str, Any], adapter_type: str) -> Dict[str, Any]:
        """
        Format a dataset for training with a specific adapter type.
        
        Args:
            dataset: The preprocessed dataset.
            adapter_type: The type of adapter (lora, qlora, prefix_tuning).
            
        Returns:
            A dictionary containing the formatted dataset.
        """
        logger.info(f"Formatting dataset for {adapter_type} training")
        
        dataset_format = dataset["format"]
        train_data = dataset["train_data"]
        eval_data = dataset["eval_data"]
        
        # Format based on dataset format
        if dataset_format == "text":
            formatted_train = self._format_text_dataset(train_data, adapter_type)
            formatted_eval = self._format_text_dataset(eval_data, adapter_type)
        elif dataset_format == "instruction":
            formatted_train = self._format_instruction_dataset(train_data, adapter_type)
            formatted_eval = self._format_instruction_dataset(eval_data, adapter_type)
        elif dataset_format == "conversation":
            formatted_train = self._format_conversation_dataset(train_data, adapter_type)
            formatted_eval = self._format_conversation_dataset(eval_data, adapter_type)
        else:
            logger.error(f"Unsupported dataset format: {dataset_format}")
            raise ValueError(f"Unsupported dataset format: {dataset_format}")
        
        logger.info(f"Dataset formatted for {adapter_type} training")
        
        return {
            "format": dataset_format,
            "adapter_type": adapter_type,
            "train_data": formatted_train,
            "eval_data": formatted_eval
        }
    
    def _format_text_dataset(self, data: List[Dict[str, Any]], adapter_type: str) -> List[Dict[str, Any]]:
        """
        Format a text dataset for training.
        
        Args:
            data: The dataset data.
            adapter_type: The type of adapter.
            
        Returns:
            The formatted dataset.
        """
        logger.debug(f"Formatting text dataset for {adapter_type}")
        
        formatted_data = []
        
        for item in data:
            text = item.get("text", "")
            
            # Format based on adapter type
            if adapter_type in ["lora", "qlora"]:
                # For LoRA and QLoRA, we use the text as is
                formatted_data.append({"text": text})
            elif adapter_type == "prefix_tuning":
                # For prefix tuning, we need to add a prefix
                formatted_data.append({"text": f"<|prefix|> {text}"})
            
        return formatted_data
    
    def _format_instruction_dataset(self, data: List[Dict[str, Any]], adapter_type: str) -> List[Dict[str, Any]]:
        """
        Format an instruction dataset for training.
        
        Args:
            data: The dataset data.
            adapter_type: The type of adapter.
            
        Returns:
            The formatted dataset.
        """
        logger.debug(f"Formatting instruction dataset for {adapter_type}")
        
        formatted_data = []
        
        for item in data:
            prompt = item.get("prompt", "")
            completion = item.get("completion", "")
            
            # Format based on adapter type
            if adapter_type in ["lora", "qlora"]:
                # For LoRA and QLoRA, we use a standard instruction format
                formatted_data.append({
                    "prompt": prompt,
                    "completion": completion
                })
            elif adapter_type == "prefix_tuning":
                # For prefix tuning, we add a prefix
                formatted_data.append({
                    "prompt": f"<|prefix|> {prompt}",
                    "completion": completion
                })
            
        return formatted_data
    
    def _format_conversation_dataset(self, data: List[Dict[str, Any]], adapter_type: str) -> List[Dict[str, Any]]:
        """
        Format a conversation dataset for training.
        
        Args:
            data: The dataset data.
            adapter_type: The type of adapter.
            
        Returns:
            The formatted dataset.
        """
        logger.debug(f"Formatting conversation dataset for {adapter_type}")
        
        formatted_data = []
        
        for item in data:
            messages = item.get("messages", [])
            
            # Format based on adapter type
            if adapter_type in ["lora", "qlora"]:
                # For LoRA and QLoRA, we use the messages as is
                formatted_data.append({"messages": messages})
            elif adapter_type == "prefix_tuning":
                # For prefix tuning, we add a prefix to the first message
                if messages:
                    first_message = messages[0].copy()
                    first_message["content"] = f"<|prefix|> {first_message['content']}"
                    formatted_messages = [first_message] + messages[1:]
                    formatted_data.append({"messages": formatted_messages})
                else:
                    # If no messages, skip this item
                    continue
            
        return formatted_data
    
    def save_dataset(self, dataset: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """
        Save a formatted dataset to disk.
        
        Args:
            dataset: The formatted dataset.
            output_dir: The directory to save the dataset to.
            
        Returns:
            A dictionary containing the paths to the saved files.
        """
        logger.info(f"Saving dataset to {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        dataset_format = dataset["format"]
        adapter_type = dataset["adapter_type"]
        train_data = dataset["train_data"]
        eval_data = dataset["eval_data"]
        
        # Save train data
        train_path = os.path.join(output_dir, "train.jsonl")
        with open(train_path, 'w', encoding='utf-8') as f:
            for item in train_data:
                f.write(json.dumps(item) + '\n')
        
        # Save eval data
        eval_path = os.path.join(output_dir, "eval.jsonl")
        with open(eval_path, 'w', encoding='utf-8') as f:
            for item in eval_data:
                f.write(json.dumps(item) + '\n')
        
        # Save metadata
        metadata = {
            "format": dataset_format,
            "adapter_type": adapter_type,
            "train_samples": len(train_data),
            "eval_samples": len(eval_data)
        }
        
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Dataset saved: {len(train_data)} training samples, {len(eval_data)} evaluation samples")
        
        return {
            "train_path": train_path,
            "eval_path": eval_path,
            "metadata_path": metadata_path
        }
    
    def get_dataset_info(self, dataset_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a dataset.
        
        Args:
            dataset_path: Path to the dataset directory. If None, uses a default path.
            
        Returns:
            A dictionary containing dataset information.
        """
        # If dataset_path is not provided, use a default path or return mock data for testing
        if dataset_path is None:
            logger.info("No dataset path provided, returning mock dataset info")
            return {
                "format": "instruction",
                "samples": 1000,
                "train_samples": 800,
                "eval_samples": 200,
                "train_path": "train.jsonl",
                "eval_path": "eval.jsonl"
            }
            
        logger.info(f"Getting dataset info for {dataset_path}")
        
        # Check if the dataset directory exists
        if not os.path.exists(dataset_path):
            logger.error(f"Dataset directory not found: {dataset_path}")
            raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")
        
        # Check for train and eval files
        train_path = os.path.join(dataset_path, "train.jsonl")
        eval_path = os.path.join(dataset_path, "eval.jsonl")
        metadata_path = os.path.join(dataset_path, "metadata.json")
        
        # Load metadata if available
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading metadata: {str(e)}")
        
        # Count samples
        train_samples = 0
        if os.path.exists(train_path):
            with open(train_path, 'r', encoding='utf-8') as f:
                train_samples = sum(1 for _ in f)
        
        eval_samples = 0
        if os.path.exists(eval_path):
            with open(eval_path, 'r', encoding='utf-8') as f:
                eval_samples = sum(1 for _ in f)
        
        # Determine format
        dataset_format = metadata.get("format", "unknown")
        
        # Create dataset info
        dataset_info = {
            "format": dataset_format,
            "samples": train_samples + eval_samples,
            "train_samples": train_samples,
            "eval_samples": eval_samples,
            "train_path": train_path if os.path.exists(train_path) else None,
            "eval_path": eval_path if os.path.exists(eval_path) else None
        }
        
        # Add additional metadata
        for key, value in metadata.items():
            if key not in dataset_info:
                dataset_info[key] = value
        
        logger.info(f"Dataset info retrieved: {dataset_format} format, {train_samples + eval_samples} total samples")
        
        return dataset_info
    
    def analyze_dataset(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a dataset to provide statistics and insights.
        
        Args:
            dataset: The dataset to analyze.
            
        Returns:
            A dictionary containing dataset statistics and insights.
        """
        logger.info("Analyzing dataset")
        
        dataset_format = dataset["format"]
        train_data = dataset["train_data"]
        eval_data = dataset["eval_data"]
        
        # Basic statistics
        stats = {
            "format": dataset_format,
            "total_samples": len(train_data) + len(eval_data),
            "train_samples": len(train_data),
            "eval_samples": len(eval_data),
            "train_eval_ratio": len(train_data) / max(1, len(train_data) + len(eval_data))
        }
        
        # Format-specific statistics
        if dataset_format == "text":
            text_stats = self._analyze_text_dataset(train_data + eval_data)
            stats.update(text_stats)
        elif dataset_format == "instruction":
            instruction_stats = self._analyze_instruction_dataset(train_data + eval_data)
            stats.update(instruction_stats)
        elif dataset_format == "conversation":
            conversation_stats = self._analyze_conversation_dataset(train_data + eval_data)
            stats.update(conversation_stats)
        
        logger.info("Dataset analysis completed")
        
        return stats
    
    def _analyze_text_dataset(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a text dataset.
        
        Args:
            data: The dataset data.
            
        Returns:
            A dictionary containing dataset statistics.
        """
        logger.debug("Analyzing text dataset")
        
        # Calculate text lengths
        text_lengths = [len(item.get("text", "")) for item in data]
        
        # Calculate token estimates (rough estimate: 1 token ≈ 4 characters)
        token_estimates = [length // 4 for length in text_lengths]
        
        # Calculate statistics
        stats = {
            "avg_text_length": np.mean(text_lengths) if text_lengths else 0,
            "min_text_length": min(text_lengths) if text_lengths else 0,
            "max_text_length": max(text_lengths) if text_lengths else 0,
            "median_text_length": np.median(text_lengths) if text_lengths else 0,
            "std_text_length": np.std(text_lengths) if text_lengths else 0,
            
            "avg_tokens": np.mean(token_estimates) if token_estimates else 0,
            "min_tokens": min(token_estimates) if token_estimates else 0,
            "max_tokens": max(token_estimates) if token_estimates else 0,
            "median_tokens": np.median(token_estimates) if token_estimates else 0,
            "std_tokens": np.std(token_estimates) if token_estimates else 0,
            
            "total_tokens": sum(token_estimates)
        }
        
        return stats
    
    def _analyze_instruction_dataset(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze an instruction dataset.
        
        Args:
            data: The dataset data.
            
        Returns:
            A dictionary containing dataset statistics.
        """
        logger.debug("Analyzing instruction dataset")
        
        # Calculate prompt and completion lengths
        prompt_lengths = [len(item.get("prompt", "")) for item in data]
        completion_lengths = [len(item.get("completion", "")) for item in data]
        
        # Calculate token estimates (rough estimate: 1 token ≈ 4 characters)
        prompt_token_estimates = [length // 4 for length in prompt_lengths]
        completion_token_estimates = [length // 4 for length in completion_lengths]
        total_token_estimates = [p + c for p, c in zip(prompt_token_estimates, completion_token_estimates)]
        
        # Calculate statistics
        stats = {
            "avg_prompt_length": np.mean(prompt_lengths) if prompt_lengths else 0,
            "min_prompt_length": min(prompt_lengths) if prompt_lengths else 0,
            "max_prompt_length": max(prompt_lengths) if prompt_lengths else 0,
            "median_prompt_length": np.median(prompt_lengths) if prompt_lengths else 0,
            "std_prompt_length": np.std(prompt_lengths) if prompt_lengths else 0,
            
            "avg_completion_length": np.mean(completion_lengths) if completion_lengths else 0,
            "min_completion_length": min(completion_lengths) if completion_lengths else 0,
            "max_completion_length": max(completion_lengths) if completion_lengths else 0,
            "median_completion_length": np.median(completion_lengths) if completion_lengths else 0,
            "std_completion_length": np.std(completion_lengths) if completion_lengths else 0,
            
            "avg_prompt_tokens": np.mean(prompt_token_estimates) if prompt_token_estimates else 0,
            "avg_completion_tokens": np.mean(completion_token_estimates) if completion_token_estimates else 0,
            "avg_total_tokens": np.mean(total_token_estimates) if total_token_estimates else 0,
            
            "total_prompt_tokens": sum(prompt_token_estimates),
            "total_completion_tokens": sum(completion_token_estimates),
            "total_tokens": sum(total_token_estimates)
        }
        
        return stats
    
    def _analyze_conversation_dataset(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a conversation dataset.
        
        Args:
            data: The dataset data.
            
        Returns:
            A dictionary containing dataset statistics.
        """
        logger.debug("Analyzing conversation dataset")
        
        # Calculate conversation statistics
        num_messages = []
        message_lengths = []
        role_counts = {}
        
        for item in data:
            messages = item.get("messages", [])
            num_messages.append(len(messages))
            
            for message in messages:
                role = message.get("role", "")
                content = message.get("content", "")
                
                message_lengths.append(len(content))
                
                # Count roles
                role_counts[role] = role_counts.get(role, 0) + 1
        
        # Calculate token estimates (rough estimate: 1 token ≈ 4 characters)
        message_token_estimates = [length // 4 for length in message_lengths]
        
        # Calculate statistics
        stats = {
            "avg_messages_per_conversation": np.mean(num_messages) if num_messages else 0,
            "min_messages_per_conversation": min(num_messages) if num_messages else 0,
            "max_messages_per_conversation": max(num_messages) if num_messages else 0,
            "median_messages_per_conversation": np.median(num_messages) if num_messages else 0,
            
            "avg_message_length": np.mean(message_lengths) if message_lengths else 0,
            "min_message_length": min(message_lengths) if message_lengths else 0,
            "max_message_length": max(message_lengths) if message_lengths else 0,
            "median_message_length": np.median(message_lengths) if message_lengths else 0,
            
            "avg_message_tokens": np.mean(message_token_estimates) if message_token_estimates else 0,
            "total_messages": sum(num_messages),
            "total_tokens": sum(message_token_estimates),
            "role_distribution": role_counts
        }
        
        return stats
