#!/usr/bin/env python3
"""
Abstract synchronization framework for digital asset inventory systems.
Provides common patterns for extracting, processing, and syncing data from various sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import time
from datetime import datetime

# Type definitions
T = TypeVar('T')

class SyncStatus(Enum):
    """Sync operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"

@dataclass
class SyncResult:
    """Result of a sync operation."""
    status: SyncStatus
    items_synced: int
    items_failed: int
    duration_ms: int
    error_log: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ExtractedItem:
    """Raw item extracted from source."""
    id: str
    raw_data: Dict[str, Any]
    source_metadata: Dict[str, Any]
    extraction_method: str

class CategoryConfidence:
    """Categorization result with confidence scoring."""
    def __init__(self, category: str, subcategory: str, confidence: float, method: str):
        self.category = category
        self.subcategory = subcategory  
        self.confidence = confidence
        self.method = method

# Abstract Protocols
class SourceExtractor(Protocol):
    """Protocol for source data extraction."""
    
    def authenticate(self) -> bool:
        """Authenticate with the source."""
        ...
    
    def extract_items(self) -> List[ExtractedItem]:
        """Extract raw items from source."""
        ...
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the source."""
        ...

class ItemProcessor(Protocol):
    """Protocol for item processing and enhancement."""
    
    def process_item(self, item: ExtractedItem) -> Dict[str, Any]:
        """Process and enhance raw item data."""
        ...
    
    def categorize_item(self, item: Dict[str, Any]) -> CategoryConfidence:
        """Categorize item with confidence scoring."""
        ...

class DataSyncer(Protocol):
    """Protocol for syncing processed data to storage."""
    
    def sync_items(self, items: List[Dict[str, Any]]) -> SyncResult:
        """Sync processed items to storage."""
        ...

# Abstract Base Classes
class BaseSyncEngine(ABC):
    """
    Abstract base class for synchronization engines.
    Implements the Template Method pattern for sync operations.
    """
    
    def __init__(self, extractor: SourceExtractor, processor: ItemProcessor, syncer: DataSyncer):
        self.extractor = extractor
        self.processor = processor
        self.syncer = syncer
        self.sync_start_time = None
        
    def sync(self) -> SyncResult:
        """
        Main sync method using Template Method pattern.
        Orchestrates the full sync workflow.
        """
        self.sync_start_time = time.time()
        
        try:
            # Step 1: Pre-sync setup
            self._pre_sync_setup()
            
            # Step 2: Authentication
            if not self._authenticate():
                return SyncResult(
                    status=SyncStatus.FAILED,
                    items_synced=0,
                    items_failed=0,
                    duration_ms=self._get_duration_ms(),
                    error_log="Authentication failed"
                )
            
            # Step 3: Extract items
            raw_items = self._extract_items()
            if not raw_items:
                return SyncResult(
                    status=SyncStatus.SUCCESS,
                    items_synced=0,
                    items_failed=0,
                    duration_ms=self._get_duration_ms(),
                    metadata={"message": "No items to sync"}
                )
            
            # Step 4: Process items
            processed_items = self._process_items(raw_items)
            
            # Step 5: Sync to storage
            sync_result = self._sync_items(processed_items)
            
            # Step 6: Post-sync cleanup
            self._post_sync_cleanup()
            
            return sync_result
            
        except Exception as e:
            return SyncResult(
                status=SyncStatus.FAILED,
                items_synced=0,
                items_failed=0,
                duration_ms=self._get_duration_ms(),
                error_log=str(e)
            )
    
    def _authenticate(self) -> bool:
        """Authenticate with the source."""
        return self.extractor.authenticate()
    
    def _extract_items(self) -> List[ExtractedItem]:
        """Extract items from source."""
        return self.extractor.extract_items()
    
    def _process_items(self, raw_items: List[ExtractedItem]) -> List[Dict[str, Any]]:
        """Process extracted items."""
        processed = []
        for item in raw_items:
            try:
                processed_item = self.processor.process_item(item)
                # Add categorization
                categorization = self.processor.categorize_item(processed_item)
                processed_item.update({
                    'category': categorization.category,
                    'subcategory': categorization.subcategory,
                    'categorization_confidence': categorization.confidence,
                    'categorization_method': categorization.method
                })
                processed.append(processed_item)
            except Exception as e:
                # Log but continue processing other items
                print(f"Error processing item {item.id}: {e}")
                continue
        return processed
    
    def _sync_items(self, items: List[Dict[str, Any]]) -> SyncResult:
        """Sync processed items."""
        return self.syncer.sync_items(items)
    
    def _get_duration_ms(self) -> int:
        """Get sync duration in milliseconds."""
        if self.sync_start_time:
            return int((time.time() - self.sync_start_time) * 1000)
        return 0
    
    # Template method hooks (can be overridden)
    def _pre_sync_setup(self):
        """Pre-sync setup hook."""
        pass
    
    def _post_sync_cleanup(self):
        """Post-sync cleanup hook."""
        pass

class BaseItemProcessor(ABC):
    """
    Abstract base class for item processors.
    Provides common processing patterns.
    """
    
    @abstractmethod
    def process_item(self, item: ExtractedItem) -> Dict[str, Any]:
        """Process a single item."""
        pass
    
    def categorize_item(self, item: Dict[str, Any]) -> CategoryConfidence:
        """Default categorization with confidence scoring."""
        return self._categorize_with_patterns(item)
    
    def _categorize_with_patterns(self, item: Dict[str, Any]) -> CategoryConfidence:
        """Categorize using pattern matching."""
        name = item.get('name', '').lower()
        
        # Pattern matching with confidence scoring
        category_scores = {
            'ebook': self._score_ebook_patterns(name),
            'game': self._score_game_patterns(name),
            'software': self._score_software_patterns(name),
            'audio': self._score_audio_patterns(name),
            'video': self._score_video_patterns(name)
        }
        
        # Find best match
        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category]
        
        subcategory = self._determine_subcategory(best_category, name)
        method = f"pattern_matching_confidence_{confidence:.2f}"
        
        return CategoryConfidence(best_category, subcategory, confidence, method)
    
    def _score_ebook_patterns(self, name: str) -> float:
        """Score ebook patterns."""
        patterns = ['book', 'guide', 'manual', 'tutorial', 'handbook']
        return sum(0.3 for pattern in patterns if pattern in name)
    
    def _score_game_patterns(self, name: str) -> float:
        """Score game patterns."""
        patterns = ['game', 'adventure', 'strategy', 'rpg', 'simulation']
        return sum(0.3 for pattern in patterns if pattern in name)
    
    def _score_software_patterns(self, name: str) -> float:
        """Score software patterns."""
        patterns = ['software', 'tool', 'utility', 'app', 'suite']
        return sum(0.3 for pattern in patterns if pattern in name)
    
    def _score_audio_patterns(self, name: str) -> float:
        """Score audio patterns.""" 
        patterns = ['soundtrack', 'music', 'audio', 'mp3', 'album']
        return sum(0.3 for pattern in patterns if pattern in name)
    
    def _score_video_patterns(self, name: str) -> float:
        """Score video patterns."""
        patterns = ['video', 'movie', 'film', 'documentary', 'tutorial']
        return sum(0.3 for pattern in patterns if pattern in name)
    
    def _determine_subcategory(self, category: str, name: str) -> str:
        """Determine subcategory based on category and name."""
        if category == 'ebook':
            if 'programming' in name or 'coding' in name:
                return 'programming'
            elif 'security' in name or 'hacking' in name:
                return 'security'
            else:
                return 'general'
        elif category == 'game':
            if 'strategy' in name:
                return 'strategy'
            elif 'rpg' in name or 'role' in name:
                return 'rpg'
            else:
                return 'general'
        else:
            return 'general'

class PluggableSync(BaseSyncEngine):
    """
    Concrete sync engine with pluggable components.
    Allows mixing and matching different extractors, processors, and syncers.
    """
    pass

# Factory for creating sync engines
class SyncEngineFactory:
    """Factory for creating configured sync engines."""
    
    @staticmethod
    def create_humble_bundle_sync(database, auth) -> PluggableSync:
        """Create sync engine for Humble Bundle."""
        from .humble_bundle_extractor import HumbleBundleExtractor
        from .enhanced_processor import EnhancedProcessor
        from .database_syncer import DatabaseSyncer
        
        extractor = HumbleBundleExtractor(auth)
        processor = EnhancedProcessor()
        syncer = DatabaseSyncer(database)
        
        return PluggableSync(extractor, processor, syncer)
    
    @staticmethod
    def create_steam_sync(database, api_key) -> PluggableSync:
        """Create sync engine for Steam (future implementation)."""
        # Future: SteamExtractor, SteamProcessor, DatabaseSyncer
        raise NotImplementedError("Steam sync not yet implemented")