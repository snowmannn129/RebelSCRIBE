#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Registry for RebelSCRIBE.

This module provides functionality for discovering, tracking, and managing AI models
from multiple sources, including HuggingFace, local storage, and custom repositories.
It supports model versioning, metadata management, and model discovery.

Example usage:
    ```python
    from src.ai.model_registry import (
        ModelRegistry, ModelSource, ModelInfo, ModelType,
        discover_models, get_model_info, register_model
    )
    
    # Get the model registry instance
    registry = ModelRegistry.get_instance()
    
    # Discover models from all sources
    models = registry.discover_models()
    
    # Get information about a specific model
    model_info = registry.get_model_info("llama-2-7b")
    
    # Register a new model
    new_model = ModelInfo(
        id="custom-model",
        name="My Custom Model",
        version="1.0",
        source=ModelSource.LOCAL,
        model_type=ModelType.LLAMA,
        path="/path/to/model",
        description="A custom fine-tuned model"
    )
    registry.register_model(new_model)
    
    # Get all models of a specific type
    llama_models = registry.get_models_by_type(ModelType.LLAMA)
    
    # Get all models from a specific source
    local_models = registry.get_models_by_source(ModelSource.LOCAL)
    
    # Check for model updates
    updates = registry.check_for_updates()
    ```
"""

import os
import json
import time
import logging
import threading
import re
import hashlib
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
import datetime

# Import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from huggingface_hub import HfApi, ModelFilter
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    # Define a dummy ModelFilter for testing
    class ModelFilter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

from src.utils.logging_utils import get_logger
from src.utils.file_utils import ensure_directory
from src.ai.progress_callbacks import (
    OperationType, ProgressStatus, ProgressInfo, ProgressCallback,
    create_operation, start_operation, update_progress,
    complete_operation, fail_operation
)

logger = get_logger(__name__)


class ModelSource(Enum):
    """Enum representing the source of a model."""
    HUGGINGFACE = auto()
    LOCAL = auto()
    CUSTOM = auto()
    UNKNOWN = auto()


class ModelType(Enum):
    """Enum representing the type of model."""
    LLAMA = auto()
    MISTRAL = auto()
    PHI = auto()
    FALCON = auto()
    MPT = auto()
    GPT2 = auto()
    T5 = auto()
    GGUF = auto()
    AWQ = auto()
    OTHER = auto()


class ModelFormat(Enum):
    """Enum representing the format of a model."""
    PYTORCH = auto()
    SAFETENSORS = auto()
    GGUF = auto()
    ONNX = auto()
    AWQ = auto()
    OTHER = auto()


@dataclass
class ModelInfo:
    """Class for storing model information."""
    id: str
    name: str
    version: str
    source: ModelSource
    model_type: ModelType
    path: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    format: ModelFormat = ModelFormat.OTHER
    size_bytes: Optional[int] = None
    parameters: Optional[int] = None
    quantization: Optional[str] = None
    last_updated: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model info to a dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data["source"] = self.source.name
        data["model_type"] = self.model_type.name
        data["format"] = self.format.name
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInfo':
        """Create a ModelInfo instance from a dictionary."""
        # Convert string enums back to enum values
        source = ModelSource[data.pop("source")]
        model_type = ModelType[data.pop("model_type")]
        format_str = data.pop("format", "OTHER")
        format_enum = ModelFormat[format_str]
        
        return cls(
            source=source,
            model_type=model_type,
            format=format_enum,
            **data
        )


class ModelRegistryError(Exception):
    """Base exception for model registry errors."""
    pass


class ModelNotFoundError(ModelRegistryError):
    """Exception raised when a model is not found."""
    pass


class ModelSourceError(ModelRegistryError):
    """Exception raised when there's an error with a model source."""
    pass


