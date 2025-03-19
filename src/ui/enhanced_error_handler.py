#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Enhanced UI Error Handler

This module implements an enhanced central error handler for UI errors.
It provides a way to handle UI errors in a consistent way with advanced features:
- Error severity categorization
- Component-based error categorization
- Different UI treatments based on error severity
- Error history for debugging and troubleshooting
- Error callbacks for specialized error handling
- Error aggregation and rate limiting
"""

import time
import json
import csv
import re
import uuid
import os
from enum import Enum, auto
from typing import Optional, Callable, Dict, List, Tuple, Any, Set, Pattern, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict

from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, QComboBox,
    QCheckBox, QLineEdit, QTextEdit, QScrollArea, QFrame, QSplitter,
    QToolTip, QApplication
)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPoint, QRect, QSize
from PyQt6.QtGui import QColor, QIcon, QPixmap, QPainter, QFont, QFontMetrics

from src.utils.logging_utils import get_logger
from src.ui.event_bus import get_event_bus, ErrorOccurredEvent, EventCategory, EventPriority
from src.utils.file_utils import ensure_directory

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Enum for error severity levels."""
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3
    
    def __str__(self) -> str:
        """Return a string representation of the severity level."""
        return self.name
    
    @classmethod
    def from_string(cls, severity_str: str) -> 'ErrorSeverity':
        """Create an ErrorSeverity from a string."""
        try:
            return cls[severity_str.upper()]
        except KeyError:
            logger.warning(f"Invalid severity string: {severity_str}. Using ERROR as default.")
            return cls.ERROR


class DialogType(Enum):
    """Enum for dialog types."""
    MODAL = auto()
    NON_MODAL = auto()
    NOTIFICATION = auto()


class NotificationPosition(Enum):
    """Enum for notification positions."""
    TOP_RIGHT = auto()
    TOP_LEFT = auto()
    BOTTOM_RIGHT = auto()
    BOTTOM_LEFT = auto()
    CENTER = auto()


@dataclass
class ErrorRecord:
    """Class for storing error information."""
    id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    component: Optional[str]
    timestamp: datetime
    context: Optional[Dict[str, Any]] = field(default_factory=dict)
    handled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error record to a dictionary."""
        result = asdict(self)
        result['severity'] = str(self.severity)
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorRecord':
        """Create an ErrorRecord from a dictionary."""
        data = data.copy()
        data['severity'] = ErrorSeverity.from_string(data['severity'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ErrorFilter:
    """Class for filtering errors."""
    def __init__(self, 
                 severity: Optional[ErrorSeverity] = None,
                 component: Optional[str] = None,
                 error_type: Optional[str] = None,
                 time_range: Optional[Tuple[datetime, datetime]] = None,
                 message_pattern: Optional[Union[str, Pattern]] = None):
        """
        Initialize the error filter.
        
        Args:
            severity: Filter by severity level
            component: Filter by component
            error_type: Filter by error type
            time_range: Filter by time range (start, end)
            message_pattern: Filter by message pattern (string or compiled regex)
        """
        self.severity = severity
        self.component = component
        self.error_type = error_type
        self.time_range = time_range
        
        if isinstance(message_pattern, str):
            self.message_pattern = re.compile(message_pattern)
        else:
            self.message_pattern = message_pattern
    
    def matches(self, error: ErrorRecord) -> bool:
        """Check if an error matches this filter."""
        # Check severity
        if self.severity is not None and error.severity != self.severity:
            return False
        
        # Check component
        if self.component is not None:
            if error.component is None:
                return False
            if not error.component.startswith(self.component):
                return False
        
        # Check error type
        if self.error_type is not None and error.error_type != self.error_type:
            return False
        
        # Check time range
        if self.time_range is not None:
            start, end = self.time_range
            if error.timestamp < start or error.timestamp > end:
                return False
        
        # Check message pattern
        if self.message_pattern is not None:
            if not self.message_pattern.search(error.error_message):
                return False
        
        return True


class ErrorCallback:
    """Class for error callbacks."""
    def __init__(self, 
                 callback_id: str,
                 callback: Callable[[ErrorRecord], None],
                 filter: Optional[ErrorFilter] = None,
                 priority: int = 0):
        """
        Initialize the error callback.
        
        Args:
            callback_id: Unique identifier for this callback
            callback: The callback function
            filter: Optional filter to determine which errors trigger this callback
            priority: Priority of this callback (higher values = higher priority)
        """
        self.callback_id = callback_id
        self.callback = callback
        self.filter = filter
        self.priority = priority
    
    def matches(self, error: ErrorRecord) -> bool:
        """Check if an error matches this callback's filter."""
        if self.filter is None:
            return True
        return self.filter.matches(error)


class ErrorPattern:
    """Class for error patterns used in aggregation."""
    def __init__(self, pattern: Union[str, Pattern]):
        """
        Initialize the error pattern.
        
        Args:
            pattern: Regex pattern for matching error messages
        """
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        else:
            self.pattern = pattern
        
        self.count = 0
        self.first_seen = None
        self.last_seen = None
        self.examples = []
    
    def matches(self, error: ErrorRecord) -> bool:
        """Check if an error matches this pattern."""
        return bool(self.pattern.search(error.error_message))
    
    def add_error(self, error: ErrorRecord) -> None:
        """Add an error to this pattern."""
        self.count += 1
        
        if self.first_seen is None:
            self.first_seen = error.timestamp
        
        self.last_seen = error.timestamp
        
        # Keep a few examples
        if len(self.examples) < 5:
            self.examples.append(error)


