from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from utils.response_utils import CivilResponse, CivilErrorResponse


class CivilAIQueryAPIView(APIView):
    """Public chat endpoint backed by the cluster-cache RAG pipeline."""
    permission_classes = [AllowAny]

    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query:
            return CivilErrorResponse(
                {"error": "Query is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lazy import keeps Django startup light (no model/index build on boot).
        from rag_engine.service import ask

        result = ask(query)

        return CivilResponse(
            {
                "combined_context": result["answer"],
                "answer": result["answer"],
                "sources": result.get("sources", []),
                "docs_used": result.get("sources", []),
                "cache_hit": result.get("cache_hit", False),
                "greeting": result.get("greeting", False),
                "off_topic": result.get("off_topic", False),
                "llm": result.get("llm", "none"),
                "llm_fallback": result.get("llm_fallback", False),
            },
            status=status.HTTP_200_OK,
            is_success="Response Generated.",
        )


class RagReloadAPIView(APIView):
    """Drop the cached pipeline so newly added docs/PDFs get re-indexed."""
    permission_classes = [AllowAny]

    def post(self, request):
        from rag_engine.service import reset

        reset()
        return CivilResponse(
            {"reloaded": True},
            status=status.HTTP_200_OK,
            is_success="RAG index will reload on next query.",
        )
