from dataclasses import dataclass

from langgraph.graph import MessagesState
from langgraph.managed import IsLastStep


@dataclass
class State(MessagesState):
    """
    Represents the complete state of the agent, extending InputState with additional attributes.
    This class can be used to store any information needed throughout the agent's lifecycle.
    """

    is_last_step: IsLastStep