class NonBlockingNotification(QWidget):
    """Widget for displaying non-blocking notifications."""
    
    closed = pyqtSignal()
    
    def __init__(self, 
                 title: str, 
                 message: str, 
                 severity: ErrorSeverity,
                 timeout: Optional[int] = None,
                 parent: Optional[QWidget] = None,
                 details: Optional[str] = None,
                 actions: Optional[List[Tuple[str, Callable]]] = None):
        """
        Initialize the notification.
        
        Args:
            title: The notification title
            message: The notification message
            severity: The error severity
            timeout: Timeout in milliseconds (None for no timeout)
            parent: The parent widget
            details: Optional detailed error information
            actions: Optional list of action buttons (label, callback)
        """
        super().__init__(parent)
        
        self.severity = severity
        self.timeout = timeout
        self.details = details
        self.actions = actions or []
        self.timer = None
        self.remaining_time = timeout
        self.show_details = False
        
        # Set up the UI
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(350)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create notification frame
        self.frame = QFrame()
        self.frame.setObjectName("notificationFrame")
        self.frame_layout = QVBoxLayout(self.frame)
        
        # Get color and icon based on severity
        if severity == ErrorSeverity.INFO:
            icon = QIcon.fromTheme("dialog-information")
            self.color = QColor(0, 120, 215)  # Blue
            self.bg_color = QColor(240, 249, 255)
            self.border_color = QColor(200, 229, 255)
        elif severity == ErrorSeverity.WARNING:
            icon = QIcon.fromTheme("dialog-warning")
            self.color = QColor(255, 185, 0)  # Yellow
            self.bg_color = QColor(255, 250, 230)
            self.border_color = QColor(255, 213, 128)
        elif severity == ErrorSeverity.ERROR:
            icon = QIcon.fromTheme("dialog-error")
            self.color = QColor(232, 17, 35)  # Red
            self.bg_color = QColor(255, 235, 238)
            self.border_color = QColor(255, 153, 164)
        else:  # CRITICAL
            icon = QIcon.fromTheme("dialog-error")
            self.color = QColor(136, 23, 152)  # Purple
            self.bg_color = QColor(245, 235, 255)
            self.border_color = QColor(210, 180, 222)
        
        # Create header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 5)
        
        # Add icon
        icon_label = QLabel()
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(24, 24))
        else:
            # Fallback icons if theme icons are not available
            if severity == ErrorSeverity.INFO:
                icon_label.setText("ℹ️")
            elif severity == ErrorSeverity.WARNING:
                icon_label.setText("⚠️")
            elif severity == ErrorSeverity.ERROR or severity == ErrorSeverity.CRITICAL:
                icon_label.setText("❌")
        
        icon_label.setFixedSize(24, 24)
        header_layout.addWidget(icon_label)
        
        # Add title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {self.color.name()}; font-weight: bold;")
        header_layout.addWidget(title_label, 1)
        
        # Add close button
        close_button = QPushButton("×")
        close_button.setFixedSize(24, 24)
        close_button.setStyleSheet("border: none; font-weight: bold; font-size: 16px;")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.close)
        header_layout.addWidget(close_button)
        
        self.frame_layout.addLayout(header_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"background-color: {self.border_color.name()};")
        separator.setFixedHeight(1)
        self.frame_layout.addWidget(separator)
        
        # Add message
        message_layout = QVBoxLayout()
        message_layout.setContentsMargins(10, 5, 10, 10)
        
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message_layout.addWidget(self.message_label)
        
        # Add details section if provided
        if details:
            self.details_button = QPushButton("Show Details")
            self.details_button.setStyleSheet(f"color: {self.color.name()}; background: transparent; border: none; text-decoration: underline;")
            self.details_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.details_button.clicked.connect(self.toggle_details)
            message_layout.addWidget(self.details_button, 0, Qt.AlignmentFlag.AlignLeft)
            
            self.details_text = QTextEdit()
            self.details_text.setReadOnly(True)
            self.details_text.setText(details)
            self.details_text.setFixedHeight(100)
            self.details_text.setVisible(False)
            message_layout.addWidget(self.details_text)
        
        # Add action buttons if provided
        if actions:
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(0, 5, 0, 0)
            
            for label, callback in actions:
                button = QPushButton(label)
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.color.name()};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 5px 10px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.color.darker(110).name()};
                    }}
                    QPushButton:pressed {{
                        background-color: {self.color.darker(120).name()};
                    }}
                """)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(lambda checked, cb=callback: self.handle_action(cb))
                buttons_layout.addWidget(button)
            
            buttons_layout.addStretch(1)
            message_layout.addLayout(buttons_layout)
        
        # Add progress bar for timeout
        if timeout is not None:
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, timeout)
            self.progress_bar.setValue(timeout)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setFixedHeight(3)
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {self.bg_color.darker(105).name()};
                    border: none;
                    border-radius: 1px;
                }}
                QProgressBar::chunk {{
                    background-color: {self.color.name()};
                    border-radius: 1px;
                }}
            """)
            message_layout.addWidget(self.progress_bar)
            
            # Set up timer for progress bar
            self.timer = QTimer(self)
            self.timer.setInterval(100)  # Update every 100ms
            self.timer.timeout.connect(self.update_progress)
            self.timer.start()
        
        self.frame_layout.addLayout(message_layout)
        
        # Add frame to main layout
        self.main_layout.addWidget(self.frame)
        
        # Set up timeout
        if timeout is not None:
            QTimer.singleShot(timeout, self.close)
        
        # Set up shadow effect
        self.setGraphicsEffect(self.create_shadow_effect())
        
        # Set up stylesheet
        self.frame.setStyleSheet(f"""
            #notificationFrame {{
                background-color: {self.bg_color.name()};
                border: 1px solid {self.border_color.name()};
                border-radius: 8px;
            }}
        """)
    
    def create_shadow_effect(self) -> 'QGraphicsDropShadowEffect':
        """Create a shadow effect for the notification."""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        return shadow
    
    def toggle_details(self) -> None:
        """Toggle the visibility of the details section."""
        self.show_details = not self.show_details
        self.details_text.setVisible(self.show_details)
        self.details_button.setText("Hide Details" if self.show_details else "Show Details")
        
        # Adjust size
        self.adjustSize()
    
    def handle_action(self, callback: Callable) -> None:
        """Handle an action button click."""
        try:
            callback()
        except Exception as e:
            logger.error(f"Error in notification action callback: {e}")
        finally:
            self.close()
    
    def update_progress(self) -> None:
        """Update the progress bar."""
        if self.timer and self.remaining_time is not None:
            self.remaining_time = max(0, self.remaining_time - 100)
            self.progress_bar.setValue(self.remaining_time)
            
            if self.remaining_time <= 0:
                self.timer.stop()
    
    def pause_timeout(self) -> None:
        """Pause the timeout timer."""
        if self.timer:
            self.timer.stop()
    
    def resume_timeout(self) -> None:
        """Resume the timeout timer."""
        if self.timer and self.remaining_time > 0:
            self.timer.start()
    
    def enterEvent(self, event) -> None:
        """Handle mouse enter event."""
        self.pause_timeout()
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave event."""
        self.resume_timeout()
        super().leaveEvent(event)
    
    def close(self) -> None:
        """Close the notification."""
        if self.timer:
            self.timer.stop()
        
        self.closed.emit()
        super().close()
    
    def paintEvent(self, event) -> None:
        """Paint the notification background."""
        # No need to paint anything as we're using a frame with stylesheet
        pass


class NotificationManager(QObject):
    """Manager for non-blocking notifications."""
    
    def __init__(self, parent=None):
        """
        Initialize the notification manager.
        
        Args:
            parent: The parent QObject
        """
        super().__init__(parent)
        
        self.notifications = []
        self.position = NotificationPosition.TOP_RIGHT
        self.spacing = 10
        self.max_notifications = 5
        self.default_timeouts = {
            ErrorSeverity.INFO: 5000,      # 5 seconds
            ErrorSeverity.WARNING: 10000,  # 10 seconds
            ErrorSeverity.ERROR: 15000,    # 15 seconds
            ErrorSeverity.CRITICAL: None   # No timeout
        }
        self.animation_duration = 250  # ms
        self.fade_effect = True
        self.slide_effect = True
        self.stacking_order = "newest_on_top"  # or "oldest_on_top"
        
        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(16)  # ~60fps
        self.animation_timer.timeout.connect(self._update_animations)
        self.animations = {}  # {notification: {start_time, duration, start_pos, end_pos}}
    
    def set_position(self, position: NotificationPosition) -> None:
        """
        Set the notification position.
        
        Args:
            position: The position for notifications
        """
        if position != self.position:
            self.position = position
            self.update_positions(animate=True)
    
    def set_default_timeout(self, severity: ErrorSeverity, timeout: Optional[int]) -> None:
        """
        Set the default timeout for a severity level.
        
        Args:
            severity: The error severity
            timeout: Timeout in milliseconds (None for no timeout)
        """
        self.default_timeouts[severity] = timeout
    
    def configure(self, 
                 max_notifications: Optional[int] = None,
                 spacing: Optional[int] = None,
                 animation_duration: Optional[int] = None,
                 fade_effect: Optional[bool] = None,
                 slide_effect: Optional[bool] = None,
                 stacking_order: Optional[str] = None) -> None:
        """
        Configure the notification manager.
        
        Args:
            max_notifications: Maximum number of notifications to show at once
            spacing: Spacing between notifications in pixels
            animation_duration: Duration of animations in milliseconds
            fade_effect: Whether to use fade effect for notifications
            slide_effect: Whether to use slide effect for notifications
            stacking_order: Order to stack notifications ("newest_on_top" or "oldest_on_top")
        """
        if max_notifications is not None:
            self.max_notifications = max_notifications
        
        if spacing is not None:
            self.spacing = spacing
        
        if animation_duration is not None:
            self.animation_duration = animation_duration
        
        if fade_effect is not None:
            self.fade_effect = fade_effect
        
        if slide_effect is not None:
            self.slide_effect = slide_effect
        
        if stacking_order is not None:
            if stacking_order in ["newest_on_top", "oldest_on_top"]:
                self.stacking_order = stacking_order
            else:
                logger.warning(f"Invalid stacking order: {stacking_order}. Using 'newest_on_top'.")
        
        # Update positions with new configuration
        self.update_positions()
    
    def show_notification(self, 
                         title: str, 
                         message: str, 
                         severity: ErrorSeverity,
                         timeout: Optional[int] = None,
                         details: Optional[str] = None,
                         actions: Optional[List[Tuple[str, Callable]]] = None) -> NonBlockingNotification:
        """
        Show a notification.
        
        Args:
            title: The notification title
            message: The notification message
            severity: The error severity
            timeout: Timeout in milliseconds (None for no timeout, use default if not specified)
            details: Optional detailed error information
            actions: Optional list of action buttons (label, callback)
            
        Returns:
            The created notification widget
        """
        # Use default timeout if not specified
        if timeout is None:
            timeout = self.default_timeouts.get(severity)
        
        # Create notification
        notification = NonBlockingNotification(
            title=title,
            message=message,
            severity=severity,
            timeout=timeout,
            details=details,
            actions=actions
        )
        notification.closed.connect(lambda: self.remove_notification(notification))
        
        # Add to list (at beginning if newest on top, at end if oldest on top)
        if self.stacking_order == "newest_on_top":
            self.notifications.insert(0, notification)
        else:
            self.notifications.append(notification)
        
        # Limit number of notifications
        while len(self.notifications) > self.max_notifications:
            if self.stacking_order == "newest_on_top":
                # Remove oldest (last) notification
                if len(self.notifications) > 0:
                    notification_to_remove = self.notifications[-1]
                    self.remove_notification(notification_to_remove)
            else:
                # Remove newest (first) notification
                if len(self.notifications) > 0:
                    notification_to_remove = self.notifications[0]
                    self.remove_notification(notification_to_remove)
        
        # Update positions and show with animation
        self.update_positions(animate=True)
        
        # Apply initial animation effects
        if self.fade_effect:
            notification.setWindowOpacity(0.0)
        
        notification.show()
        
        # Start animation
        if self.fade_effect or self.slide_effect:
            self._start_show_animation(notification)
        
        return notification
    
    def remove_notification(self, notification: NonBlockingNotification) -> None:
        """
        Remove a notification.
        
        Args:
            notification: The notification to remove
        """
        try:
            if notification in self.notifications:
                # Start hide animation
                if (self.fade_effect or self.slide_effect) and notification.isVisible():
                    self._start_hide_animation(notification)
                else:
                    # Remove immediately if no animation
                    self._remove_notification_immediately(notification)
        except Exception as e:
            logger.error(f"Error removing notification: {e}")
            # Ensure notification is removed from list even if there's an error
            if notification in self.notifications:
                self.notifications.remove(notification)
    
    def _remove_notification_immediately(self, notification: NonBlockingNotification) -> None:
        """
        Remove a notification immediately without animation.
        
        Args:
            notification: The notification to remove
        """
        if notification in self.notifications:
            self.notifications.remove(notification)
            
            # Stop any ongoing animations
            if notification in self.animations:
                del self.animations[notification]
            
            # Update positions of remaining notifications
            self.update_positions(animate=True)
    
    def _start_show_animation(self, notification: NonBlockingNotification) -> None:
        """
        Start the show animation for a notification.
        
        Args:
            notification: The notification to animate
        """
        # Calculate target position
        target_pos = notification.pos()
        
        # Set initial position for slide effect
        if self.slide_effect:
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            if self.position in [NotificationPosition.TOP_RIGHT, NotificationPosition.TOP_LEFT]:
                # Slide from top
                start_pos = QPoint(target_pos.x(), -notification.height())
            elif self.position in [NotificationPosition.BOTTOM_RIGHT, NotificationPosition.BOTTOM_LEFT]:
                # Slide from bottom
                start_pos = QPoint(target_pos.x(), screen_geometry.height())
            else:  # CENTER
                # Fade in place
                start_pos = target_pos
            
            notification.move(start_pos)
        else:
            start_pos = target_pos
        
        # Set up animation
        self.animations[notification] = {
            "type": "show",
            "start_time": time.time() * 1000,
            "duration": self.animation_duration,
            "start_pos": start_pos,
            "end_pos": target_pos,
            "start_opacity": 0.0 if self.fade_effect else 1.0,
            "end_opacity": 1.0
        }
        
        # Start animation timer if not already running
        if not self.animation_timer.isActive():
            self.animation_timer.start()
    
    def _start_hide_animation(self, notification: NonBlockingNotification) -> None:
        """
        Start the hide animation for a notification.
        
        Args:
            notification: The notification to animate
        """
        # Calculate target position for slide effect
        start_pos = notification.pos()
        
        if self.slide_effect:
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            if self.position in [NotificationPosition.TOP_RIGHT, NotificationPosition.TOP_LEFT]:
                # Slide to top
                end_pos = QPoint(start_pos.x(), -notification.height())
            elif self.position in [NotificationPosition.BOTTOM_RIGHT, NotificationPosition.BOTTOM_LEFT]:
                # Slide to bottom
                end_pos = QPoint(start_pos.x(), screen_geometry.height())
            else:  # CENTER
                # Fade in place
                end_pos = start_pos
        else:
            end_pos = start_pos
        
        # Set up animation
        self.animations[notification] = {
            "type": "hide",
            "start_time": time.time() * 1000,
            "duration": self.animation_duration,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "start_opacity": notification.windowOpacity(),
            "end_opacity": 0.0 if self.fade_effect else notification.windowOpacity()
        }
        
        # Start animation timer if not already running
        if not self.animation_timer.isActive():
            self.animation_timer.start()
    
    def _update_animations(self) -> None:
        """Update all ongoing animations."""
        current_time = time.time() * 1000
        completed_animations = []
        
        for notification, animation in self.animations.items():
            # Calculate progress (0.0 to 1.0)
            elapsed = current_time - animation["start_time"]
            progress = min(1.0, elapsed / animation["duration"])
            
            # Apply easing function (ease out cubic)
            t = 1.0 - (1.0 - progress) ** 3
            
            # Update position if using slide effect
            if self.slide_effect:
                start_x, start_y = animation["start_pos"].x(), animation["start_pos"].y()
                end_x, end_y = animation["end_pos"].x(), animation["end_pos"].y()
                
                current_x = start_x + (end_x - start_x) * t
                current_y = start_y + (end_y - start_y) * t
                
                notification.move(int(current_x), int(current_y))
            
            # Update opacity if using fade effect
            if self.fade_effect:
                start_opacity = animation["start_opacity"]
                end_opacity = animation["end_opacity"]
                current_opacity = start_opacity + (end_opacity - start_opacity) * t
                
                notification.setWindowOpacity(current_opacity)
            
            # Check if animation is complete
            if progress >= 1.0:
                completed_animations.append((notification, animation["type"]))
        
        # Handle completed animations
        for notification, animation_type in completed_animations:
            del self.animations[notification]
            
            if animation_type == "hide":
                # Remove notification after hide animation
                if notification in self.notifications:
                    self.notifications.remove(notification)
                    notification.deleteLater()
                    
                    # Update positions of remaining notifications
                    self.update_positions(animate=True)
        
        # Stop timer if no more animations
        if not self.animations:
            self.animation_timer.stop()
    
    def update_positions(self, animate: bool = False) -> None:
        """
        Update the positions of all notifications.
        
        Args:
            animate: Whether to animate the position changes
        """
        if not self.notifications:
            return
        
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Calculate positions based on notification position setting
        positions = []
        y_offset = self.spacing
        
        for notification in self.notifications:
            notification_height = notification.sizeHint().height()
            notification_width = notification.width()
            
            if self.position == NotificationPosition.TOP_RIGHT:
                x = screen_geometry.width() - notification_width - self.spacing
                positions.append(QPoint(x, y_offset))
            elif self.position == NotificationPosition.TOP_LEFT:
                x = self.spacing
                positions.append(QPoint(x, y_offset))
            elif self.position == NotificationPosition.BOTTOM_RIGHT:
                x = screen_geometry.width() - notification_width - self.spacing
                y = screen_geometry.height() - notification_height - y_offset
                positions.append(QPoint(x, y))
            elif self.position == NotificationPosition.BOTTOM_LEFT:
                x = self.spacing
                y = screen_geometry.height() - notification_height - y_offset
                positions.append(QPoint(x, y))
            elif self.position == NotificationPosition.CENTER:
                x = (screen_geometry.width() - notification_width) // 2
                y = (screen_geometry.height() - notification_height) // 2
                positions.append(QPoint(x, y))
            
            y_offset += notification_height + self.spacing
        
        # Apply positions
        for i, notification in enumerate(self.notifications):
            if animate and notification.isVisible() and notification not in self.animations:
                # Animate position change
                start_pos = notification.pos()
                end_pos = positions[i]
                
                # Only animate if position actually changed
                if start_pos != end_pos:
                    self.animations[notification] = {
                        "type": "move",
                        "start_time": time.time() * 1000,
                        "duration": self.animation_duration,
                        "start_pos": start_pos,
                        "end_pos": end_pos,
                        "start_opacity": notification.windowOpacity(),
                        "end_opacity": notification.windowOpacity()
                    }
                    
                    # Start animation timer if not already running
                    if not self.animation_timer.isActive():
                        self.animation_timer.start()
            else:
                # Set position immediately
                notification.move(positions[i])
    
    def clear_all(self) -> None:
        """Close all notifications."""
        # Make a copy of the list since we'll be modifying it
        notifications = self.notifications.copy()
        
        for notification in notifications:
            notification.close()


class EnhancedErrorHandler(QObject):
    """
    Enhanced central error handler for UI errors.
    
    This class provides a way to handle UI errors in a consistent way with advanced features:
    - Error severity categorization
    - Component-based error categorization
    - Different UI treatments based on error severity
    - Error history for debugging and troubleshooting
    - Error callbacks for specialized error handling
    - Error aggregation and rate limiting
    """
    
    # Define signals for error events
    error_occurred = pyqtSignal(ErrorRecord)
    
    def __init__(self, parent=None):
        """
        Initialize the error handler.
        
        Args:
            parent: The parent QObject
        """
        super().__init__(parent)
        
        # Get event bus instance
        self.event_bus = get_event_bus()
        
        # Initialize error history
        self.error_history: List[ErrorRecord] = []
        self.max_history_size = 1000
        
        # Initialize error callbacks
        self.callbacks: Dict[str, ErrorCallback] = {}
        
        # Initialize UI treatment configuration
        self.ui_treatments: Dict[ErrorSeverity, Dict[str, Any]] = {
            ErrorSeverity.INFO: {
                'dialog_type': DialogType.NOTIFICATION,
                'use_non_blocking': True,
                'timeout': 5000,
                'position': NotificationPosition.TOP_RIGHT
            },
            ErrorSeverity.WARNING: {
                'dialog_type': DialogType.NOTIFICATION,
                'use_non_blocking': True,
                'timeout': 10000,
                'position': NotificationPosition.TOP_RIGHT
            },
            ErrorSeverity.ERROR: {
                'dialog_type': DialogType.MODAL,
                'use_non_blocking': False,
                'timeout': None,
                'position': None
            },
            ErrorSeverity.CRITICAL: {
                'dialog_type': DialogType.MODAL,
                'use_non_blocking': False,
                'timeout': None,
                'position': None
            }
        }
        
        # Initialize notification manager
        self.notification_manager = NotificationManager()
        
        # Initialize error aggregation
        self.error_aggregation_enabled = False
        self.error_patterns: List[ErrorPattern] = []
        self.aggregation_timeout = 5000  # ms
        self.pattern_matching_enabled = False
        
        # Initialize rate limiting
        self.rate_limiting_enabled = False
        self.rate_limit_threshold = 5
        self.rate_limit_window = 60000  # ms (1 minute)
        self.error_counts: Dict[str, int] = {}
        self.error_timestamps: Dict[str, List[datetime]] = {}
        self.use_exponential_backoff = False
        self.backoff_base = 2
        self.backoff_max = 60000  # ms (1 minute)
        
        # Initialize component registry
        self.component_registry: Dict[str, Dict[str, Any]] = {}
        
        logger.debug("Enhanced UI Error Handler initialized")
    
    def handle_error(self, 
                    error_type: str, 
                    error_message: str, 
                    severity: ErrorSeverity = ErrorSeverity.ERROR, 
                    component: Optional[str] = None, 
                    parent: Optional[QWidget] = None, 
                    show_dialog: bool = True,
                    context: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle an error.
        
        Args:
            error_type: The type of error
            error_message: The error message
            severity: The error severity
            component: The component that generated the error
            parent: The parent widget for the error dialog
            show_dialog: Whether to show an error dialog
            context: Additional context information
        
        Returns:
            The ID of the error record
        """
        # Create error record
        error_id = str(uuid.uuid4())
        error_record = ErrorRecord(
            id=error_id,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            component=component,
            timestamp=datetime.now(),
            context=context or {},
            handled=False
        )
        
        # Log the error
        log_level = {
            ErrorSeverity.INFO: logger.info,
            ErrorSeverity.WARNING: logger.warning,
            ErrorSeverity.ERROR: logger.error,
            ErrorSeverity.CRITICAL: logger.critical
        }.get(severity, logger.error)
        
        component_str = f"[{component}] " if component else ""
        log_level(f"{component_str}{error_type}: {error_message}")
        
        # Add to history
        self._add_to_history(error_record)
        
        # Emit the error signal
        self.error_occurred.emit(error_record)
        
        # Emit the error event
        self.event_bus.emit_event(ErrorOccurredEvent(
            error_type=error_type,
            error_message=error_message
        ))
        
        # Check for error aggregation
        if self.error_aggregation_enabled and self._should_aggregate(error_record):
            # Error was aggregated, don't show dialog
            return error_id
        
        # Check for rate limiting
        if self.rate_limiting_enabled and self._should_rate_limit(error_record):
            # Error was rate limited, don't show dialog
            return error_id
        
        # Show error dialog if requested
        if show_dialog:
            self._show_error_dialog(error_record, parent)
        
        # Call error callbacks
        self._call_callbacks(error_record)
        
        # Mark as handled
        error_record.handled = True
        
        return error_id
    
    def handle_exception(self, 
                        exception: Exception, 
                        context: str = None, 
                        severity: Optional[ErrorSeverity] = None, 
                        component: Optional[str] = None, 
                        parent: Optional[QWidget] = None, 
                        show_dialog: bool = True) -> str:
        """
        Handle an exception.
        
        Args:
            exception: The exception to handle
            context: The context in which the exception occurred
            severity: The error severity (if None, will be determined automatically)
            component: The component that generated the error
            parent: The parent widget for the error dialog
            show_dialog: Whether to show an error dialog
        
        Returns:
            The ID of the error record
        """
        error_type = type(exception).__name__
        error_message = f"{context}: {str(exception)}" if context else str(exception)
        
        # Determine severity if not provided
        if severity is None:
            severity = self._determine_severity(exception)
        
        # Create context dictionary
        context_dict = {
            'exception_type': error_type,
            'traceback': getattr(exception, '__traceback__', None)
        }
        
        if context:
            context_dict['context'] = context
        
        return self.handle_error(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            component=component,
            parent=parent,
            show_dialog=show_dialog,
            context=context_dict
        )
    
    def log_error(self, 
                 error_type: str, 
                 error_message: str, 
                 severity: ErrorSeverity = ErrorSeverity.ERROR, 
                 component: Optional[str] = None) -> str:
        """
        Log an error without displaying a UI message.
        
        Args:
            error_type: The type of error
            error_message: The error message
            severity: The error severity
            component: The component that generated the error
        
        Returns:
            The ID of the error record
        """
        return self.handle_error(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            component=component,
            show_dialog=False
        )
    
    def get_error_history(self, 
                         severity: Optional[ErrorSeverity] = None, 
                         component: Optional[str] = None, 
                         time_range: Optional[Tuple[datetime, datetime]] = None, 
                         limit: Optional[int] = None) -> List[ErrorRecord]:
        """
        Get the history of errors, optionally filtered by severity, component, and time range.
        
        Args:
            severity: Filter by severity level
            component: Filter by component
            time_range: Filter by time range (start, end)
            limit: Maximum number of errors to return
        
        Returns:
            List of error records
        """
        # Create filter
        error_filter = ErrorFilter(
            severity=severity,
            component=component,
            time_range=time_range
        )
        
        # Apply filter
        filtered_errors = [
            error for error in self.error_history
            if error_filter.matches(error)
        ]
        
        # Apply limit
        if limit is not None:
            filtered_errors = filtered_errors[-limit:]
        
        return filtered_errors
    
    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.error_history.clear()
        logger.debug("Error history cleared")
    
    def set_error_callback(self, 
                          error_type: Optional[str] = None, 
                          severity: Optional[ErrorSeverity] = None, 
                          component: Optional[str] = None, 
                          callback: Optional[Callable[[ErrorRecord], None]] = None) -> str:
        """
        Set a callback for errors of a specific type, severity, and/or component.
        
        Args:
            error_type: The type of error to match
            severity: The severity level to match
            component: The component to match
            callback: The callback function
        
        Returns:
            A callback ID that can be used to remove the callback
        """
        if callback is None:
            raise ValueError("Callback function cannot be None")
        
        # Create filter
        error_filter = ErrorFilter(
            error_type=error_type,
            severity=severity,
            component=component
        )
        
        # Create callback ID
        callback_id = str(uuid.uuid4())
        
        # Create callback
        error_callback = ErrorCallback(
            callback_id=callback_id,
            callback=callback,
            filter=error_filter
        )
        
        # Add to callbacks
        self.callbacks[callback_id] = error_callback
        
        logger.debug(f"Error callback registered with ID {callback_id}")
        
        return callback_id
    
    def remove_error_callback(self, callback_id: str) -> bool:
        """
        Remove an error callback by its ID.
        
        Args:
            callback_id: The ID of the callback to remove
        
        Returns:
            True if the callback was removed, False if it wasn't found
        """
        if callback_id in self.callbacks:
            del self.callbacks[callback_id]
            logger.debug(f"Error callback with ID {callback_id} removed")
            return True
        
        logger.warning(f"Error callback with ID {callback_id} not found")
        return False
    
    def configure_ui_treatment(self, 
                              severity: ErrorSeverity, 
                              dialog_type: DialogType, 
                              use_non_blocking: bool = False, 
                              timeout: Optional[int] = None, 
                              position: Optional[NotificationPosition] = None) -> None:
        """
        Configure the UI treatment for errors of a specific severity.
        
        Args:
            severity: The severity level to configure
            dialog_type: The type of dialog to use
            use_non_blocking: Whether to use non-blocking notifications
            timeout: The timeout for non-blocking notifications in milliseconds
            position: The position for non-blocking notifications
        """
        self.ui_treatments[severity] = {
            'dialog_type': dialog_type,
            'use_non_blocking': use_non_blocking,
            'timeout': timeout,
            'position': position
        }
        
        logger.debug(f"UI treatment configured for severity {severity}")
    
    def enable_error_aggregation(self, 
                                enabled: bool = True, 
                                timeout: int = 5000, 
                                pattern_matching: bool = False) -> None:
        """
        Enable or disable error aggregation for similar errors.
        
        Args:
            enabled: Whether to enable error aggregation
            timeout: The timeout for aggregating errors in milliseconds
            pattern_matching: Whether to use pattern matching for identifying similar errors
        """
        self.error_aggregation_enabled = enabled
        self.aggregation_timeout = timeout
        self.pattern_matching_enabled = pattern_matching
        
        if not enabled:
            self.error_patterns.clear()
        
        logger.debug(f"Error aggregation {'enabled' if enabled else 'disabled'}")
    
    def configure_rate_limiting(self, 
                               threshold: int = 5, 
                               time_window: int = 60000, 
                               use_exponential_backoff: bool = False) -> None:
        """
        Configure rate limiting for error notifications.
        
        Args:
            threshold: The maximum number of errors to show in the time window
            time_window: The time window in milliseconds
            use_exponential_backoff: Whether to use exponential backoff for repeated errors
        """
        self.rate_limiting_enabled = True
        self.rate_limit_threshold = threshold
        self.rate_limit_window = time_window
        self.use_exponential_backoff = use_exponential_backoff
        
        logger.debug("Rate limiting configured")
    
    def report_error(self, 
                    error_id: str, 
                    include_system_info: bool = True, 
                    anonymize: bool = False,
                    additional_info: Optional[Dict[str, Any]] = None,
                    report_service: Optional[str] = None) -> bool:
        """
        Report an error to the error reporting system.
        
        Args:
            error_id: The ID of the error to report
            include_system_info: Whether to include system information in the report
            anonymize: Whether to anonymize sensitive data in the report
            additional_info: Additional information to include in the report
            report_service: The reporting service to use (default: configured service)
            
        Returns:
            True if the report was sent successfully, False otherwise
        """
        # Find the error record
        error_record = None
        for error in self.error_history:
            if error.id == error_id:
                error_record = error
                break
        
        if error_record is None:
            logger.warning(f"Error with ID {error_id} not found")
            return False
        
        # Create report data
        report_data = error_record.to_dict()
        
        # Add additional information if provided
        if additional_info:
            report_data['additional_info'] = additional_info
        
        # Add system information if requested
        if include_system_info:
            import platform
            import sys
            import psutil
            import os
            
            # Get application version from config or environment
            try:
                from src.utils.config_manager import ConfigManager
                config = ConfigManager()
                app_version = config.get("application", "version", "1.0.0")
            except:
                app_version = os.environ.get("APP_VERSION", "1.0.0")
            
            # Get basic system info
            system_info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': sys.version,
                'application_version': app_version
            }
            
            # Add memory information
            try:
                memory = psutil.virtual_memory()
                system_info['memory'] = {
                    'total': memory.total,
                    'available': memory.available,
                    'percent_used': memory.percent
                }
            except:
                # psutil might not be available
                pass
            
            # Add disk information
            try:
                disk = psutil.disk_usage('/')
                system_info['disk'] = {
                    'total': disk.total,
                    'free': disk.free,
                    'percent_used': disk.percent
                }
            except:
                pass
            
            # Add environment variables (excluding sensitive ones)
            env_vars = {}
            sensitive_keys = ['key', 'token', 'password', 'secret', 'credential', 'auth']
            for key, value in os.environ.items():
                # Skip sensitive environment variables
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    continue
                env_vars[key] = value
            
            system_info['environment'] = env_vars
            
            report_data['system_info'] = system_info
        
        # Add application state information
        try:
            from src.ui.state_manager import get_state_manager
            state_manager = get_state_manager()
            
            # Get non-sensitive state information
            app_state = {}
            sensitive_keys = ['password', 'token', 'key', 'secret', 'credential', 'auth']
            
            for key in state_manager.get_all_keys():
                # Skip sensitive state keys
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    continue
                
                try:
                    value = state_manager.get_state(key)
                    app_state[key] = value
                except:
                    pass
            
            report_data['application_state'] = app_state
        except:
            # State manager might not be available
            pass
        
        # Add stack trace if available
        if 'context' in report_data and 'traceback' in report_data['context']:
            import traceback
            try:
                tb = report_data['context']['traceback']
                if tb:
                    stack_trace = ''.join(traceback.format_tb(tb))
                    report_data['stack_trace'] = stack_trace
            except:
                pass
        
        # Anonymize sensitive data if requested
        if anonymize:
            self._anonymize_report_data(report_data)
        
        # Send report to error reporting service
        success = self._send_error_report(report_data, report_service)
        
        if success:
            logger.info(f"Error report for ID {error_id} sent successfully")
        else:
            logger.warning(f"Failed to send error report for ID {error_id}")
        
        return success
    
    def _send_error_report(self, report_data: Dict[str, Any], service: Optional[str] = None) -> bool:
        """
        Send an error report to the configured reporting service.
        
        Args:
            report_data: The report data to send
            service: The reporting service to use (default: configured service)
            
        Returns:
            True if the report was sent successfully, False otherwise
        """
        # Determine which service to use
        if service is None:
            # Get configured service from config
            try:
                from src.utils.config_manager import ConfigManager
                config = ConfigManager()
                service = config.get("error_reporting", "service", "local")
            except:
                service = "local"
        
        # Send report based on service
        if service == "local":
            # Save to local file
            try:
                import os
                from datetime import datetime
                
                # Create reports directory if it doesn't exist
                reports_dir = os.path.join(os.path.expanduser("~"), ".rebelscribe", "error_reports")
                os.makedirs(reports_dir, exist_ok=True)
                
                # Create filename with timestamp and error ID
                error_id = report_data.get("id", "unknown")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"error_{timestamp}_{error_id}.json"
                filepath = os.path.join(reports_dir, filename)
                
                # Write report to file
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2)
                
                logger.info(f"Error report saved to {filepath}")
                return True
            except Exception as e:
                logger.error(f"Failed to save error report: {e}")
                return False
        
        elif service == "email":
            # Send report via email
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                from src.utils.config_manager import ConfigManager
                
                # Get email configuration
                config = ConfigManager()
                smtp_server = config.get("error_reporting", "smtp_server", "")
                smtp_port = config.get("error_reporting", "smtp_port", 587)
                smtp_username = config.get("error_reporting", "smtp_username", "")
                smtp_password = config.get("error_reporting", "smtp_password", "")
                from_email = config.get("error_reporting", "from_email", "")
                to_email = config.get("error_reporting", "to_email", "")
                
                if not all([smtp_server, smtp_username, smtp_password, from_email, to_email]):
                    logger.error("Email configuration is incomplete")
                    return False
                
                # Create email message
                msg = MIMEMultipart()
                msg["From"] = from_email
                msg["To"] = to_email
                msg["Subject"] = f"RebelSCRIBE Error Report: {report_data.get('error_type', 'Unknown Error')}"
                
                # Add error details to email body
                body = f"""
                Error Report ID: {report_data.get('id', 'Unknown')}
                Error Type: {report_data.get('error_type', 'Unknown')}
                Error Message: {report_data.get('error_message', 'No message')}
                Severity: {report_data.get('severity', 'Unknown')}
                Component: {report_data.get('component', 'Unknown')}
                Timestamp: {report_data.get('timestamp', 'Unknown')}
                
                Please see the attached JSON file for complete details.
                """
                msg.attach(MIMEText(body, "plain"))
                
                # Add report as JSON attachment
                attachment = MIMEText(json.dumps(report_data, indent=2))
                attachment.add_header("Content-Disposition", "attachment", filename="error_report.json")
                msg.attach(attachment)
                
                # Send email
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                
                logger.info(f"Error report sent via email to {to_email}")
                return True
            except Exception as e:
                logger.error(f"Failed to send error report via email: {e}")
                return False
        
        elif service == "http":
            # Send report via HTTP POST
            try:
                import requests
                from src.utils.config_manager import ConfigManager
                
                # Get HTTP configuration
                config = ConfigManager()
                endpoint_url = config.get("error_reporting", "endpoint_url", "")
                api_key = config.get("error_reporting", "api_key", "")
                
                if not endpoint_url:
                    logger.error("HTTP endpoint URL is not configured")
                    return False
                
                # Prepare headers
                headers = {
                    "Content-Type": "application/json"
                }
                
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                # Send POST request
                response = requests.post(
                    endpoint_url,
                    json=report_data,
                    headers=headers,
                    timeout=10
                )
                
                # Check response
                if response.status_code in (200, 201, 202):
                    logger.info(f"Error report sent to {endpoint_url} successfully")
                    return True
                else:
                    logger.warning(f"Error report HTTP request failed with status {response.status_code}: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Failed to send error report via HTTP: {e}")
                return False
        
        else:
            logger.warning(f"Unknown error reporting service: {service}")
            return False
    
    def export_error_history(self, 
                            file_path: str, 
                            format: str = "json", 
                            include_system_info: bool = True, 
                            anonymize: bool = False) -> bool:
        """
        Export the error history to a file.
        
        Args:
            file_path: The path to export to
            format: The format to export in ("json", "csv", "txt")
            include_system_info: Whether to include system information
            anonymize: Whether to anonymize sensitive data
            
        Returns:
            True if the export was successful, False otherwise
        """
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory(directory)
        
        # Convert error history to dictionaries
        error_dicts = [error.to_dict() for error in self.error_history]
        
        # Add system information if requested
        if include_system_info:
            import platform
            import sys
            
            system_info = {
                'platform': platform.platform(),
                'python_version': sys.version,
                'application_version': '1.0.0'  # Replace with actual version
            }
            
            for error_dict in error_dicts:
                error_dict['system_info'] = system_info
        
        # Anonymize sensitive data if requested
        if anonymize:
            for error_dict in error_dicts:
                self._anonymize_report_data(error_dict)
        
        try:
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(error_dicts, f, indent=2)
            
            elif format.lower() == "csv":
                if not error_dicts:
                    # Create empty CSV with headers
                    with open(file_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['id', 'error_type', 'error_message', 'severity', 
                                        'component', 'timestamp', 'handled'])
                else:
                    # Write CSV with data
                    with open(file_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        # Write header
                        writer.writerow(error_dicts[0].keys())
                        # Write data
                        for error_dict in error_dicts:
                            writer.writerow(error_dict.values())
            
            elif format.lower() == "txt":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("RebelSCRIBE Error History\n")
                    f.write("=======================\n\n")
                    
                    for error_dict in error_dicts:
                        f.write(f"ID: {error_dict['id']}\n")
                        f.write(f"Type: {error_dict['error_type']}\n")
                        f.write(f"Message: {error_dict['error_message']}\n")
                        f.write(f"Severity: {error_dict['severity']}\n")
                        f.write(f"Component: {error_dict['component']}\n")
                        f.write(f"Timestamp: {error_dict['timestamp']}\n")
                        f.write(f"Handled: {error_dict['handled']}\n")
                        
                        if 'context' in error_dict and error_dict['context']:
                            f.write("Context:\n")
                            for key, value in error_dict['context'].items():
                                f.write(f"  {key}: {value}\n")
                        
                        if 'system_info' in error_dict:
                            f.write("System Info:\n")
                            for key, value in error_dict['system_info'].items():
                                f.write(f"  {key}: {value}\n")
                        
                        f.write("\n")
            
            else:
                logger.warning(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Error history exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting error history: {e}")
            return False
    
    def get_aggregated_errors(self) -> Dict[str, Tuple[ErrorRecord, int]]:
        """
        Get the aggregated errors with their counts.
        
        Returns:
            Dictionary mapping error types to tuples of (example error, count)
        """
        result = {}
        
        for pattern in self.error_patterns:
            if pattern.examples:
                result[pattern.pattern.pattern] = (pattern.examples[0], pattern.count)
        
        return result
    
    def get_component_error_statistics(self, 
                                      component: Optional[str] = None, 
                                      time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Dict[ErrorSeverity, int]]:
        """
        Get error statistics for components.
        
        Args:
            component: The component to get statistics for, or None for all components
            time_range: The time range to get statistics for, or None for all time
            
        Returns:
            A dictionary mapping component names to dictionaries mapping severity to count
        """
        # Create filter
        error_filter = ErrorFilter(
            component=component,
            time_range=time_range
        )
        
        # Apply filter
        filtered_errors = [
            error for error in self.error_history
            if error_filter.matches(error)
        ]
        
        # Group by component and severity
        result = defaultdict(lambda: defaultdict(int))
        
        for error in filtered_errors:
            comp = error.component or "unknown"
            result[comp][error.severity] += 1
        
        return result
    
    def register_component(self, 
                          component_name: str, 
                          parent_component: Optional[str] = None, 
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a component with the error handler.
        
        Args:
            component_name: The name of the component
            parent_component: The name of the parent component, if any
            metadata: Additional metadata for the component
        """
        self.component_registry[component_name] = {
            'parent': parent_component,
            'metadata': metadata or {}
        }
        
        logger.debug(f"Component {component_name} registered with error handler")
    
    def unregister_component(self, component_name: str) -> bool:
        """
        Unregister a component from the error handler.
        
        Args:
            component_name: The name of the component
            
        Returns:
            True if the component was unregistered, False if it wasn't found
        """
        if component_name in self.component_registry:
            del self.component_registry[component_name]
            logger.debug(f"Component {component_name} unregistered from error handler")
            return True
        
        logger.warning(f"Component {component_name} not found in registry")
        return False
    
    def get_component_hierarchy(self, component_name: str) -> List[str]:
        """
        Get the hierarchy of a component.
        
        Args:
            component_name: The name of the component
            
        Returns:
            List of component names in the hierarchy, from root to leaf
        """
        if component_name not in self.component_registry:
            return [component_name]
        
        result = []
        current = component_name
        
        while current is not None:
            result.insert(0, current)
            current = self.component_registry.get(current, {}).get('parent')
        
        return result
    
    def _add_to_history(self, error: ErrorRecord) -> None:
        """
        Add an error to the history.
        
        Args:
            error: The error record to add
        """
        self.error_history.append(error)
        
        # Limit history size
        while len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
    
    def _show_error_dialog(self, error: ErrorRecord, parent: Optional[QWidget] = None) -> None:
        """
        Show an error dialog.
        
        Args:
            error: The error record
            parent: The parent widget for the dialog
        """
        # Get UI treatment for this severity
        treatment = self.ui_treatments.get(error.severity, {})
        dialog_type = treatment.get('dialog_type', DialogType.MODAL)
        use_non_blocking = treatment.get('use_non_blocking', False)
        timeout = treatment.get('timeout', None)
        position = treatment.get('position', NotificationPosition.TOP_RIGHT)
        
        # Set notification manager position
        if position is not None:
            self.notification_manager.set_position(position)
        
        # Show dialog based on type
        if dialog_type == DialogType.NOTIFICATION or use_non_blocking:
            # Show non-blocking notification
            title = f"{error.severity}: {error.error_type}"
            self.notification_manager.show_notification(
                title=title,
                message=error.error_message,
                severity=error.severity,
                timeout=timeout
            )
        
        elif dialog_type == DialogType.NON_MODAL:
            # Show non-modal dialog
            dialog = QMessageBox(parent)
            dialog.setWindowTitle(f"{error.severity}: {error.error_type}")
            dialog.setText(error.error_message)
            
            if error.severity == ErrorSeverity.INFO:
                dialog.setIcon(QMessageBox.Icon.Information)
            elif error.severity == ErrorSeverity.WARNING:
                dialog.setIcon(QMessageBox.Icon.Warning)
            elif error.severity == ErrorSeverity.ERROR:
                dialog.setIcon(QMessageBox.Icon.Critical)
            else:  # CRITICAL
                dialog.setIcon(QMessageBox.Icon.Critical)
            
            dialog.setWindowModality(Qt.WindowModality.NonModal)
            dialog.show()
        
        else:  # MODAL
            # Show modal dialog
            if error.severity == ErrorSeverity.INFO:
                QMessageBox.information(
                    parent,
                    f"Information: {error.error_type}",
                    error.error_message
                )
            elif error.severity == ErrorSeverity.WARNING:
                QMessageBox.warning(
                    parent,
                    f"Warning: {error.error_type}",
                    error.error_message
                )
            elif error.severity == ErrorSeverity.ERROR:
                QMessageBox.critical(
                    parent,
                    f"Error: {error.error_type}",
                    error.error_message
                )
            else:  # CRITICAL
                QMessageBox.critical(
                    parent,
                    f"Critical Error: {error.error_type}",
                    error.error_message
                )
    
    def _call_callbacks(self, error: ErrorRecord) -> None:
        """
        Call callbacks for an error.
        
        Args:
            error: The error record
        """
        # Get matching callbacks
        matching_callbacks = [
            callback for callback in self.callbacks.values()
            if callback.matches(error)
        ]
        
        # Sort by priority (higher first)
        matching_callbacks.sort(key=lambda cb: cb.priority, reverse=True)
        
        # Call callbacks
        for callback in matching_callbacks:
            try:
                callback.callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def _should_aggregate(self, error: ErrorRecord) -> bool:
        """
        Check if an error should be aggregated.
        
        Args:
            error: The error record
            
        Returns:
            True if the error should be aggregated, False otherwise
        """
        if not self.error_aggregation_enabled:
            return False
        
        # Check for exact match
        for pattern in self.error_patterns:
            if pattern.matches(error):
                # Check if within timeout
                if pattern.last_seen is not None:
                    time_diff = (error.timestamp - pattern.last_seen).total_seconds() * 1000
                    if time_diff <= self.aggregation_timeout:
                        # Aggregate error
                        pattern.add_error(error)
                        return True
        
        # No match or outside timeout, create new pattern
        if self.pattern_matching_enabled:
            # Create pattern from error message
            pattern = ErrorPattern(re.escape(error.error_message))
        else:
            # Use exact match
            pattern = ErrorPattern(f"^{re.escape(error.error_message)}$")
        
        pattern.add_error(error)
        self.error_patterns.append(pattern)
        
        return False
    
    def _should_rate_limit(self, error: ErrorRecord) -> bool:
        """
        Check if an error should be rate limited.
        
        Args:
            error: The error record
            
        Returns:
            True if the error should be rate limited, False otherwise
        """
        if not self.rate_limiting_enabled:
            return False
        
        # Create key for this error
        key = f"{error.error_type}:{error.component or 'unknown'}"
        
        # Initialize if needed
        if key not in self.error_timestamps:
            self.error_timestamps[key] = []
            self.error_counts[key] = 0
        
        # Add timestamp
        self.error_timestamps[key].append(error.timestamp)
        
        # Remove old timestamps
        cutoff = error.timestamp - timedelta(milliseconds=self.rate_limit_window)
        self.error_timestamps[key] = [
            ts for ts in self.error_timestamps[key]
            if ts >= cutoff
        ]
        
        # Check count
        count = len(self.error_timestamps[key])
        
        if self.use_exponential_backoff:
            # Calculate backoff
            backoff = min(
                self.backoff_max,
                self.backoff_base ** self.error_counts[key]
            )
            
            # Check if enough time has passed
            if self.error_counts[key] > 0:
                last_time = self.error_timestamps[key][-2] if len(self.error_timestamps[key]) > 1 else None
                if last_time is not None:
                    time_diff = (error.timestamp - last_time).total_seconds() * 1000
                    if time_diff < backoff:
                        # Rate limit this error
                        return True
            
            # Increment count
            self.error_counts[key] += 1
            
            return False
        else:
            # Simple threshold-based rate limiting
            if count > self.rate_limit_threshold:
                # Rate limit this error
                return True
            
            return False
    
    def _determine_severity(self, exception: Exception) -> ErrorSeverity:
        """
        Determine the severity of an exception.
        
        Args:
            exception: The exception
            
        Returns:
            The error severity
        """
        # Map common exception types to severities
        exception_type = type(exception).__name__
        
        # Critical exceptions - severe issues that may affect application stability
        if exception_type in [
            'SystemError', 'MemoryError', 'RecursionError',
            'KeyboardInterrupt', 'SystemExit', 'SegmentationFault',
            'DatabaseCorruptionError', 'OutOfMemoryError', 'StackOverflowError',
            'FatalError', 'CriticalIOError', 'SystemShutdownError'
        ]:
            return ErrorSeverity.CRITICAL
        
        # Error exceptions - issues that prevent a specific operation from completing
        if exception_type in [
            'ValueError', 'TypeError', 'AttributeError', 'IndexError',
            'KeyError', 'FileNotFoundError', 'PermissionError',
            'ImportError', 'ModuleNotFoundError', 'OSError',
            'IOError', 'ConnectionError', 'TimeoutError',
            'ZeroDivisionError', 'AssertionError', 'NotImplementedError',
            'UnboundLocalError', 'UnicodeError', 'LookupError',
            'StopIteration', 'BufferError', 'ArithmeticError',
            'EnvironmentError', 'ReferenceError', 'SyntaxError',
            'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeTranslateError'
        ]:
            return ErrorSeverity.ERROR
        
        # Warning exceptions - potential issues that may require user attention
        if exception_type in [
            'DeprecationWarning', 'PendingDeprecationWarning',
            'RuntimeWarning', 'SyntaxWarning', 'UserWarning',
            'FutureWarning', 'ImportWarning', 'UnicodeWarning',
            'BytesWarning', 'ResourceWarning', 'Warning',
            'PerformanceWarning', 'ConfigurationWarning', 'DataLossWarning',
            'IncompleteReadWarning', 'NetworkWarning', 'FilesystemWarning'
        ]:
            return ErrorSeverity.WARNING
        
        # Info exceptions - informational messages that don't require user action
        if exception_type in [
            'InfoMessage', 'DebugInfo', 'ProcessInfo', 'OperationInfo',
            'StatusInfo', 'ProgressInfo', 'CompletionInfo', 'NotificationInfo'
        ]:
            return ErrorSeverity.INFO
        
        # Check for custom exception attributes that might indicate severity
        if hasattr(exception, 'severity'):
            severity_attr = getattr(exception, 'severity')
            if isinstance(severity_attr, str):
                try:
                    return ErrorSeverity.from_string(severity_attr)
                except (ValueError, KeyError):
                    pass
            elif isinstance(severity_attr, int) and 0 <= severity_attr <= 3:
                return ErrorSeverity(severity_attr)
        
        # Check for exception message patterns that might indicate severity
        message = str(exception).lower()
        
        if any(term in message for term in ['critical', 'fatal', 'crash', 'corrupt', 'emergency']):
            return ErrorSeverity.CRITICAL
        
        if any(term in message for term in ['warning', 'caution', 'attention', 'notice']):
            return ErrorSeverity.WARNING
        
        if any(term in message for term in ['info', 'information', 'notification', 'note']):
            return ErrorSeverity.INFO
        
        # Check exception inheritance hierarchy
        for cls in exception.__class__.__mro__:
            cls_name = cls.__name__
            
            if cls_name.endswith('Critical') or cls_name.endswith('CriticalError'):
                return ErrorSeverity.CRITICAL
                
            if cls_name.endswith('Error') or cls_name.endswith('Exception'):
                return ErrorSeverity.ERROR
                
            if cls_name.endswith('Warning'):
                return ErrorSeverity.WARNING
                
            if cls_name.endswith('Info') or cls_name.endswith('Information'):
                return ErrorSeverity.INFO
        
        # Default to ERROR for unknown exceptions
        return ErrorSeverity.ERROR
    
    def _anonymize_report_data(self, data: Dict[str, Any]) -> None:
        """
        Anonymize sensitive data in a report.
        
        Args:
            data: The report data to anonymize
        """
        # Anonymize user-specific data
        if 'error_message' in data:
            # Anonymize file paths
            data['error_message'] = re.sub(
                r'[A-Za-z]:\\Users\\[^\\]+',
                'C:\\Users\\USER',
                data['error_message']
            )
            
            data['error_message'] = re.sub(
                r'/home/[^/]+',
                '/home/user',
                data['error_message']
            )
            
            # Anonymize email addresses
            data['error_message'] = re.sub(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                'user@example.com',
                data['error_message']
            )
        
        # Anonymize context data
        if 'context' in data and isinstance(data['context'], dict):
            # Remove potentially sensitive keys
            for key in ['user', 'email', 'password', 'token', 'api_key']:
                if key in data['context']:
                    data['context'][key] = '[REDACTED]'
        
        # Anonymize system info
        if 'system_info' in data and isinstance(data['system_info'], dict):
            # Anonymize hostname
            if 'platform' in data['system_info']:
                data['system_info']['platform'] = re.sub(
                    r'-[a-zA-Z0-9_-]+-',
                    '-hostname-',
                    data['system_info']['platform']
                )


# Create a singleton instance of the enhanced error handler
_enhanced_instance: Optional[EnhancedErrorHandler] = None

def get_enhanced_error_handler(parent=None) -> EnhancedErrorHandler:
    """
    Get the singleton instance of the enhanced error handler.
    
    Args:
        parent: The parent QObject
    
    Returns:
        The enhanced error handler instance
    """
    global _enhanced_instance
    if _enhanced_instance is None:
        _enhanced_instance = EnhancedErrorHandler(parent)
    return _enhanced_instance
