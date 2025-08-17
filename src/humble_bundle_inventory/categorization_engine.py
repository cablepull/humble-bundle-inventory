#!/usr/bin/env python3
"""
Advanced categorization engine for digital assets.
Provides confidence-based categorization with extensible rules and machine learning support.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import re
import json

class CategoryType(Enum):
    """Supported category types."""
    EBOOK = "ebook"
    GAME = "game"
    SOFTWARE = "software"
    AUDIO = "audio"
    VIDEO = "video"
    COMIC = "comic"
    BUNDLE = "bundle"
    SUBSCRIPTION_CONTENT = "subscription_content"
    UNKNOWN = "unknown"

@dataclass
class CategoryRule:
    """A categorization rule with patterns and weights."""
    name: str
    category: CategoryType
    subcategory: str
    patterns: List[str]
    weight: float
    field_weights: Dict[str, float]  # Weight by field (name, description, etc.)
    required_patterns: List[str] = None  # Must match all of these
    exclusion_patterns: List[str] = None  # Must not match any of these

@dataclass
class CategoryResult:
    """Result of categorization with confidence scoring."""
    category: CategoryType
    subcategory: str
    confidence: float
    method: str
    matched_rules: List[str]
    scores: Dict[str, float]

class CategoryMatcher(ABC):
    """Abstract base for category matching strategies."""
    
    @abstractmethod
    def match(self, item: Dict[str, Any]) -> Dict[CategoryType, float]:
        """Return category scores for an item."""
        pass

class PatternMatcher(CategoryMatcher):
    """Pattern-based category matcher."""
    
    def __init__(self, rules: List[CategoryRule]):
        self.rules = rules
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for rule in self.rules:
            rule._compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in rule.patterns]
            if rule.required_patterns:
                rule._compiled_required = [re.compile(pattern, re.IGNORECASE) for pattern in rule.required_patterns]
            if rule.exclusion_patterns:
                rule._compiled_exclusions = [re.compile(pattern, re.IGNORECASE) for pattern in rule.exclusion_patterns]
    
    def match(self, item: Dict[str, Any]) -> Dict[CategoryType, float]:
        """Match item against all rules and return scores."""
        scores = {cat: 0.0 for cat in CategoryType}
        
        for rule in self.rules:
            rule_score = self._score_rule(rule, item)
            scores[rule.category] += rule_score
        
        return scores
    
    def _score_rule(self, rule: CategoryRule, item: Dict[str, Any]) -> float:
        """Score a single rule against an item."""
        total_score = 0.0
        
        # Check required patterns first
        if rule.required_patterns:
            for pattern in rule._compiled_required:
                if not self._matches_in_item(pattern, item):
                    return 0.0  # Required pattern not found
        
        # Check exclusion patterns
        if rule.exclusion_patterns:
            for pattern in rule._compiled_exclusions:
                if self._matches_in_item(pattern, item):
                    return 0.0  # Exclusion pattern found
        
        # Score pattern matches
        for pattern in rule._compiled_patterns:
            for field, field_weight in rule.field_weights.items():
                if field in item and item[field]:
                    text = str(item[field]).lower()
                    if pattern.search(text):
                        total_score += rule.weight * field_weight
        
        return total_score
    
    def _matches_in_item(self, pattern: re.Pattern, item: Dict[str, Any]) -> bool:
        """Check if pattern matches anywhere in item."""
        searchable_fields = ['name', 'human_name', 'description', 'machine_name']
        for field in searchable_fields:
            if field in item and item[field]:
                if pattern.search(str(item[field]).lower()):
                    return True
        return False

class CategorizationEngine:
    """Main categorization engine with multiple strategies."""
    
    def __init__(self):
        self.matchers: List[CategoryMatcher] = []
        self.rules = self._load_default_rules()
        self.pattern_matcher = PatternMatcher(self.rules)
        self.matchers.append(self.pattern_matcher)
    
    def categorize(self, item: Dict[str, Any]) -> CategoryResult:
        """Categorize an item using all available strategies."""
        all_scores = {cat: 0.0 for cat in CategoryType}
        matched_rules = []
        methods = []
        
        # Run all matchers
        for matcher in self.matchers:
            scores = matcher.match(item)
            for cat, score in scores.items():
                all_scores[cat] += score
            methods.append(type(matcher).__name__)
        
        # Find best category
        best_category = max(all_scores, key=all_scores.get)
        confidence = min(all_scores[best_category], 1.0)
        
        # Determine subcategory
        subcategory = self._determine_subcategory(best_category, item)
        
        return CategoryResult(
            category=best_category,
            subcategory=subcategory,
            confidence=confidence,
            method='+'.join(methods),
            matched_rules=matched_rules,
            scores=all_scores
        )
    
    def _determine_subcategory(self, category: CategoryType, item: Dict[str, Any]) -> str:
        """Determine subcategory based on category and item details."""
        name = str(item.get('name', '') or item.get('human_name', '')).lower()
        
        if category == CategoryType.EBOOK:
            if any(keyword in name for keyword in ['programming', 'coding', 'development']):
                return 'programming'
            elif any(keyword in name for keyword in ['security', 'hacking', 'pentesting']):
                return 'security'
            elif any(keyword in name for keyword in ['cooking', 'recipe', 'kitchen']):
                return 'cooking'
            elif any(keyword in name for keyword in ['gardening', 'garden', 'plant']):
                return 'gardening'
            elif any(keyword in name for keyword in ['art', 'design', 'creative']):
                return 'arts'
            elif any(keyword in name for keyword in ['survival', 'outdoor', 'wilderness']):
                return 'survival'
            else:
                return 'general'
        
        elif category == CategoryType.GAME:
            if any(keyword in name for keyword in ['strategy', 'rts', 'turn-based']):
                return 'strategy'
            elif any(keyword in name for keyword in ['rpg', 'role playing', 'adventure']):
                return 'rpg'
            elif any(keyword in name for keyword in ['simulation', 'simulator', 'sim']):
                return 'simulation'
            elif any(keyword in name for keyword in ['puzzle', 'brain', 'logic']):
                return 'puzzle'
            elif any(keyword in name for keyword in ['action', 'shooter', 'fps']):
                return 'action'
            else:
                return 'general'
        
        elif category == CategoryType.SUBSCRIPTION_CONTENT:
            if 'coupon' in name:
                return 'coupon'
            elif 'choice' in name:
                return 'humble_choice'
            else:
                return 'general'
        
        else:
            return 'general'
    
    def _load_default_rules(self) -> List[CategoryRule]:
        """Load default categorization rules."""
        return [
            # Ebook rules
            CategoryRule(
                name="ebook_keywords",
                category=CategoryType.EBOOK,
                subcategory="general",
                patterns=[r'\bbook\b', r'\bguide\b', r'\bmanual\b', r'\btutorial\b', r'\bhandbook\b'],
                weight=1.0,
                field_weights={'name': 0.8, 'human_name': 0.8, 'description': 0.3, 'machine_name': 0.5}
            ),
            CategoryRule(
                name="ebook_programming",
                category=CategoryType.EBOOK,
                subcategory="programming",
                patterns=[r'\bprogramming\b', r'\bcoding\b', r'\bdevelopment\b', r'\bpython\b', r'\bjava\b', r'\bjavascript\b'],
                weight=1.2,
                field_weights={'name': 0.9, 'human_name': 0.9, 'description': 0.4}
            ),
            CategoryRule(
                name="ebook_security",
                category=CategoryType.EBOOK,
                subcategory="security",
                patterns=[r'\bsecurity\b', r'\bhacking\b', r'\bpentesting\b', r'\bcyber\b', r'\bmalware\b'],
                weight=1.2,
                field_weights={'name': 0.9, 'human_name': 0.9, 'description': 0.4}
            ),
            
            # Game rules
            CategoryRule(
                name="game_keywords",
                category=CategoryType.GAME,
                subcategory="general",
                patterns=[r'\bgame\b', r'\badventure\b', r'\bquest\b', r'\blegend\b'],
                weight=1.0,
                field_weights={'name': 0.8, 'human_name': 0.8, 'description': 0.3}
            ),
            CategoryRule(
                name="game_strategy",
                category=CategoryType.GAME,
                subcategory="strategy",
                patterns=[r'\bstrategy\b', r'\brts\b', r'\bturn.based\b', r'\bcivilization\b', r'\bwar\b'],
                weight=1.1,
                field_weights={'name': 0.9, 'human_name': 0.9, 'description': 0.4}
            ),
            
            # Software rules
            CategoryRule(
                name="software_keywords",
                category=CategoryType.SOFTWARE,
                subcategory="general",
                patterns=[r'\bsoftware\b', r'\btool\b', r'\butility\b', r'\bapp\b', r'\bsuite\b', r'\bstudio\b'],
                weight=1.0,
                field_weights={'name': 0.8, 'human_name': 0.8, 'description': 0.3}
            ),
            
            # Audio rules
            CategoryRule(
                name="audio_keywords",
                category=CategoryType.AUDIO,
                subcategory="general",
                patterns=[r'\bsoundtrack\b', r'\bmusic\b', r'\baudio\b', r'\bmp3\b', r'\balbum\b'],
                weight=1.0,
                field_weights={'name': 0.8, 'human_name': 0.8, 'description': 0.3}
            ),
            
            # Subscription content rules
            CategoryRule(
                name="subscription_coupons",
                category=CategoryType.SUBSCRIPTION_CONTENT,
                subcategory="coupon",
                patterns=[r'\bcoupon\b', r'\bdiscount\b', r'\%\s*off\b'],
                weight=2.0,  # High weight for high confidence
                field_weights={'name': 1.0, 'human_name': 1.0, 'machine_name': 0.8}
            ),
            CategoryRule(
                name="subscription_choice",
                category=CategoryType.SUBSCRIPTION_CONTENT,
                subcategory="humble_choice",
                patterns=[r'\bchoice\b', r'\bsubscription\b'],
                weight=1.8,
                field_weights={'name': 1.0, 'human_name': 1.0, 'machine_name': 0.8}
            ),
        ]
    
    def add_matcher(self, matcher: CategoryMatcher):
        """Add a custom matcher to the engine."""
        self.matchers.append(matcher)
    
    def add_rule(self, rule: CategoryRule):
        """Add a custom rule to the pattern matcher."""
        self.rules.append(rule)
        # Recreate pattern matcher with new rules
        self.pattern_matcher = PatternMatcher(self.rules)
        # Replace in matchers list
        for i, matcher in enumerate(self.matchers):
            if isinstance(matcher, PatternMatcher):
                self.matchers[i] = self.pattern_matcher
                break

# Factory for creating categorization engines
class CategorizationEngineFactory:
    """Factory for creating configured categorization engines."""
    
    @staticmethod
    def create_humble_bundle_engine() -> CategorizationEngine:
        """Create engine optimized for Humble Bundle content."""
        engine = CategorizationEngine()
        
        # Add Humble Bundle specific rules
        humble_rules = [
            CategoryRule(
                name="humble_bundle_specific",
                category=CategoryType.BUNDLE,
                subcategory="humble_bundle",
                patterns=[r'\bbundle\b', r'\bhumble\b'],
                weight=1.5,
                field_weights={'name': 1.0, 'human_name': 1.0}
            )
        ]
        
        for rule in humble_rules:
            engine.add_rule(rule)
        
        return engine
    
    @staticmethod
    def create_generic_engine() -> CategorizationEngine:
        """Create a generic categorization engine."""
        return CategorizationEngine()