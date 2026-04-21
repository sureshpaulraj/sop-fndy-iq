"""
Grounding Validator Agent
Validates that generated responses are grounded in source chunks.
"""

import os
import logging
import json

logger = logging.getLogger(__name__)


async def validate_grounding(
    client, query: str, chunks: list[dict]
) -> dict:
    """
    Generate a response from the query + chunks, then validate grounding.

    Uses GPT-4.1 to:
    1. Generate an answer based on the retrieved chunks
    2. Self-evaluate whether the answer is grounded in the sources

    Args:
        client: AIProjectClient instance
        query: Original user query
        chunks: Retrieved SOP chunks

    Returns:
        dict with 'response', 'grounded' (bool), 'confidence' (float)
    """
    chunk_context = "\n\n---\n\n".join(
        [
            f"Source: {c['source']} (p.{c.get('page', '?')})\n{c['content']}"
            for c in chunks
        ]
    )

    system_prompt = """You are a grounding validator for SOP documents at Reyes Coca-Cola Bottling.

Your task:
1. Answer the user's question using ONLY the provided source chunks
2. Do NOT add information not present in the sources
3. If the sources don't contain enough information, say so
4. Rate your confidence that the answer is fully grounded (0.0 to 1.0)

Respond in JSON format:
{
    "response": "Your answer here...",
    "grounded": true/false,
    "confidence": 0.95,
    "reasoning": "Brief explanation of grounding assessment"
}"""

    user_prompt = f"""Question: {query}

Source Documents:
{chunk_context}

Generate a grounded answer and assess your confidence."""

    try:
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )

        openai_client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_ad_token_provider=token_provider,
            api_version="2025-01-01",
        )

        response = openai_client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-41"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        result = json.loads(response.choices[0].message.content)
        logger.info(
            f"[Grounding] Confidence: {result.get('confidence', 0)}, "
            f"Grounded: {result.get('grounded', False)}"
        )
        return result

    except Exception as e:
        logger.error(f"[Grounding] Validation failed: {e}")
        return {
            "response": "Unable to validate grounding.",
            "grounded": False,
            "confidence": 0.0,
        }
