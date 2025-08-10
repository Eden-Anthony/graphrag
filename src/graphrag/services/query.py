"""Query service for handling user queries and LLM integration."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from openai import OpenAI

from ..config import Config
from ..models import Note, QueryResult
from .knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling user queries and generating answers."""

    def __init__(self, knowledge_graph_service: KnowledgeGraphService):
        """Initialize the query service."""
        self.kg_service = knowledge_graph_service
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL_QUERY

    def query(self, question: str, context_size: int = None) -> QueryResult:
        """Process a user query and return an answer with context."""
        if context_size is None:
            context_size = Config.CONTEXT_WINDOW_SIZE

        try:
            # Step 1: Retrieve relevant context using hybrid retrieval
            context_notes = self._retrieve_context(question, context_size)

            # Step 2: Generate answer using GPT-5
            answer, citations = self._generate_answer(question, context_notes)

            # Step 3: Create query result
            return QueryResult(
                answer=answer,
                context_notes=context_notes,
                citations=citations,
                confidence=0.8,  # Base confidence
                query_time=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return QueryResult(
                answer=f"I encountered an error while processing your query: {str(e)}",
                context_notes=[],
                citations=[],
                confidence=0.0,
                query_time=datetime.utcnow()
            )

    def _retrieve_context(self, question: str, context_size: int) -> List[Note]:
        """Retrieve relevant context using hybrid retrieval."""
        try:
            # Use the hybrid cypher retriever to get relevant notes
            search_results = self.kg_service.search_notes(
                question, context_size)

            # Convert search results to Note objects
            context_notes = []
            for result in search_results:
                if hasattr(result, 'content'):
                    # Handle different result formats
                    if hasattr(result.content, 'get'):
                        # Result is a dict-like object
                        note_data = result.content
                    else:
                        # Result is a string, try to parse it
                        note_data = self._parse_result_content(result.content)

                    if note_data:
                        note = Note(
                            file_path=note_data.get('note_path', ''),
                            title=note_data.get('note_title', ''),
                            content=note_data.get('note_content', ''),
                            entities=[],
                            tags=set(),
                            links=set()
                        )
                        context_notes.append(note)

            return context_notes

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return []

    def _parse_result_content(self, content: str) -> Optional[Dict]:
        """Parse the content string from search results."""
        try:
            # Try to extract structured data from the content string
            import ast
            if content.startswith('{') and content.endswith('}'):
                return ast.literal_eval(content)
            return None
        except:
            return None

    def _generate_answer(self, question: str, context_notes: List[Note]) -> tuple[str, List[str]]:
        """Generate an answer using GPT-5 based on retrieved context."""
        try:
            # Prepare context for the LLM
            context_text = self._prepare_context_for_llm(context_notes)

            # Create the prompt for GPT-5
            prompt = self._create_answer_generation_prompt(
                question, context_text)

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert knowledge assistant that helps users find information from their personal knowledge base. 
                        You have access to notes from an Obsidian vault that have been processed into a knowledge graph.
                        
                        Your task is to:
                        1. Analyze the provided context notes
                        2. Answer the user's question based on the available information
                        3. Provide specific citations to the source notes
                        4. If information is missing, clearly state what you don't know
                        5. Synthesize information from multiple notes when relevant
                        
                        Always be helpful, accurate, and cite your sources."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            answer = response.choices[0].message.content

            # Extract citations from the answer
            citations = self._extract_citations(answer, context_notes)

            return answer, citations

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return f"I encountered an error while generating an answer: {str(e)}", []

    def _prepare_context_for_llm(self, context_notes: List[Note]) -> str:
        """Prepare context notes for the LLM prompt."""
        if not context_notes:
            return "No relevant context found."

        context_parts = []
        for i, note in enumerate(context_notes, 1):
            # Truncate content if too long
            content = note.content[:1000] if len(
                note.content) > 1000 else note.content

            context_part = f"""
Note {i}: {note.title}
File: {note.file_path}
Content: {content}
---
"""
            context_parts.append(context_part)

        return "\n".join(context_parts)

    def _create_answer_generation_prompt(self, question: str, context: str) -> str:
        """Create the prompt for answer generation."""
        return f"""
Question: {question}

Context Notes:
{context}

Please provide a comprehensive answer to the question based on the context notes above. 

Requirements:
1. Answer the question directly and completely
2. Use information from the context notes
3. Cite specific notes by their titles (e.g., "According to [Note Title]...")
4. If the context doesn't contain enough information, clearly state what you don't know
5. Synthesize information from multiple notes when relevant
6. Be concise but thorough

Answer:"""

    def _extract_citations(self, answer: str, context_notes: List[Note]) -> List[str]:
        """Extract citations from the generated answer."""
        citations = []

        # Look for note titles mentioned in the answer
        for note in context_notes:
            if note.title in answer:
                citations.append(f"{note.title} ({note.file_path})")

        # If no specific citations found, include all context notes
        if not citations and context_notes:
            citations = [
                f"{note.title} ({note.file_path})" for note in context_notes]

        return citations

    def chat_query(self, question: str, conversation_history: List[Dict] = None) -> QueryResult:
        """Handle a chat-style query with conversation history."""
        if conversation_history is None:
            conversation_history = []

        # For now, treat chat queries the same as regular queries
        # In the future, this could incorporate conversation context
        return self.query(question)

    def get_similar_entities(self, entity_name: str, limit: int = 5) -> List[Dict]:
        """Find entities similar to the given entity."""
        try:
            # Use the knowledge graph to find related entities
            related_notes = self.kg_service.get_related_notes(
                entity_name, limit)

            # Extract unique entities from related notes
            similar_entities = []
            seen_entities = set()

            for note_data in related_notes:
                note = note_data["note"]
                other_entities = note_data["other_entities"]

                for entity_name in other_entities:
                    if entity_name not in seen_entities:
                        similar_entities.append({
                            "entity_name": entity_name,
                            "source_note": note["title"],
                            "note_path": note["file_path"]
                        })
                        seen_entities.add(entity_name)

            return similar_entities[:limit]

        except Exception as e:
            logger.error(f"Failed to find similar entities: {e}")
            return []

    def get_topic_summary(self, topic: str, limit: int = 10) -> str:
        """Get a summary of information about a specific topic."""
        try:
            # Search for notes about the topic
            context_notes = self._retrieve_context(
                f"information about {topic}", limit)

            if not context_notes:
                return f"No information found about '{topic}' in your knowledge base."

            # Generate a summary using GPT-5
            summary_prompt = f"""
            Please provide a comprehensive summary of the information about '{topic}' based on the following notes:
            
            {self._prepare_context_for_llm(context_notes)}
            
            Provide a well-structured summary that covers the key points, relationships, and insights about this topic.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at summarizing information from multiple sources. Provide clear, organized summaries."
                    },
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Topic summary generation failed: {e}")
            return f"Failed to generate summary for '{topic}': {str(e)}"
