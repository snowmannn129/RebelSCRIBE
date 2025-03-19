#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adapter support module for RebelSCRIBE.

This module provides support for efficient fine-tuning of large language models
using adapter methods like LoRA (Low-Rank Adaptation), QLoRA (Quantized LoRA),
and prefix tuning.
"""

import os
import json
import shutil
import logging
import tempfile
import glob
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from pathlib import Path
from datetime import datetime
import zipfile

import torch
import numpy as np
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    EvalPrediction,
)
from datasets import Dataset, load_dataset
from peft import (
    LoraConfig,
    PrefixTuningConfig,
    TaskType,
    get_peft_model,
    PeftModel,
    PeftConfig,
    prepare_model_for_kbit_training,
)

logger = logging.getLogger(__name__)

# Ensure NLTK and rouge_score are available
try:
    import nltk
    nltk.download('punkt', quiet=True)
except ImportError:
    logger.warning("NLTK not installed. BLEU scoring will not be available.")

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
except ImportError:
    logger.warning("NLTK not installed. BLEU scoring will not be available.")

try:
    from rouge_score import rouge_scorer
except ImportError:
    logger.warning("rouge_score not installed. ROUGE scoring will not be available.")


class AdapterInfo:
    """
    Class to store information about an adapter.
    """
    
    def __init__(
        self,
        name: str,
        path: str,
        base_model: str,
        adapter_type: str,
        creation_date: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize adapter information.
        
        Args:
            name: Name of the adapter.
            path: Path to the adapter.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            creation_date: Date the adapter was created.
            parameters: Parameters used to create the adapter.
            metrics: Evaluation metrics for the adapter.
        """
        self.name = name
        self.path = path
        self.base_model = base_model
        self.adapter_type = adapter_type
        self.creation_date = creation_date or datetime.now().isoformat()
        self.parameters = parameters or {}
        self.metrics = metrics or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert adapter info to a dictionary.
        
        Returns:
            Dictionary representation of the adapter info.
        """
        return {
            "name": self.name,
            "path": self.path,
            "base_model": self.base_model,
            "adapter_type": self.adapter_type,
            "creation_date": self.creation_date,
            "parameters": self.parameters,
            "metrics": self.metrics,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdapterInfo':
        """
        Create an AdapterInfo instance from a dictionary.
        
        Args:
            data: Dictionary containing adapter information.
        
        Returns:
            AdapterInfo instance.
        """
        return cls(
            name=data["name"],
            path=data["path"],
            base_model=data["base_model"],
            adapter_type=data["adapter_type"],
            creation_date=data.get("creation_date"),
            parameters=data.get("parameters", {}),
            metrics=data.get("metrics", {}),
        )


class AdapterManager:
    """
    Manager for model adapters like LoRA, QLoRA, and prefix tuning.
    
    This class provides methods for creating, loading, saving, and applying
    adapters to large language models for efficient fine-tuning.
    
    Supported adapter types:
    - LoRA (Low-Rank Adaptation): Efficient fine-tuning by adding low-rank matrices
    - QLoRA (Quantized LoRA): LoRA with quantized base model for memory efficiency
    - Prefix Tuning: Adds trainable continuous prefix vectors to transformer layers
    """
    
    def __init__(self, cache_dir: Optional[str] = None, adapters_dir: Optional[str] = None):
        """
        Initialize the AdapterManager.
        
        Args:
            cache_dir: Directory to cache models and adapters.
                       If None, uses the default cache directory.
            adapters_dir: Directory to store adapters.
                         If None, uses a default location.
        """
        self.cache_dir = cache_dir
        self.adapters_dir = adapters_dir or os.path.join(
            os.path.expanduser("~"), ".rebelscribe", "adapters"
        )
        self._ensure_dependencies()
        self._ensure_adapters_dir()
        self._load_adapter_registry()
    
    def _ensure_dependencies(self) -> None:
        """
        Ensure that all required dependencies are installed.
        
        Raises:
            ImportError: If any required dependency is missing.
        """
        try:
            import peft
            import transformers
            import datasets
            import torch
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise ImportError(
                "Adapter support requires peft, transformers, datasets, and torch. "
                "Please install them using pip: "
                "pip install peft transformers datasets torch"
            ) from e
    
    def _ensure_adapters_dir(self) -> None:
        """
        Ensure that the adapters directory exists.
        """
        os.makedirs(self.adapters_dir, exist_ok=True)
        
        # Create registry file if it doesn't exist
        registry_path = os.path.join(self.adapters_dir, "registry.json")
        if not os.path.exists(registry_path):
            with open(registry_path, "w") as f:
                json.dump({"adapters": []}, f)
    
    def _load_adapter_registry(self) -> None:
        """
        Load the adapter registry from disk.
        """
        registry_path = os.path.join(self.adapters_dir, "registry.json")
        try:
            with open(registry_path, "r") as f:
                registry = json.load(f)
            
            self.adapter_registry = [
                AdapterInfo.from_dict(adapter_data)
                for adapter_data in registry.get("adapters", [])
            ]
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not load adapter registry from {registry_path}")
            self.adapter_registry = []
    
    def _save_adapter_registry(self) -> None:
        """
        Save the adapter registry to disk.
        """
        registry_path = os.path.join(self.adapters_dir, "registry.json")
        registry = {
            "adapters": [
                adapter.to_dict() for adapter in self.adapter_registry
            ]
        }
        
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)
    
    def create_lora_adapter(
        self,
        base_model_name: str,
        adapter_name: str,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        bias: str = "none",
        task_type: TaskType = TaskType.CAUSAL_LM,
        quantization_bits: Optional[int] = None,
    ) -> Tuple[PeftModel, AutoTokenizer]:
        """
        Create a LoRA adapter for a base model.
        
        Args:
            base_model_name: Name or path of the base model.
            adapter_name: Name for the adapter.
            r: Rank of the update matrices.
            lora_alpha: Alpha parameter for LoRA scaling.
            lora_dropout: Dropout probability for LoRA layers.
            target_modules: List of modules to apply LoRA to.
                           If None, will try to automatically infer.
            bias: Bias configuration ('none', 'all', or 'lora_only').
            task_type: Type of task (CAUSAL_LM, SEQ_CLS, etc.).
            quantization_bits: Number of bits for quantization (4, 8, or None).
                              If not None, will use QLoRA.
        
        Returns:
            Tuple of (adapted model, tokenizer)
        """
        logger.info(f"Creating LoRA adapter '{adapter_name}' for model '{base_model_name}'")
        
        # Determine if we're using QLoRA (quantized)
        is_qlora = quantization_bits in (4, 8)
        
        # Set up quantization parameters if using QLoRA
        quantization_config = None
        if is_qlora:
            logger.info(f"Using QLoRA with {quantization_bits}-bit quantization")
            from transformers import BitsAndBytesConfig
            
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=quantization_bits == 4,
                load_in_8bit=quantization_bits == 8,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        
        # Load the base model
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=quantization_config,
            device_map="auto",
            cache_dir=self.cache_dir,
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            cache_dir=self.cache_dir,
        )
        
        # Prepare model for k-bit training if using QLoRA
        if is_qlora:
            model = prepare_model_for_kbit_training(
                model,
                use_gradient_checkpointing=True,
            )
        
        # If target modules not specified, try to infer them
        if target_modules is None:
            target_modules = self._infer_target_modules(model)
            logger.info(f"Automatically inferred target modules: {target_modules}")
        
        # Configure LoRA
        lora_config = LoraConfig(
            r=r,
            lora_alpha=lora_alpha,
            target_modules=target_modules,
            lora_dropout=lora_dropout,
            bias=bias,
            task_type=task_type,
        )
        
        # Apply LoRA to the model
        model = get_peft_model(model, lora_config)
        
        # Set adapter name
        model.active_adapter = adapter_name
        
        # Register adapter
        adapter_path = os.path.join(self.adapters_dir, adapter_name)
        self.register_adapter(
            name=adapter_name,
            path=adapter_path,
            base_model=base_model_name,
            adapter_type="lora" if not is_qlora else "qlora",
            parameters={
                "r": r,
                "lora_alpha": lora_alpha,
                "lora_dropout": lora_dropout,
                "target_modules": target_modules,
                "bias": bias,
                "quantization_bits": quantization_bits,
            },
        )
        
        logger.info(f"Successfully created LoRA adapter '{adapter_name}'")
        return model, tokenizer
    
    def _infer_target_modules(self, model: Any) -> List[str]:
        """
        Infer the target modules for LoRA based on model architecture.
        
        Args:
            model: The model to analyze.
            
        Returns:
            List of module names that are suitable for LoRA.
        """
        # Common module names for different model architectures
        architecture_to_modules = {
            "llama": ["q_proj", "k_proj", "v_proj", "o_proj"],
            "mistral": ["q_proj", "k_proj", "v_proj", "o_proj"],
            "falcon": ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"],
            "mpt": ["c_proj", "c_attn"],
            "phi": ["q_proj", "k_proj", "v_proj", "dense"],
            "gpt2": ["c_attn", "c_proj"],
            "gpt_neox": ["query_key_value", "dense"],
            "opt": ["q_proj", "k_proj", "v_proj", "fc1", "fc2"],
            "default": ["query", "key", "value", "dense"],
        }
        
        # Try to determine model architecture from model config
        model_architecture = "default"
        if hasattr(model, "config"):
            model_type = getattr(model.config, "model_type", "").lower()
            for arch in architecture_to_modules:
                if arch in model_type:
                    model_architecture = arch
                    break
        
        logger.info(f"Detected model architecture: {model_architecture}")
        return architecture_to_modules[model_architecture]
    
    def save_adapter(
        self,
        model: PeftModel,
        adapter_name: str,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Save a trained adapter to disk.
        
        Args:
            model: The model with the adapter.
            adapter_name: Name of the adapter to save.
            output_dir: Directory to save the adapter to.
                       If None, uses a default location.
        
        Returns:
            Path to the saved adapter.
        """
        if output_dir is None:
            output_dir = os.path.join(self.adapters_dir, adapter_name)
        
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Saving adapter '{adapter_name}' to {output_dir}")
        
        # Save the adapter
        model.save_pretrained(output_dir)
        
        # Update adapter registry
        adapter_info = self.get_adapter_info(adapter_name)
        if adapter_info:
            adapter_info.path = output_dir
            self._save_adapter_registry()
        
        return output_dir
    
    def load_adapter(
        self,
        base_model_name: str,
        adapter_path: str,
        adapter_name: Optional[str] = None,
        device_map: str = "auto",
    ) -> Tuple[PeftModel, AutoTokenizer]:
        """
        Load a saved adapter and apply it to a base model.
        
        Args:
            base_model_name: Name or path of the base model.
            adapter_path: Path to the saved adapter.
            adapter_name: Name to give the loaded adapter.
                         If None, uses the name from the saved config.
            device_map: Device mapping strategy.
        
        Returns:
            Tuple of (adapted model, tokenizer)
        """
        logger.info(f"Loading adapter from {adapter_path} for model {base_model_name}")
        
        # Load the adapter config to determine if it's quantized
        peft_config = PeftConfig.from_pretrained(adapter_path)
        
        # Determine if the adapter was created with quantization
        is_quantized = False
        quantization_config = None
        
        # Check for quantization markers in the config
        if hasattr(peft_config, "quantization_config"):
            is_quantized = True
            from transformers import BitsAndBytesConfig
            
            # Recreate the quantization config
            if getattr(peft_config.quantization_config, "load_in_4bit", False):
                bits = 4
            elif getattr(peft_config.quantization_config, "load_in_8bit", False):
                bits = 8
            else:
                bits = None
                
            if bits:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=bits == 4,
                    load_in_8bit=bits == 8,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
        
        # Load the base model with appropriate quantization
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=quantization_config,
            device_map=device_map,
            cache_dir=self.cache_dir,
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            cache_dir=self.cache_dir,
        )
        
        # Load the adapter
        model = PeftModel.from_pretrained(
            model,
            adapter_path,
            adapter_name=adapter_name,
        )
        
        logger.info(f"Successfully loaded adapter from {adapter_path}")
        return model, tokenizer
    
    def fine_tune(
        self,
        model: PeftModel,
        tokenizer: AutoTokenizer,
        dataset: Union[Dataset, Dict[str, Dataset]],
        output_dir: str,
        training_args: Optional[TrainingArguments] = None,
        **kwargs,
    ) -> PeftModel:
        """
        Fine-tune a model with an adapter using a dataset.
        
        Args:
            model: The model with adapter to fine-tune.
            tokenizer: The tokenizer for the model.
            dataset: The dataset to use for fine-tuning.
            output_dir: Directory to save checkpoints and results.
            training_args: Arguments for training.
                          If None, uses default arguments.
            **kwargs: Additional arguments to pass to the Trainer.
        
        Returns:
            The fine-tuned model.
        """
        logger.info("Starting fine-tuning with adapter")
        
        # Set default training arguments if not provided
        if training_args is None:
            training_args = TrainingArguments(
                output_dir=output_dir,
                per_device_train_batch_size=4,
                gradient_accumulation_steps=4,
                num_train_epochs=3,
                learning_rate=3e-4,
                fp16=True,
                logging_steps=10,
                save_steps=100,
                save_total_limit=3,
                remove_unused_columns=False,
            )
        
        # Prepare data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,
        )
        
        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset["train"] if isinstance(dataset, dict) else dataset,
            eval_dataset=dataset.get("validation") if isinstance(dataset, dict) else None,
            data_collator=data_collator,
            **kwargs,
        )
        
        # Train the model
        logger.info("Starting training")
        trainer.train()
        
        # Save the final model
        logger.info(f"Saving fine-tuned model to {output_dir}")
        trainer.save_model(output_dir)
        
        return model
    
    def prepare_dataset(
        self,
        texts: List[str],
        tokenizer: AutoTokenizer,
        max_length: int = 512,
    ) -> Dataset:
        """
        Prepare a dataset from a list of texts for fine-tuning.
        
        Args:
            texts: List of text samples for fine-tuning.
            tokenizer: The tokenizer to use.
            max_length: Maximum sequence length.
        
        Returns:
            A dataset ready for fine-tuning.
        """
        logger.info(f"Preparing dataset with {len(texts)} samples")
        
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                padding="max_length",
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
        
        # Create dataset
        dataset = Dataset.from_dict({"text": texts})
        
        # Tokenize dataset
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=["text"],
        )
        
        return tokenized_dataset
    
    def create_qlora_adapter(
        self,
        base_model_name: str,
        adapter_name: str,
        quantization_bits: int = 4,
        **kwargs,
    ) -> Tuple[PeftModel, AutoTokenizer]:
        """
        Create a QLoRA (Quantized LoRA) adapter for a base model.
        
        This is a convenience method that calls create_lora_adapter with
        quantization enabled.
        
        Args:
            base_model_name: Name or path of the base model.
            adapter_name: Name for the adapter.
            quantization_bits: Number of bits for quantization (4 or 8).
            **kwargs: Additional arguments to pass to create_lora_adapter.
        
        Returns:
            Tuple of (adapted model, tokenizer)
        """
        return self.create_lora_adapter(
            base_model_name=base_model_name,
            adapter_name=adapter_name,
            quantization_bits=quantization_bits,
            **kwargs,
        )
    
    def create_prefix_tuning_adapter(
        self,
        base_model_name: str,
        adapter_name: str,
        num_virtual_tokens: int = 20,
        prefix_projection: bool = False,
        encoder_hidden_size: Optional[int] = None,
        task_type: TaskType = TaskType.CAUSAL_LM,
        quantization_bits: Optional[int] = None,
    ) -> Tuple[PeftModel, AutoTokenizer]:
        """
        Create a Prefix Tuning adapter for a base model.
        
        Prefix Tuning adds trainable continuous prefix vectors to the input
        of each transformer layer, which can be more parameter-efficient than
        fine-tuning the entire model.
        
        Args:
            base_model_name: Name or path of the base model.
            adapter_name: Name for the adapter.
            num_virtual_tokens: Number of virtual tokens to add as prefix.
            prefix_projection: Whether to use a projection matrix for the prefix.
            encoder_hidden_size: Hidden size for the prefix projection.
                                Only used when prefix_projection is True.
            task_type: Type of task (CAUSAL_LM, SEQ_CLS, etc.).
            quantization_bits: Number of bits for quantization (4, 8, or None).
                              If not None, will use quantized model.
        
        Returns:
            Tuple of (adapted model, tokenizer)
        """
        logger.info(f"Creating Prefix Tuning adapter '{adapter_name}' for model '{base_model_name}'")
        
        # Determine if we're using quantization
        is_quantized = quantization_bits in (4, 8)
        
        # Set up quantization parameters if using quantization
        quantization_config = None
        if is_quantized:
            logger.info(f"Using quantization with {quantization_bits}-bit precision")
            from transformers import BitsAndBytesConfig
            
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=quantization_bits == 4,
                load_in_8bit=quantization_bits == 8,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        
        # Load the base model
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=quantization_config,
            device_map="auto",
            cache_dir=self.cache_dir,
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            cache_dir=self.cache_dir,
        )
        
        # Prepare model for k-bit training if using quantization
        if is_quantized:
            model = prepare_model_for_kbit_training(
                model,
                use_gradient_checkpointing=True,
            )
        
        # Configure Prefix Tuning
        prefix_config = PrefixTuningConfig(
            task_type=task_type,
            num_virtual_tokens=num_virtual_tokens,
            prefix_projection=prefix_projection,
            encoder_hidden_size=encoder_hidden_size,
        )
        
        # Apply Prefix Tuning to the model
        model = get_peft_model(model, prefix_config)
        
        # Set adapter name
        model.active_adapter = adapter_name
        
        # Register adapter
        adapter_path = os.path.join(self.adapters_dir, adapter_name)
        self.register_adapter(
            name=adapter_name,
            path=adapter_path,
            base_model=base_model_name,
            adapter_type="prefix_tuning",
            parameters={
                "num_virtual_tokens": num_virtual_tokens,
                "prefix_projection": prefix_projection,
                "encoder_hidden_size": encoder_hidden_size,
                "quantization_bits": quantization_bits,
            },
        )
        
        logger.info(f"Successfully created Prefix Tuning adapter '{adapter_name}'")
        return model, tokenizer
    
    def get_adapters(self) -> List[AdapterInfo]:
        """
        Get a list of all available adapters.
        
        Returns:
            List of AdapterInfo objects.
        """
        return self.adapter_registry
    
    def get_adapter_info(self, adapter_name: str) -> Optional[AdapterInfo]:
        """
        Get information about a specific adapter.
        
        Args:
            adapter_name: Name of the adapter.
        
        Returns:
            AdapterInfo object if found, None otherwise.
        """
        for adapter in self.adapter_registry:
            if adapter.name == adapter_name:
                return adapter
        return None
    
    def register_adapter(
        self,
        name: str,
        path: str,
        base_model: str,
        adapter_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> AdapterInfo:
        """
        Register an adapter in the registry.
        
        Args:
            name: Name of the adapter.
            path: Path to the adapter.
            base_model: Name of the base model.
            adapter_type: Type of adapter (lora, qlora, prefix_tuning).
            parameters: Parameters used to create the adapter.
            metrics: Evaluation metrics for the adapter.
        
        Returns:
            AdapterInfo object for the registered adapter.
        """
        # Check if adapter already exists
        existing_adapter = self.get_adapter_info(name)
        if existing_adapter:
            # Update existing adapter
            existing_adapter.path = path
            existing_adapter.base_model = base_model
            existing_adapter.adapter_type = adapter_type
            if parameters:
                existing_adapter.parameters = parameters
            if metrics:
                existing_adapter.metrics = metrics
            adapter_info = existing_adapter
        else:
            # Create new adapter info
            adapter_info = AdapterInfo(
                name=name,
                path=path,
                base_model=base_model,
                adapter_type=adapter_type,
                parameters=parameters,
                metrics=metrics,
            )
            self.adapter_registry.append(adapter_info)
        
        # Save registry
        self._save_adapter_registry()
        
        return adapter_info
    
    def unregister_adapter(self, adapter_name: str) -> bool:
        """
        Unregister an adapter from the registry.
        
        Args:
            adapter_name: Name of the adapter to unregister.
        
        Returns:
            True if the adapter was unregistered, False otherwise.
        """
        for i, adapter in enumerate(self.adapter_registry):
            if adapter.name == adapter_name:
                del self.adapter_registry[i]
                self._save_adapter_registry()
                return True
        return False
    
    def delete_adapter(self, adapter_name: str) -> bool:
        """
        Delete an adapter from disk and unregister it.
        
        Args:
            adapter_name: Name of the adapter to delete.
        
        Returns:
            True if the adapter was deleted, False otherwise.
        """
        adapter_info = self.get_adapter_info(adapter_name)
        if not adapter_info:
            logger.warning(f"Adapter '{adapter_name}' not found in registry")
            return False
        
        # Delete adapter files
        try:
            if os.path.exists(adapter_info.path):
                if os.path.isdir(adapter_info.path):
                    shutil.rmtree(adapter_info.path)
                else:
                    os.remove(adapter_info.path)
            
            # Unregister adapter
            self.unregister_adapter(adapter_name)
            logger.info(f"Deleted adapter '{adapter_name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting adapter '{adapter_name}': {e}")
            return False
    
    def rename_adapter(self, old_name: str, new_name: str) -> bool:
        """
        Rename an adapter.
        
        Args:
            old_name: Current name of the adapter.
            new_name: New name for the adapter.
        
        Returns:
            True if the adapter was renamed, False otherwise.
        """
        # Check if new name already exists
        if self.get_adapter_info(new_name):
            logger.warning(f"Adapter with name '{new_name}' already exists")
            return False
        
        # Get adapter info
        adapter_info = self.get_adapter_info(old_name)
        if not adapter_info:
            logger.warning(f"Adapter '{old_name}' not found in registry")
            return False
        
        # Rename adapter directory if it exists
        old_path = adapter_info.path
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        try:
            if os.path.exists(old_path) and os.path.isdir(old_path):
                os.rename(old_path, new_path)
                adapter_info.path = new_path
            
            # Update name
            adapter_info.name = new_name
            
            # Save registry
            self._save_adapter_registry()
            
            logger.info(f"Renamed adapter '{old_name}' to '{new_name}'")
            return True
        except Exception as e:
            logger.error(f"Error renaming adapter '{old_name}' to '{new_name}': {e}")
            return False
    
    def evaluate_adapter(
        self,
        model: PeftModel,
        tokenizer: AutoTokenizer,
        eval_dataset: Union[Dataset, Dict[str, Dataset]],
        metrics: List[str] = ["perplexity", "bleu", "rouge"],
        max_samples: Optional[int] = None,
        adapter_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate an adapter using various metrics.
        
        Args:
            model: The model with the adapter.
            tokenizer: The tokenizer for the model.
            eval_dataset: The dataset to use for evaluation.
            metrics: List of metrics to compute.
            max_samples: Maximum number of samples to evaluate.
            adapter_name: Name of the adapter to evaluate.
                         If None, uses the active adapter.
        
        Returns:
            Dictionary of evaluation metrics.
        """
        logger.info(f"Evaluating adapter with metrics: {metrics}")
        
        if adapter_name is not None:
            # Set the specified adapter as active
            model.set_adapter(adapter_name)
        
        # Get the dataset
        if isinstance(eval_dataset, dict):
            if "validation" in eval_dataset:
                dataset = eval_dataset["validation"]
            elif "eval" in eval_dataset:
                dataset = eval_dataset["eval"]
            elif "test" in eval_dataset:
                dataset = eval_dataset["test"]
            else:
                dataset = next(iter(eval_dataset.values()))
        else:
            dataset = eval_dataset
        
        # Limit the number of samples if specified
        if max_samples is not None and max_samples < len(dataset):
            dataset = dataset.select(range(max_samples))
        
        results = {}
        
        # Compute perplexity
        if "perplexity" in metrics:
            try:
                perplexity = self._compute_perplexity(model, tokenizer, dataset)
                results["perplexity"] = perplexity
                logger.info(f"Perplexity: {perplexity:.4f}")
            except Exception as e:
                logger.error(f"Error computing perplexity: {e}")
                results["perplexity"] = None
        
        # Compute BLEU score
        if "bleu" in metrics:
            try:
                bleu_score = self._compute_bleu_score(model, tokenizer, dataset)
                results["bleu"] = bleu_score
                logger.info(f"BLEU score: {bleu_score:.4f}")
            except Exception as e:
                logger.error(f"Error computing BLEU score: {e}")
                results["bleu"] = None
        
        # Compute ROUGE scores
        if "rouge" in metrics:
            try:
                rouge_scores = self._compute_rouge_scores(model, tokenizer, dataset)
                results["rouge"] = rouge_scores
                logger.info(f"ROUGE scores: {rouge_scores}")
            except Exception as e:
                logger.error(f"Error computing ROUGE scores: {e}")
                results["rouge"] = {}
        
        # Update adapter info if available
        if adapter_name is not None:
            adapter_info = self.get_adapter_info(adapter_name)
            if adapter_info:
                adapter_info.metrics.update(results)
                self._save_adapter_registry()
        
        return results
    
    def _compute_perplexity(
        self,
        model: PeftModel,
        tokenizer: AutoTokenizer,
        dataset: Dataset,
    ) -> float:
        """
        Compute perplexity on a dataset.
        
        Args:
            model: The model to evaluate.
            tokenizer: The tokenizer for the model.
            dataset: The dataset to evaluate on.
        
        Returns:
            Perplexity score (lower is better).
        """
        logger.info("Computing perplexity")
        
        # Set model to evaluation mode
        model.eval()
        
        # Prepare data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,
        )
        
        # Create evaluation trainer
        trainer = Trainer(
            model=model,
            args=TrainingArguments(
                output_dir=tempfile.mkdtemp(),
                per_device_eval_batch_size=4,
                remove_unused_columns=False,
            ),
            eval_dataset=dataset,
            data_collator=data_collator,
        )
        
        # Evaluate
        eval_results = trainer.evaluate()
        
        # Extract perplexity
        perplexity = np.exp(eval_results["eval_loss"])
        
        return perplexity
    
    def _compute_bleu_score(
        self,
        model: PeftModel,
        tokenizer: AutoTokenizer,
        dataset: Dataset,
    ) -> float:
        """
        Compute BLEU score on a dataset.
        
        Args:
            model: The model to evaluate.
            tokenizer: The tokenizer for the model.
            dataset: The dataset to evaluate on.
        
        Returns:
            BLEU score (higher is better).
        """
        logger.info("Computing BLEU score")
        
        # Set model to evaluation mode
        model.eval()
        
        # Check if dataset has the right format
        if "input" not in dataset.column_names or "output" not in dataset.column_names:
            # Try to infer input and output columns
            if "text" in dataset.column_names:
                # Split text into input and output
                dataset = dataset.map(
                    lambda example: {
                        "input": example["text"].split("\n")[0],
                        "output": "\n".join(example["text"].split("\n")[1:]),
                    }
                )
            elif "instruction" in dataset.column_names and "response" in dataset.column_names:
                dataset = dataset.map(
                    lambda example: {
                        "input": example["instruction"],
                        "output": example["response"],
                    }
                )
            else:
                raise ValueError(
                    "Dataset must have 'input' and 'output' columns, "
                    "or 'text' column that can be split, "
                    "or 'instruction' and 'response' columns."
                )
        
        # Generate predictions
        predictions = []
        references = []
        
        for example in dataset:
            input_text = example["input"]
            reference = example["output"]
            
            # Tokenize input
            inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
            
            # Generate output
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=100,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=False,
                )
            
            # Decode output
            prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove input from prediction if it's included
            if prediction.startswith(input_text):
                prediction = prediction[len(input_text):].strip()
            
            # Tokenize prediction and reference
            prediction_tokens = tokenizer.tokenize(prediction)
            reference_tokens = tokenizer.tokenize(reference)
            
            predictions.append(prediction_tokens)
            references.append([reference_tokens])
        
        # Compute BLEU score
        smoothing = SmoothingFunction().method1
        bleu_scores = [
            sentence_bleu([ref], pred, smoothing_function=smoothing)
            for pred, ref in zip(predictions, references)
        ]
        
        # Return average BLEU score
        return sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0
    
    def _compute_rouge_scores(
        self,
        model: PeftModel,
        tokenizer: AutoTokenizer,
        dataset: Dataset,
    ) -> Dict[str, float]:
        """
        Compute ROUGE scores on a dataset.
        
        Args:
            model: The model to evaluate.
            tokenizer: The tokenizer for the model.
            dataset: The dataset to evaluate on.
        
        Returns:
            Dictionary of ROUGE scores (higher is better).
        """
        logger.info("Computing ROUGE scores")
        
        # Set model to evaluation mode
        model.eval()
        
        # Check if dataset has the right format
        if "input" not in dataset.column_names or "output" not in dataset.column_names:
            # Try to infer input and output columns
            if "text" in dataset.column_names:
                # Split text into input and output
                dataset = dataset.map(
                    lambda example: {
                        "input": example["text"].split("\n")[0],
                        "output": "\n".join(example["text"].split("\n")[1:]),
                    }
                )
            elif "instruction" in dataset.column_names and "response" in dataset.column_names:
                dataset = dataset.map(
                    lambda example: {
                        "input": example["instruction"],
                        "output": example["response"],
                    }
                )
            else:
                raise ValueError(
                    "Dataset must have 'input' and 'output' columns, "
                    "or 'text' column that can be split, "
                    "or 'instruction' and 'response' columns."
                )
        
        # Initialize ROUGE scorer
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        
        # Generate predictions
        rouge_scores = {
            'rouge1': [],
            'rouge2': [],
            'rougeL': [],
        }
        
        for example in dataset:
            input_text = example["input"]
            reference = example["output"]
            
            # Tokenize input
            inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
            
            # Generate output
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=100,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=False,
                )
            
            # Decode output
            prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove input from prediction if it's included
            if prediction.startswith(input_text):
                prediction = prediction[len(input_text):].strip()
            
            # Compute ROUGE scores
            scores = scorer.score(reference, prediction)
            
            # Add scores
            for key in rouge_scores:
                rouge_scores[key].append(scores[key].fmeasure)
        
        # Return average ROUGE scores
        return {
            key: sum(values) / len(values) if values else 0.0
            for key, values in rouge_scores.items()
        }
    
    def compare_adapters(
        self,
        adapter_names: List[str],
        base_model_name: str,
        eval_dataset: Union[Dataset, Dict[str, Dataset]],
        metrics: List[str] = ["perplexity", "bleu", "rouge"],
        max_samples: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare multiple adapters using various metrics.
        
        Args:
            adapter_names: List of adapter names to compare.
            base_model_name: Name of the base model.
            eval_dataset: The dataset to use for evaluation.
            metrics: List of metrics to compute.
            max_samples: Maximum number of samples to evaluate.
        
        Returns:
            Dictionary mapping adapter names to evaluation metrics.
        """
        logger.info(f"Comparing adapters: {adapter_names}")
        
        results = {}
        
        for adapter_name in adapter_names:
            logger.info(f"Evaluating adapter '{adapter_name}'")
            
            # Get adapter info
            adapter_info = self.get_adapter_info(adapter_name)
            if not adapter_info:
                logger.warning(f"Adapter '{adapter_name}' not found in registry")
                continue
            
            # Load adapter
            try:
                model, tokenizer = self.load_adapter(
                    base_model_name=base_model_name,
                    adapter_path=adapter_info.path,
                    adapter_name=adapter_name,
                )
                
                # Evaluate adapter
                adapter_results = self.evaluate_adapter(
                    model=model,
                    tokenizer=tokenizer,
                    eval_dataset=eval_dataset,
                    metrics=metrics,
                    max_samples=max_samples,
                    adapter_name=adapter_name,
                )
                
                results[adapter_name] = adapter_results
            except Exception as e:
                logger.error(f"Error evaluating adapter '{adapter_name}': {e}")
                results[adapter_name] = {"error": str(e)}
        
        return results
    
    def merge_adapter(
        self,
        model: PeftModel,
        adapter_name: Optional[str] = None,
    ) -> Any:
        """
        Merge an adapter with its base model.
        
        This creates a standalone model with the adapter weights
        merged into the base model weights.
        
        Args:
            model: The model with the adapter.
            adapter_name: Name of the adapter to merge.
                         If None, uses the active adapter.
        
        Returns:
            The merged model.
        """
        logger.info("Merging adapter with base model")
        
        if adapter_name is not None:
            # Set the specified adapter as active
            model.set_adapter(adapter_name)
        
        # Merge the adapter with the base model
        merged_model = model.merge_and_unload()
        
        logger.info("Successfully merged adapter with base model")
        return merged_model
    
    def export_adapter(
        self,
        adapter_name: str,
        output_path: str,
        include_metrics: bool = True,
    ) -> str:
        """
        Export an adapter to a zip file.
        
        Args:
            adapter_name: Name of the adapter to export.
            output_path: Path to save the exported adapter.
            include_metrics: Whether to include evaluation metrics.
        
        Returns:
            Path to the exported adapter.
        """
        adapter_info = self.get_adapter_info(adapter_name)
        if not adapter_info:
            raise ValueError(f"Adapter '{adapter_name}' not found in registry")
        
        if not os.path.exists(adapter_info.path):
            raise ValueError(f"Adapter path '{adapter_info.path}' does not exist")
        
        # Create a temporary directory for the export
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy adapter files
            adapter_export_dir = os.path.join(temp_dir, adapter_name)
            if os.path.isdir(adapter_info.path):
                shutil.copytree(adapter_info.path, adapter_export_dir)
            else:
                os.makedirs(adapter_export_dir, exist_ok=True)
                shutil.copy(adapter_info.path, adapter_export_dir)
            
            # Create metadata file
            metadata = adapter_info.to_dict()
            if not include_metrics:
                metadata.pop("metrics", None)
            
            with open(os.path.join(adapter_export_dir, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Create zip file
            if not output_path.endswith(".zip"):
                output_path += ".zip"
            
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(adapter_export_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
        
        logger.info(f"Exported adapter '{adapter_name}' to {output_path}")
        return output_path
    
    def import_adapter(
        self,
        zip_path: str,
        new_name: Optional[str] = None,
    ) -> AdapterInfo:
        """
        Import an adapter from a zip file.
        
        Args:
            zip_path: Path to the zip file containing the adapter.
            new_name: New name for the adapter.
                     If None, uses the name from the metadata.
        
        Returns:
            AdapterInfo object for the imported adapter.
        """
        if not os.path.exists(zip_path):
            raise ValueError(f"Zip file '{zip_path}' does not exist")
        
        # Create a temporary directory for the import
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract zip file
            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(temp_dir)
            
            # Find metadata file
            metadata_files = glob.glob(os.path.join(temp_dir, "**/metadata.json"), recursive=True)
            if not metadata_files:
                raise ValueError(f"No metadata.json found in zip file '{zip_path}'")
            
            # Load metadata
            with open(metadata_files[0], "r") as f:
                metadata = json.load(f)
            
            # Get adapter name
            adapter_name = new_name or metadata.get("name")
            if not adapter_name:
                raise ValueError(f"No adapter name found in metadata and no new name provided")
            
            # Get adapter directory
            adapter_dir = os.path.dirname(metadata_files[0])
            
            # Create adapter directory in adapters_dir
            adapter_path = os.path.join(self.adapters_dir, adapter_name)
            if os.path.exists(adapter_path):
                logger.warning(f"Adapter path '{adapter_path}' already exists, overwriting")
                if os.path.isdir(adapter_path):
                    shutil.rmtree(adapter_path)
                else:
                    os.remove(adapter_path)
            
            # Copy adapter files
            if os.path.isdir(adapter_dir):
                shutil.copytree(adapter_dir, adapter_path)
            else:
                os.makedirs(os.path.dirname(adapter_path), exist_ok=True)
                shutil.copy(adapter_dir, adapter_path)
            
            # Register adapter
            adapter_info = self.register_adapter(
                name=adapter_name,
                path=adapter_path,
                base_model=metadata.get("base_model", "unknown"),
                adapter_type=metadata.get("adapter_type", "unknown"),
                parameters=metadata.get("parameters", {}),
                metrics=metadata.get("metrics", {}),
            )
        
        logger.info(f"Imported adapter '{adapter_name}' from {zip_path}")
        return adapter_info
