"""Entity detection service using OpenAI GPT models."""

import time
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

import openai
from openai import OpenAI

from ..config import Config
from ..models import Entity, EntityType, EntityDetectionResult, Note, Relationship, RelationshipType


class EntityDetectionService:
    """Service for detecting entities and relationships from Obsidian notes."""

    def __init__(self):
        """Initialize the entity detection service."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL_ENTITY_DETECTION

        # Load entity types from the entity_types.txt file
        self.entity_types = self._load_entity_types()

    def _load_entity_types(self) -> List[str]:
        """Load entity types from the entity_types.txt file."""
        entity_types_file = Path(
            __file__).parent.parent.parent.parent / "entity_types.txt"
        if entity_types_file.exists():
            with open(entity_types_file, 'r') as f:
                content = f.read()
                # Extract entity types from the file
                types = re.findall(r'"([^"]+)"', content)
                return [t for t in types if t and not t.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'))]
        return []

    def detect_entities(self, note: Note) -> EntityDetectionResult:
        """Detect entities and relationships from a note."""
        start_time = time.time()

        try:
            # Prepare the prompt for entity detection
            prompt = self._create_entity_detection_prompt(note)

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing text and identifying entities and relationships. Extract entities and their relationships from the given text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )

            # Parse the response
            entities, relationships = self._parse_entity_detection_response(
                response.choices[0].message.content, note
            )

            processing_time = time.time() - start_time

            return EntityDetectionResult(
                note_id=note.id,
                entities=entities,
                relationships=relationships,
                confidence=0.8,  # Base confidence
                processing_time=processing_time
            )

        except Exception as e:
            # Fallback to basic entity detection
            entities, relationships = self._fallback_entity_detection(note)
            processing_time = time.time() - start_time

            return EntityDetectionResult(
                note_id=note.id,
                entities=entities,
                relationships=relationships,
                confidence=0.5,  # Lower confidence for fallback
                processing_time=processing_time
            )

    def _create_entity_detection_prompt(self, note: Note) -> str:
        """Create the prompt for entity detection."""
        return f"""
Analyze the following Obsidian note and extract entities and relationships.

Note Title: {note.title}
Note Content:
{note.content[:2000]}  # Limit content length

Please identify:
1. Entities (people, organizations, concepts, locations, books, projects, meetings, topics)
2. Relationships between entities

Return your response in the following JSON format:
{{
    "entities": [
        {{
            "name": "Entity Name",
            "entity_type": "Person|Organization|Concept|Location|Book|Project|Meeting|Topic",
            "confidence": 0.9,
            "aliases": ["alias1", "alias2"],
            "properties": {{"key": "value"}}
        }}
    ],
    "relationships": [
        {{
            "source_entity": "Source Entity Name",
            "target_entity": "Target Entity Name", 
            "relationship_type": "MENTIONS|RELATED_TO|WORKS_FOR|AUTHOR_OF|PART_OF|SIMILAR_TO|COLLABORATES_WITH|LOCATED_IN|DISCUSSES|ATTENDS",
            "confidence": 0.8,
            "properties": {{"key": "value"}}
        }}
    ]
}}

Available entity types: {', '.join(self.entity_types[:20])}  # Show first 20 types
Available relationship types: MENTIONS, RELATED_TO, WORKS_FOR, AUTHOR_OF, PART_OF, SIMILAR_TO, COLLABORATES_WITH, LOCATED_IN, DISCUSSES, ATTENDS

Focus on extracting meaningful entities and relationships that would be useful for knowledge graph construction.
"""

    def _parse_entity_detection_response(self, response: str, note: Note) -> Tuple[List[Entity], List[Relationship]]:
        """Parse the OpenAI response to extract entities and relationships."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return [], []

            data = json.loads(json_match.group())

            # Parse entities
            entities = []
            for entity_data in data.get("entities", []):
                try:
                    entity = Entity(
                        name=entity_data["name"],
                        entity_type=EntityType(entity_data["entity_type"]),
                        confidence=entity_data.get("confidence", 0.8),
                        aliases=set(entity_data.get("aliases", [])),
                        properties=entity_data.get("properties", {})
                    )
                    entities.append(entity)
                except (KeyError, ValueError) as e:
                    continue

            # Parse relationships
            relationships = []
            for rel_data in data.get("relationships", []):
                try:
                    # Find source and target entities
                    source_entity = next(
                        (e for e in entities if e.name == rel_data["source_entity"]), None)
                    target_entity = next(
                        (e for e in entities if e.name == rel_data["target_entity"]), None)

                    if source_entity and target_entity:
                        relationship = Relationship(
                            source_entity_id=source_entity.id,
                            target_entity_id=target_entity.id,
                            relationship_type=RelationshipType(
                                rel_data["relationship_type"]),
                            confidence=rel_data.get("confidence", 0.7),
                            properties=rel_data.get("properties", {})
                        )
                        relationships.append(relationship)
                except (KeyError, ValueError) as e:
                    continue

            return entities, relationships

        except (json.JSONDecodeError, KeyError) as e:
            return [], []

    def _fallback_entity_detection(self, note: Note) -> Tuple[List[Entity], List[Relationship]]:
        """Fallback entity detection using basic text analysis."""
        entities = []
        relationships = []

        # Basic entity detection patterns
        content = note.content.lower()

        # Detect people (capitalized words that might be names)
        people_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        people = re.findall(people_pattern, note.content)
        for person in people[:5]:  # Limit to 5 people
            entity = Entity(
                name=person,
                entity_type=EntityType.PERSON,
                confidence=0.6,
                aliases=set()
            )
            entities.append(entity)

        # Detect organizations (common org patterns)
        org_patterns = [
            r'\b[A-Z][a-z]+ (Inc|Corp|LLC|Ltd|Company|Organization|Foundation)\b',
            r'\b[A-Z][A-Z]+\b'  # Acronyms
        ]
        for pattern in org_patterns:
            orgs = re.findall(pattern, note.content)
            for org in orgs[:3]:  # Limit to 3 organizations
                entity = Entity(
                    name=org,
                    entity_type=EntityType.ORGANIZATION,
                    confidence=0.6,
                    aliases=set()
                )
                entities.append(entity)

        # Detect concepts (words in quotes or italics)
        concept_patterns = [
            r'"([^"]+)"',
            r'\*([^*]+)\*',
            r'`([^`]+)`'
        ]
        for pattern in concept_patterns:
            concepts = re.findall(pattern, note.content)
            for concept in concepts[:5]:  # Limit to 5 concepts
                entity = Entity(
                    name=concept,
                    entity_type=EntityType.CONCEPT,
                    confidence=0.5,
                    aliases=set()
                )
                entities.append(entity)

        return entities, relationships

    def batch_detect_entities(self, notes: List[Note]) -> List[EntityDetectionResult]:
        """Detect entities from multiple notes in batches."""
        results = []

        for i in range(0, len(notes), Config.ENTITY_DETECTION_BATCH_SIZE):
            batch = notes[i:i + Config.ENTITY_DETECTION_BATCH_SIZE]

            for note in batch:
                result = self.detect_entities(note)
                results.append(result)

        return results


# Import time at the top to avoid circular imports