class ModelRegistry:
    """
    Singleton class for managing AI models from multiple sources.
    
    This class provides functionality for discovering, tracking, and managing AI models
    from multiple sources, including HuggingFace, local storage, and custom repositories.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'ModelRegistry':
        """Get the singleton instance of the ModelRegistry."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def __init__(self):
        """Initialize the model registry."""
        # Ensure this is only called once
        if ModelRegistry._instance is not None:
            raise RuntimeError("Use ModelRegistry.get_instance() to get the singleton instance")
        
        # Initialize registry data
        self._models: Dict[str, ModelInfo] = {}
        self._registry_file = self._get_registry_file_path()
        self._last_discovery: Dict[ModelSource, float] = {}
        self._discovery_cache: Dict[ModelSource, List[ModelInfo]] = {}
        
        # Load existing registry data
        self._load_registry()
    
    def _get_registry_file_path(self) -> str:
        """Get the path to the registry file."""
        # Get the registry directory
        registry_dir = os.environ.get(
            "REBELSCRIBE_REGISTRY_DIR", 
            os.path.join(os.path.expanduser("~"), ".rebelscribe", "registry")
        )
        
        # Ensure the directory exists
        ensure_directory(registry_dir)
        
        # Return the path to the registry file
        return os.path.join(registry_dir, "model_registry.json")
    
    def _load_registry(self) -> None:
        """Load the registry data from the registry file."""
        if not os.path.exists(self._registry_file):
            logger.info(f"Registry file not found at {self._registry_file}, creating new registry")
            return
        
        try:
            with open(self._registry_file, "r") as f:
                data = json.load(f)
            
            # Convert dictionaries to ModelInfo objects
            for model_id, model_data in data.get("models", {}).items():
                self._models[model_id] = ModelInfo.from_dict(model_data)
            
            # Load discovery timestamps
            for source_name, timestamp in data.get("last_discovery", {}).items():
                try:
                    source = ModelSource[source_name]
                    self._last_discovery[source] = timestamp
                except (KeyError, ValueError):
                    logger.warning(f"Unknown model source: {source_name}")
            
            logger.info(f"Loaded {len(self._models)} models from registry")
        
        except Exception as e:
            logger.error(f"Error loading registry: {e}", exc_info=True)
            # Create a backup of the corrupted file
            if os.path.exists(self._registry_file):
                backup_path = f"{self._registry_file}.bak.{int(time.time())}"
                try:
                    import shutil
                    shutil.copy2(self._registry_file, backup_path)
                    logger.info(f"Created backup of corrupted registry at {backup_path}")
                except Exception as backup_error:
                    logger.error(f"Error creating backup: {backup_error}")
    
    def _save_registry(self) -> None:
        """Save the registry data to the registry file."""
        try:
            # Convert ModelInfo objects to dictionaries
            models_dict = {model_id: model.to_dict() for model_id, model in self._models.items()}
            
            # Convert ModelSource enums to strings in last_discovery
            last_discovery_dict = {source.name: timestamp for source, timestamp in self._last_discovery.items()}
            
            # Create the data to save
            data = {
                "models": models_dict,
                "last_discovery": last_discovery_dict,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            # Save to file
            with open(self._registry_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self._models)} models to registry")
        
        except Exception as e:
            logger.error(f"Error saving registry: {e}", exc_info=True)
    
    def register_model(self, model: ModelInfo) -> None:
        """
        Register a model in the registry.
        
        Args:
            model: The model information to register.
        """
        with self._lock:
            self._models[model.id] = model
            self._save_registry()
            logger.info(f"Registered model: {model.id}")
    
    def unregister_model(self, model_id: str) -> bool:
        """
        Unregister a model from the registry.
        
        Args:
            model_id: The ID of the model to unregister.
            
        Returns:
            bool: True if the model was unregistered, False if it wasn't found.
        """
        with self._lock:
            if model_id in self._models:
                del self._models[model_id]
                self._save_registry()
                logger.info(f"Unregistered model: {model_id}")
                return True
            return False
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model.
        
        Args:
            model_id: The ID of the model to get information for.
            
        Returns:
            Optional[ModelInfo]: The model information, or None if not found.
        """
        return self._models.get(model_id)
    
    def get_all_models(self) -> List[ModelInfo]:
        """
        Get all registered models.
        
        Returns:
            List[ModelInfo]: A list of all registered models.
        """
        return list(self._models.values())
    
    def get_models_by_type(self, model_type: ModelType) -> List[ModelInfo]:
        """
        Get all models of a specific type.
        
        Args:
            model_type: The type of models to get.
            
        Returns:
            List[ModelInfo]: A list of models of the specified type.
        """
        return [model for model in self._models.values() if model.model_type == model_type]
    
    def get_models_by_source(self, source: ModelSource) -> List[ModelInfo]:
        """
        Get all models from a specific source.
        
        Args:
            source: The source of models to get.
            
        Returns:
            List[ModelInfo]: A list of models from the specified source.
        """
        return [model for model in self._models.values() if model.source == source]
    
    def search_models(self, query: str, 
                     model_type: Optional[ModelType] = None,
                     source: Optional[ModelSource] = None,
                     tags: Optional[List[str]] = None) -> List[ModelInfo]:
        """
        Search for models matching the given criteria.
        
        Args:
            query: The search query to match against model names and descriptions.
            model_type: Optional filter for model type.
            source: Optional filter for model source.
            tags: Optional list of tags to filter by.
            
        Returns:
            List[ModelInfo]: A list of models matching the search criteria.
        """
        results = []
        query = query.lower()
        
        for model in self._models.values():
            # Check if the model matches the query
            name_match = query in model.name.lower()
            desc_match = model.description and query in model.description.lower()
            id_match = query in model.id.lower()
            
            if not (name_match or desc_match or id_match):
                continue
            
            # Check if the model matches the type filter
            if model_type and model.model_type != model_type:
                continue
            
            # Check if the model matches the source filter
            if source and model.source != source:
                continue
            
            # Check if the model has all the required tags
            if tags:
                if not all(tag in model.tags for tag in tags):
                    continue
            
            results.append(model)
        
        return results
    
    def discover_models(self, 
                       sources: Optional[List[ModelSource]] = None,
                       force_refresh: bool = False,
                       progress_callback: Optional[ProgressCallback] = None) -> List[ModelInfo]:
        """
        Discover models from the specified sources.
        
        Args:
            sources: The sources to discover models from. If None, all sources are used.
            force_refresh: Whether to force a refresh of the discovery cache.
            progress_callback: Optional callback for tracking discovery progress.
            
        Returns:
            List[ModelInfo]: A list of discovered models.
        """
        # Create operation for tracking progress
        operation_id, progress_info = create_operation(
            OperationType.DISCOVERY, 
            operation_id="discover_models",
            callback=progress_callback
        )
        
        try:
            # Start the operation
            start_operation(operation_id, "Discovering models")
            
            # Determine which sources to use
            if sources is None:
                sources = list(ModelSource)
            
            # Initialize results
            all_discovered_models = []
            
            # Track progress
            total_sources = len(sources)
            current_source = 0
            
            # Discover models from each source
            for source in sources:
                current_source += 1
                source_name = source.name.lower()
                
                # Update progress
                update_progress(
                    operation_id,
                    current_source / total_sources,
                    f"Discovering models from {source_name}"
                )
                
                # Check if we need to refresh the cache
                cache_valid = (
                    not force_refresh and
                    source in self._last_discovery and
                    source in self._discovery_cache and
                    (time.time() - self._last_discovery[source]) < 3600  # 1 hour cache
                )
                
                if cache_valid:
                    # Use cached results
                    logger.debug(f"Using cached discovery results for {source_name}")
                    discovered_models = self._discovery_cache[source]
                else:
                    # Discover models from this source
                    logger.info(f"Discovering models from {source_name}")
                    
                    try:
                        if source == ModelSource.HUGGINGFACE:
                            discovered_models = self._discover_from_huggingface()
                        elif source == ModelSource.LOCAL:
                            discovered_models = self._discover_from_local()
                        elif source == ModelSource.CUSTOM:
                            discovered_models = self._discover_from_custom()
                        else:
                            logger.warning(f"Unknown model source: {source_name}")
                            discovered_models = []
                        
                        # Update cache
                        self._discovery_cache[source] = discovered_models
                        self._last_discovery[source] = time.time()
                    
                    except Exception as e:
                        logger.error(f"Error discovering models from {source_name}: {e}", exc_info=True)
                        discovered_models = []
                
                # Add to results
                all_discovered_models.extend(discovered_models)
            
            # Register all discovered models
            for model in all_discovered_models:
                self.register_model(model)
            
            # Save the registry
            self._save_registry()
            
            # Complete the operation
            complete_operation(
                operation_id,
                all_discovered_models,
                f"Discovered {len(all_discovered_models)} models"
            )
            
            return all_discovered_models
        
        except Exception as e:
            logger.error(f"Error discovering models: {e}", exc_info=True)
            fail_operation(operation_id, str(e), "Failed to discover models")
            return []
    
    def _discover_from_huggingface(self) -> List[ModelInfo]:
        """
        Discover models from HuggingFace.
        
        Returns:
            List[ModelInfo]: A list of discovered models.
        """
        if not HUGGINGFACE_AVAILABLE:
            logger.warning("HuggingFace Hub is not available. Install with: pip install huggingface_hub")
            return []
        
        try:
            # Initialize HuggingFace API
            api = HfApi()
            
            # Define model types to search for
            model_type_filters = [
                ("llama", ModelType.LLAMA),
                ("mistral", ModelType.MISTRAL),
                ("phi", ModelType.PHI),
                ("falcon", ModelType.FALCON),
                ("mpt", ModelType.MPT),
                ("gpt2", ModelType.GPT2),
                ("t5", ModelType.T5),
            ]
            
            # Initialize results
            discovered_models = []
            
            # Search for each model type
            for search_term, model_type in model_type_filters:
                # Search for models
                models = api.list_models(
                    filter=ModelFilter(
                        model_name=search_term,
                        task="text-generation"
                    ),
                    limit=50  # Limit to 50 models per type
                )
                
                # Convert to ModelInfo objects
                for model in models:
                    # Extract model information
                    model_id = model.id
                    model_name = model.id.split("/")[-1]
                    
                    # Skip if already in registry with same version
                    existing_model = self.get_model_info(model_id)
                    if existing_model and existing_model.last_updated == model.last_modified:
                        continue
                    
                    # Determine model format
                    format_enum = ModelFormat.OTHER
                    if any(f.endswith(".safetensors") for f in model.siblings):
                        format_enum = ModelFormat.SAFETENSORS
                    elif any(f.endswith(".bin") for f in model.siblings):
                        format_enum = ModelFormat.PYTORCH
                    elif any(f.endswith(".gguf") for f in model.siblings):
                        format_enum = ModelFormat.GGUF
                    elif any(f.endswith(".onnx") for f in model.siblings):
                        format_enum = ModelFormat.ONNX
                    elif any(f.endswith(".awq") for f in model.siblings):
                        format_enum = ModelFormat.AWQ
                    
                    # Extract quantization info from name
                    quantization = None
                    quant_patterns = [
                        r"Q(\d+)_(\w+)",  # Q4_K_M, Q5_K_S, etc.
                        r"(\d+)bit",      # 4bit, 8bit, etc.
                        r"int(\d+)",      # int4, int8, etc.
                    ]
                    
                    for pattern in quant_patterns:
                        match = re.search(pattern, model_name, re.IGNORECASE)
                        if match:
                            quantization = match.group(0)
                            break
                    
                    # Extract parameter count from name or description
                    parameters = None
                    param_patterns = [
                        r"(\d+)b\b",      # 7b, 13b, etc.
                        r"(\d+)B\b",      # 7B, 13B, etc.
                        r"(\d+)[.-]?bil", # 7bil, 7-bil, 7.bil, etc.
                    ]
                    
                    for pattern in param_patterns:
                        match = re.search(pattern, model_name, re.IGNORECASE)
                        if match:
                            try:
                                parameters = int(match.group(1)) * 1_000_000_000
                                break
                            except ValueError:
                                pass
                    
                    # Create ModelInfo object
                    model_info = ModelInfo(
                        id=model_id,
                        name=model_name,
                        version=model.sha,
                        source=ModelSource.HUGGINGFACE,
                        model_type=model_type,
                        url=f"https://huggingface.co/{model_id}",
                        description=model.description,
                        format=format_enum,
                        size_bytes=sum(s.size for s in model.siblings if hasattr(s, "size")),
                        parameters=parameters,
                        quantization=quantization,
                        last_updated=model.last_modified,
                        tags=model.tags,
                        metadata={
                            "author": model.author,
                            "downloads": model.downloads,
                            "likes": model.likes,
                        }
                    )
                    
                    discovered_models.append(model_info)
            
            logger.info(f"Discovered {len(discovered_models)} models from HuggingFace")
            return discovered_models
        
        except Exception as e:
            logger.error(f"Error discovering models from HuggingFace: {e}", exc_info=True)
            raise ModelSourceError(f"Error discovering models from HuggingFace: {str(e)}")
    
    def _discover_from_local(self) -> List[ModelInfo]:
        """
        Discover models from local storage.
        
        Returns:
            List[ModelInfo]: A list of discovered models.
        """
        try:
            # Get the models directory
            models_dir = os.environ.get(
                "REBELSCRIBE_MODELS_DIR", 
                os.path.join(os.path.expanduser("~"), ".rebelscribe", "models")
            )
            
            # Ensure the directory exists
            ensure_directory(models_dir)
            
            # Initialize results
            discovered_models = []
            
            # Walk through the models directory
            for root, dirs, files in os.walk(models_dir):
                # Check for model files
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    # Skip non-model files
                    if file_ext not in [".bin", ".pt", ".pth", ".safetensors", ".gguf", ".onnx", ".awq"]:
                        continue
                    
                    # Generate a unique ID for the model
                    rel_path = os.path.relpath(file_path, models_dir)
                    model_id = f"local:{rel_path}"
                    
                    # Skip if already in registry with same modification time
                    existing_model = self.get_model_info(model_id)
                    last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    if existing_model and existing_model.last_updated == last_modified:
                        continue
                    
                    # Determine model name
                    model_name = os.path.splitext(file)[0]
                    
                    # Determine model type
                    model_type = ModelType.OTHER
                    for type_name in ModelType.__members__:
                        if type_name.lower() in model_name.lower():
                            model_type = ModelType[type_name]
                            break
                    
                    # Determine model format
                    format_enum = ModelFormat.OTHER
                    if file_ext == ".safetensors":
                        format_enum = ModelFormat.SAFETENSORS
                    elif file_ext in [".bin", ".pt", ".pth"]:
                        format_enum = ModelFormat.PYTORCH
                    elif file_ext == ".gguf":
                        format_enum = ModelFormat.GGUF
                    elif file_ext == ".onnx":
                        format_enum = ModelFormat.ONNX
                    elif file_ext == ".awq":
                        format_enum = ModelFormat.AWQ
                    
                    # Extract quantization info from name
                    quantization = None
                    quant_patterns = [
                        r"Q(\d+)_(\w+)",  # Q4_K_M, Q5_K_S, etc.
                        r"(\d+)bit",      # 4bit, 8bit, etc.
                        r"int(\d+)",      # int4, int8, etc.
                    ]
                    
                    for pattern in quant_patterns:
                        match = re.search(pattern, model_name, re.IGNORECASE)
                        if match:
                            quantization = match.group(0)
                            break
                    
                    # Extract parameter count from name
                    parameters = None
                    param_patterns = [
                        r"(\d+)b\b",      # 7b, 13b, etc.
                        r"(\d+)B\b",      # 7B, 13B, etc.
                        r"(\d+)[.-]?bil", # 7bil, 7-bil, 7.bil, etc.
                    ]
                    
                    for pattern in param_patterns:
                        match = re.search(pattern, model_name, re.IGNORECASE)
                        if match:
                            try:
                                parameters = int(match.group(1)) * 1_000_000_000
                                break
                            except ValueError:
                                pass
                    
                    # Create ModelInfo object
                    model_info = ModelInfo(
                        id=model_id,
                        name=model_name,
                        version=hashlib.md5(file_path.encode()).hexdigest()[:8],
                        source=ModelSource.LOCAL,
                        model_type=model_type,
                        path=file_path,
                        description=f"Local model file: {rel_path}",
                        format=format_enum,
                        size_bytes=os.path.getsize(file_path),
                        parameters=parameters,
                        quantization=quantization,
                        last_updated=last_modified,
                        tags=["local"],
                        metadata={
                            "directory": os.path.dirname(rel_path),
                        }
                    )
                    
                    discovered_models.append(model_info)
            
            logger.info(f"Discovered {len(discovered_models)} models from local storage")
            return discovered_models
        
        except Exception as e:
            logger.error(f"Error discovering models from local storage: {e}", exc_info=True)
            raise ModelSourceError(f"Error discovering models from local storage: {str(e)}")
    
    def _discover_from_custom(self) -> List[ModelInfo]:
        """
        Discover models from custom sources.
        
        Returns:
            List[ModelInfo]: A list of discovered models.
        """
        try:
            # Get the custom sources directory
            custom_dir = os.environ.get(
                "REBELSCRIBE_CUSTOM_MODELS_DIR", 
                os.path.join(os.path.expanduser("~"), ".rebelscribe", "custom_models")
            )
            
            # Ensure the directory exists
            ensure_directory(custom_dir)
            
            # Check for a custom sources file
            sources_file = os.path.join(custom_dir, "sources.json")
            if not os.path.exists(sources_file):
                # Create a default sources file
                default_sources = {
                    "sources": [
                        {
                            "name": "Example Custom Source",
                            "url": "https://example.com/models.json",
                            "enabled": False
                        }
                    ]
                }
                
                with open(sources_file, "w") as f:
                    json.dump(default_sources, f, indent=2)
                
                logger.info(f"Created default custom sources file at {sources_file}")
                return []
            
            # Load the custom sources
            with open(sources_file, "r") as f:
                sources_data = json.load(f)
            
            # Initialize results
            discovered_models = []
            
            # Process each source
            for source in sources_data.get("sources", []):
                if not source.get("enabled", True):
                    continue
                
                source_name = source.get("name", "Unknown")
                source_url = source.get("url")
                
                if not source_url:
                    logger.warning(f"Missing URL for custom source: {source_name}")
                    continue
                
                # Fetch models from the source
                if not REQUESTS_AVAILABLE:
                    logger.warning("Requests library is not available. Install with: pip install requests")
                    continue
                
                try:
                    response = requests.get(source_url, timeout=10)
                    response.raise_for_status()
                    source_models = response.json()
                    
                    # Process each model
                    for model_data in source_models.get("models", []):
                        # Generate a unique ID for the model
                        model_id = f"custom:{source_name}:{model_data.get('id', model_data.get('name', 'unknown'))}"
                        
                        # Skip if already in registry with same version
                        existing_model = self.get_model_info(model_id)
                        if existing_model and existing_model.version == model_data.get("version", "unknown"):
                            continue
                        
                        # Determine model type
                        model_type_str = model_data.get("type", "OTHER").upper()
                        try:
                            model_type = ModelType[model_type_str]
                        except (KeyError, ValueError):
                            model_type = ModelType.OTHER
                        
                        # Determine model format
                        format_str = model_data.get("format", "OTHER").upper()
                        try:
                            format_enum = ModelFormat[format_str]
                        except (KeyError, ValueError):
                            format_enum = ModelFormat.OTHER
                        
                        # Create ModelInfo object
                        model_info = ModelInfo(
                            id=model_id,
                            name=model_data.get("name", "Unknown"),
                            version=model_data.get("version", "unknown"),
                            source=ModelSource.CUSTOM,
                            model_type=model_type,
                            url=model_data.get("url"),
                            path=model_data.get("path"),
                            description=model_data.get("description"),
                            format=format_enum,
                            size_bytes=model_data.get("size_bytes"),
                            parameters=model_data.get("parameters"),
                            quantization=model_data.get("quantization"),
                            last_updated=model_data.get("last_updated", datetime.datetime.now().isoformat()),
                            tags=model_data.get("tags", []),
                            metadata=model_data.get("metadata", {})
                        )
                        
                        discovered_models.append(model_info)
                
                except Exception as e:
                    logger.error(f"Error fetching models from {source_name}: {e}", exc_info=True)
            
            logger.info(f"Discovered {len(discovered_models)} models from custom sources")
            return discovered_models
        
        except Exception as e:
            logger.error(f"Error discovering models from custom sources: {e}", exc_info=True)
            raise ModelSourceError(f"Error discovering models from custom sources: {str(e)}")
    
    def check_for_updates(self, 
                         progress_callback: Optional[ProgressCallback] = None) -> Dict[str, ModelInfo]:
        """
        Check for updates to registered models.
        
        Args:
            progress_callback: Optional callback for tracking progress.
            
        Returns:
            Dict[str, ModelInfo]: A dictionary mapping model IDs to updated model information.
        """
        # Create operation for tracking progress
        operation_id, progress_info = create_operation(
            OperationType.UPDATE_CHECK, 
            operation_id="check_for_updates",
            callback=progress_callback
        )
        
        try:
            # Start the operation
            start_operation(operation_id, "Checking for model updates")
            
            # Discover models from all sources
            discovered_models = self.discover_models(progress_callback=progress_callback)
            
            # Find models with updates
            updates = {}
            
            for model in discovered_models:
                # Check if this is an update to an existing model
                existing_model = self.get_model_info(model.id)
                if existing_model and existing_model.version != model.version:
                    updates[model.id] = model
            
            # Complete the operation
            complete_operation(
                operation_id,
                updates,
                f"Found {len(updates)} model updates"
            )
            
            return updates
        
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)
            fail_operation(operation_id, str(e), "Failed to check for updates")
            return {}
    
    def share_model(self, model_id: str, destination_path: str) -> bool:
        """
        Share a model by copying it to a destination path.
        
        Args:
            model_id: The ID of the model to share.
            destination_path: The destination path to copy the model to.
            
        Returns:
            bool: True if the model was shared successfully, False otherwise.
        """
        try:
            # Get the model information
            model = self.get_model_info(model_id)
            if not model:
                logger.error(f"Model not found: {model_id}")
                return False
            
            # Check if the model has a local path
            if not model.path:
                logger.error(f"Model does not have a local path: {model_id}")
                return False
            
            # Check if the source path exists
            if not os.path.exists(model.path):
                logger.error(f"Model file not found: {model.path}")
                return False
            
            # Ensure the destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Copy the model file
            import shutil
            shutil.copy2(model.path, destination_path)
            
            logger.info(f"Shared model {model_id} to {destination_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error sharing model {model_id}: {e}", exc_info=True)
            return False
    
    def track_model_usage(self, model_id: str, usage_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Track usage of a model.
        
        Args:
            model_id: The ID of the model being used.
            usage_type: The type of usage (e.g., "inference", "fine-tuning").
            metadata: Optional metadata about the usage.
        """
        try:
            # Get the model information
            model = self.get_model_info(model_id)
            if not model:
                logger.warning(f"Tracking usage for unknown model: {model_id}")
                return
            
            # Get the usage tracking directory
            usage_dir = os.environ.get(
                "REBELSCRIBE_USAGE_DIR", 
                os.path.join(os.path.expanduser("~"), ".rebelscribe", "usage")
            )
            
            # Ensure the directory exists
            ensure_directory(usage_dir)
            
            # Create the usage data
            usage_data = {
                "model_id": model_id,
                "model_name": model.name,
                "model_type": model.model_type.name,
                "usage_type": usage_type,
                "timestamp": datetime.datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Generate a unique filename
            filename = f"{model_id.replace('/', '_')}_{int(time.time())}.json"
            file_path = os.path.join(usage_dir, filename)
            
            # Save the usage data
            with open(file_path, "w") as f:
                json.dump(usage_data, f, indent=2)
            
            logger.debug(f"Tracked usage of model {model_id} for {usage_type}")
        
        except Exception as e:
            logger.error(f"Error tracking model usage: {e}", exc_info=True)
    
    def get_model_usage_stats(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for models.
        
        Args:
            model_id: Optional ID of a specific model to get statistics for.
            
        Returns:
            Dict[str, Any]: A dictionary containing usage statistics.
        """
        try:
            # Get the usage tracking directory
            usage_dir = os.environ.get(
                "REBELSCRIBE_USAGE_DIR", 
                os.path.join(os.path.expanduser("~"), ".rebelscribe", "usage")
            )
            
            # Check if the directory exists
            if not os.path.exists(usage_dir):
                return {"total_usage": 0, "models": {}}
            
            # Initialize statistics
            stats = {
                "total_usage": 0,
                "models": {},
                "usage_types": {}
            }
            
            # Process each usage file
            for filename in os.listdir(usage_dir):
                if not filename.endswith(".json"):
                    continue
                
                file_path = os.path.join(usage_dir, filename)
                
                try:
                    with open(file_path, "r") as f:
                        usage_data = json.load(f)
                    
                    # Skip if we're looking for a specific model and this isn't it
                    if model_id and usage_data.get("model_id") != model_id:
                        continue
                    
                    # Update total usage
                    stats["total_usage"] += 1
                    
                    # Update model-specific usage
                    model_id_key = usage_data.get("model_id", "unknown")
                    if model_id_key not in stats["models"]:
                        stats["models"][model_id_key] = {
                            "name": usage_data.get("model_name", "Unknown"),
                            "type": usage_data.get("model_type", "OTHER"),
                            "total_usage": 0,
                            "usage_types": {}
                        }
                    
                    stats["models"][model_id_key]["total_usage"] += 1
                    
                    # Update usage type statistics
                    usage_type = usage_data.get("usage_type", "unknown")
                    
                    # Update global usage type stats
                    if usage_type not in stats["usage_types"]:
                        stats["usage_types"][usage_type] = 0
                    stats["usage_types"][usage_type] += 1
                    
                    # Update model-specific usage type stats
                    if usage_type not in stats["models"][model_id_key]["usage_types"]:
                        stats["models"][model_id_key]["usage_types"][usage_type] = 0
                    stats["models"][model_id_key]["usage_types"][usage_type] += 1
                
                except Exception as e:
                    logger.error(f"Error processing usage file {filename}: {e}", exc_info=True)
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting model usage statistics: {e}", exc_info=True)
            return {"total_usage": 0, "models": {}, "error": str(e)}


# Convenience functions for working with the model registry

def get_model_registry() -> ModelRegistry:
    """
    Get the singleton instance of the ModelRegistry.
    
    Returns:
        ModelRegistry: The model registry instance.
    """
    return ModelRegistry.get_instance()


def discover_models(sources: Optional[List[ModelSource]] = None,
                   force_refresh: bool = False,
                   progress_callback: Optional[ProgressCallback] = None) -> List[ModelInfo]:
    """
    Discover models from the specified sources.
    
    Args:
        sources: The sources to discover models from. If None, all sources are used.
        force_refresh: Whether to force a refresh of the discovery cache.
        progress_callback: Optional callback for tracking discovery progress.
        
    Returns:
        List[ModelInfo]: A list of discovered models.
    """
    registry = get_model_registry()
    return registry.discover_models(sources, force_refresh, progress_callback)


def get_model_info(model_id: str) -> Optional[ModelInfo]:
    """
    Get information about a specific model.
    
    Args:
        model_id: The ID of the model to get information for.
        
    Returns:
        Optional[ModelInfo]: The model information, or None if not found.
    """
    registry = get_model_registry()
    return registry.get_model_info(model_id)


def register_model(model: ModelInfo) -> None:
    """
    Register a model in the registry.
    
    Args:
        model: The model information to register.
    """
    registry = get_model_registry()
    registry.register_model(model)


def unregister_model(model_id: str) -> bool:
    """
    Unregister a model from the registry.
    
    Args:
        model_id: The ID of the model to unregister.
        
    Returns:
        bool: True if the model was unregistered, False if it wasn't found.
    """
    registry = get_model_registry()
    return registry.unregister_model(model_id)


def search_models(query: str, 
                 model_type: Optional[ModelType] = None,
                 source: Optional[ModelSource] = None,
                 tags: Optional[List[str]] = None) -> List[ModelInfo]:
    """
    Search for models matching the given criteria.
    
    Args:
        query: The search query to match against model names and descriptions.
        model_type: Optional filter for model type.
        source: Optional filter for model source.
        tags: Optional list of tags to filter by.
        
    Returns:
        List[ModelInfo]: A list of models matching the search criteria.
    """
    registry = get_model_registry()
    return registry.search_models(query, model_type, source, tags)


def check_for_updates(progress_callback: Optional[ProgressCallback] = None) -> Dict[str, ModelInfo]:
    """
    Check for updates to registered models.
    
    Args:
        progress_callback: Optional callback for tracking progress.
        
    Returns:
        Dict[str, ModelInfo]: A dictionary mapping model IDs to updated model information.
    """
    registry = get_model_registry()
    return registry.check_for_updates(progress_callback)


def track_model_usage(model_id: str, usage_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Track usage of a model.
    
    Args:
        model_id: The ID of the model being used.
        usage_type: The type of usage (e.g., "inference", "fine-tuning").
        metadata: Optional metadata about the usage.
    """
    registry = get_model_registry()
    registry.track_model_usage(model_id, usage_type, metadata)


def get_model_usage_stats(model_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get usage statistics for models.
    
    Args:
        model_id: Optional ID of a specific model to get statistics for.
        
    Returns:
        Dict[str, Any]: A dictionary containing usage statistics.
    """
    registry = get_model_registry()
    return registry.get_model_usage_stats(model_id)
