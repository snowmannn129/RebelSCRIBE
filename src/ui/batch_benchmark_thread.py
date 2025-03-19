#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Batch Benchmark Thread

This module implements a thread for running batch benchmarks in the background.
"""

from PyQt6.QtCore import QThread, pyqtSignal

from src.utils.logging_utils import get_logger
from src.ai.batch_benchmarking import (
    BatchBenchmark, BatchResult, run_batch_benchmark
)
from src.ai.progress_callbacks import ProgressInfo

logger = get_logger(__name__)


class BatchBenchmarkThread(QThread):
    """Thread for running batch benchmarks in the background."""
    
    # Signal emitted when progress is updated
    progress_updated = pyqtSignal(ProgressInfo)
    
    # Signal emitted when the benchmark is complete
    benchmark_complete = pyqtSignal(BatchResult)
    
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(str)
    
    def __init__(self, batch: BatchBenchmark):
        """
        Initialize the batch benchmark thread.
        
        Args:
            batch: The batch benchmark to run.
        """
        super().__init__()
        self.batch = batch
    
    def run(self):
        """Run the batch benchmark."""
        try:
            # Define progress callback
            def progress_callback(progress_info: ProgressInfo):
                self.progress_updated.emit(progress_info)
            
            # Run the batch benchmark
            result = run_batch_benchmark(self.batch, progress_callback)
            
            # Emit the result
            self.benchmark_complete.emit(result)
        
        except Exception as e:
            logger.error(f"Error running batch benchmark: {e}")
            self.error_occurred.emit(str(e))
