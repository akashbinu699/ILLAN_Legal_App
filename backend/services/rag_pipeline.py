"""LangGraph orchestration for RAG pipeline."""
from typing import TypedDict, Literal, Dict
from langgraph.graph import StateGraph, END
from backend.services.retrieval_service import retrieval_service
from backend.services.llm_service import llm_service

class RAGState(TypedDict):
    """State schema for RAG pipeline."""
    query: str
    retrieved_chunks: list
    draft_answer: str
    critique: str
    citations: list
    revision_count: int
    final_answer: str

class RAGPipeline:
    """LangGraph-based RAG pipeline with critique and revision."""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("retrieval", self._retrieval_node)
        workflow.add_node("drafting", self._drafting_node)
        workflow.add_node("critique", self._critique_node)
        workflow.add_node("revision", self._revision_node)
        
        # Define edges
        workflow.set_entry_point("retrieval")
        workflow.add_edge("retrieval", "drafting")
        workflow.add_edge("drafting", "critique")
        
        # Conditional edge: critique -> revision or END
        workflow.add_conditional_edges(
            "critique",
            self._should_revise,
            {
                "revise": "revision",
                "accept": END
            }
        )
        
        workflow.add_edge("revision", "retrieval")  # Loop back to retrieval
        
        return workflow.compile()
    
    def _retrieval_node(self, state: RAGState) -> RAGState:
        """Retrieval node: Execute hybrid search + re-ranking."""
        query = state["query"]
        
        # Retrieve relevant chunks
        chunks = retrieval_service.retrieve(
            query=query,
            n_results=10,
            top_k=3
        )
        
        return {
            **state,
            "retrieved_chunks": chunks
        }
    
    def _drafting_node(self, state: RAGState) -> RAGState:
        """Drafting node: LLM generates answer with citations."""
        query = state["query"]
        chunks = state["retrieved_chunks"]
        
        # Generate answer with citations
        result = llm_service.generate_with_citations(
            query=query,
            retrieved_chunks=chunks,
            require_citations=True
        )
        
        return {
            **state,
            "draft_answer": result["response"],
            "citations": result["citations"]
        }
    
    def _critique_node(self, state: RAGState) -> RAGState:
        """Critique node: Second LLM pass validates the answer."""
        query = state["query"]
        draft_answer = state["draft_answer"]
        citations = state["citations"]
        
        critique_prompt = f"""You are a legal expert reviewing an AI-generated answer.

Original Query: {query}

Draft Answer:
{draft_answer}

Citations Found: {len(citations)}

Please critique this answer. Check:
1. Does the answer cite sources properly? (Look for [Document ID, Page Number] format)
2. Are there any conflicts or contradictions between different sources?
3. Is the answer accurate and complete?
4. Are there any hallucinations (facts not in the sources)?

Provide your critique. If the answer is good, say "ACCEPT". If there are issues, say "REVISE" and explain why."""

        critique = llm_service.generate(critique_prompt, max_tokens=500, temperature=0.3)
        
        return {
            **state,
            "critique": critique
        }
    
    def _should_revise(self, state: RAGState) -> Literal["revise", "accept"]:
        """Determine if revision is needed based on critique."""
        critique = state["critique"].upper()
        revision_count = state.get("revision_count", 0)
        
        # Maximum 3 revisions to prevent infinite loops
        if revision_count >= 3:
            return "accept"
        
        # Check if critique says to revise
        if "REVISE" in critique or "ISSUE" in critique or "PROBLEM" in critique:
            return "revise"
        
        return "accept"
    
    def _revision_node(self, state: RAGState) -> RAGState:
        """Revision node: Update query and increment revision count."""
        query = state["query"]
        critique = state["critique"]
        revision_count = state.get("revision_count", 0)
        
        # Refine query based on critique
        revision_prompt = f"""Based on this critique, refine the search query to get better results:

Original Query: {query}
Critique: {critique}

Provide a refined, more specific query that addresses the issues mentioned."""

        refined_query = llm_service.generate(revision_prompt, max_tokens=200, temperature=0.5)
        
        return {
            **state,
            "query": refined_query.strip(),
            "revision_count": revision_count + 1,
            "retrieved_chunks": [],  # Clear for new retrieval
            "draft_answer": "",  # Clear for new draft
            "critique": ""  # Clear critique
        }
    
    def run(self, query: str) -> Dict:
        """Run the RAG pipeline."""
        initial_state: RAGState = {
            "query": query,
            "retrieved_chunks": [],
            "draft_answer": "",
            "critique": "",
            "citations": [],
            "revision_count": 0,
            "final_answer": ""
        }
        
        # Execute graph
        final_state = self.graph.invoke(initial_state)
        
        # Extract final answer
        final_answer = final_state.get("draft_answer", "")
        if not final_answer:
            final_answer = "Unable to generate answer after revisions."
        
        return {
            "answer": final_answer,
            "citations": final_state.get("citations", []),
            "revision_count": final_state.get("revision_count", 0),
            "retrieved_chunks": final_state.get("retrieved_chunks", [])
        }

# Global instance
rag_pipeline = RAGPipeline()

