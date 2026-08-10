"""
base_agent.py — Abstract Agent base class.
Phase 0 stub.

Design note (from master/agentic-criteria sections):
    Each debater satisfies the 4 agentic AI criteria:
    1. Autonomy         — runs turn-by-turn without human prompting each line
    2. Tool use         — calls resolution, MCTS, retrieval tools mid-reasoning
    3. Loop + state     — maintains KB across turns, reacts to prior context
    4. Autonomous tool invocation — agent itself decides when to call which tool

    Per-turn loop (both agents):
        1. retrieve_relevant_fact()   → fact retrieval (Unit II semantic search)
        2. generate_claim()           → LLM phrasing only
        3. TELL(kb, claim)            → update KB
        4. check_contradiction()      → resolution (Unit IV)
        5. [if needed] select_best_rebuttal()  → MCTS (Unit III)
"""
from abc import ABC, abstractmethod
from core.knowledge_base import KnowledgeBase


class BaseAgent(ABC):
    """
    Abstract debater agent — percept/decide/act loop.
    Phase 0: skeleton only — implement per-model subclasses in Phases 5+.
    """

    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role                    # "proposer" or "opponent"
        self.kb = KnowledgeBase(agent_id)

    @abstractmethod
    def perceive(self, opponent_last_claim: str | None) -> dict:
        """Receive the opponent's last claim as a percept."""
        raise NotImplementedError

    @abstractmethod
    def decide(self, percept: dict) -> dict:
        """
        Run the per-turn agentic loop — call tools (retrieve, generate, TELL, check, rebuttal).
        Returns a structured action dict with the chosen claim and supporting metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def act(self, action: dict) -> str:
        """Execute the decided action; return the claim text to emit."""
        raise NotImplementedError
