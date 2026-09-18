import re
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TransformedQuery:
    original_query: str
    rewritten_query: str
    expansion_queries: List[str]
    extracted_keywords: List[str]


class QueryTransformer:
    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    def _rule_based_rewrite(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Rule-based coreference resolution when LLM is unavailable or for fast latency.
        """
        if not conversation_history or len(conversation_history) == 0:
            return query

        # Find the most recent user turn or assistant topic
        last_turns = conversation_history[-2:]
        context_keywords = []
        for turn in reversed(last_turns):
            content = turn.get("content", "")
            # Extract key nouns / capitalized terms / technical phrases
            words = re.findall(r'\b[A-Z][a-zA-Z0-9_\-]+\b|\b[a-z]{4,}\b', content)
            context_keywords.extend([w for w in words if w.lower() not in {"what", "how", "why", "when", "where", "can", "you", "tell", "explain", "about", "this", "that"}])

        pronouns = [" it ", " its ", " they ", " them ", " their ", " this ", " that ", " these ", " those "]
        query_padded = f" {query} "
        has_pronoun = any(p in query_padded.lower() for p in pronouns)

        if has_pronoun and context_keywords:
            top_kw = " ".join(dict.fromkeys(context_keywords[:3]))
            return f"{query} (concerning: {top_kw})"

        return query

    def _rule_based_expand(self, query: str) -> List[str]:
        """
        Expands queries using domain synonym maps and technical research phrasing.
        """
        expansions = [query]
        clean_q = query.lower()

        # RAG / Hallucination expansions
        if "hallucination" in clean_q or "grounding" in clean_q:
            expansions.append(f"factual consistency and hallucination mitigation in {query}")
            expansions.append("faithfulness attribution and citation verification")
        
        if "rag" in clean_q or "retrieval" in clean_q:
            expansions.append(f"retrieval augmented generation architectures {query}")
            expansions.append("dense vector retrieval and hybrid search methods")

        if "attention" in clean_q or "transformer" in clean_q:
            expansions.append(f"self-attention mechanism and transformer scaling {query}")

        if "compare" in clean_q or "difference" in clean_q:
            expansions.append(f"architectural comparison trade-offs benchmarks {query}")

        if len(expansions) == 1:
            # Add general technical expansion
            words = [w for w in re.findall(r'\w+', query) if len(w) > 3]
            if words:
                expansions.append(f"methodology and experimental results for {' '.join(words)}")

        return list(dict.fromkeys(expansions))[:4]

    def _extract_keywords(self, query: str) -> List[str]:
        tokens = re.findall(r'\b[A-Za-z0-9_\-]{3,}\b', query.lower())
        stopwords = {
            "what", "which", "where", "when", "how", "who", "whom", "this", "that", "these",
            "those", "with", "from", "into", "during", "including", "until", "against", "among",
            "throughout", "despite", "towards", "upon", "concerning", "about", "does", "have", "been"
        }
        return list(dict.fromkeys([t for t in tokens if t not in stopwords]))

    async def transform_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> TransformedQuery:
        # Check if LLM is provided and functional
        if self.llm_service:
            try:
                system_prompt = (
                    "You are a query transformation engine for an advanced academic RAG system.\n"
                    "Given a user query and conversation history, perform:\n"
                    "1. Conversational query rewriting (resolve all pronouns/references into a standalone query).\n"
                    "2. Generate 3 diverse expanded search queries for hybrid retrieval.\n"
                    "3. Extract key technical keywords.\n"
                    "Respond strictly in JSON format:\n"
                    "{\n"
                    '  "rewritten_query": "...",\n'
                    '  "expansion_queries": ["...", "...", "..."],\n'
                    '  "keywords": ["...", "..."]\n'
                    "}"
                )
                user_msg = f"User Query: {query}\n"
                if conversation_history:
                    user_msg += f"Recent Conversation: {json.dumps(conversation_history[-3:])}"

                llm_res = await self.llm_service.generate_text(
                    prompt=user_msg,
                    system_prompt=system_prompt,
                    temperature=0.0
                )
                
                # Parse json from response
                json_match = re.search(r'\{.*\}', llm_res, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return TransformedQuery(
                        original_query=query,
                        rewritten_query=data.get("rewritten_query", query),
                        expansion_queries=data.get("expansion_queries", [query]),
                        extracted_keywords=data.get("keywords", self._extract_keywords(query))
                    )
            except Exception as e:
                logger.warning(f"LLM query transformation fallback: {e}")

        # Rule-based fallback
        rewritten = self._rule_based_rewrite(query, conversation_history)
        expansions = self._rule_based_expand(rewritten)
        keywords = self._extract_keywords(rewritten)

        return TransformedQuery(
            original_query=query,
            rewritten_query=rewritten,
            expansion_queries=expansions,
            extracted_keywords=keywords
        )
