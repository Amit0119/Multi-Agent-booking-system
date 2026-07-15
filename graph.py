from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
import operator
import sqlite3
from langchain_core.messages import AnyMessage
from agents import triage_node, booking_node
from tools import check_availability, reserve_slot, send_booking_notification

# Define the state with a list of messages
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

def router(state):
    """
    Conditional router: Evaluates the user's last message to determine the appropriate agent.
    """
    last_msg = state["messages"][-1].content.lower()
    keywords = ["book", "appointment", "schedule", "reserve"]
    
    # Route to booking agent if a keyword is found
    if any(word in last_msg for word in keywords):
        return "booking_agent"
    return "triage_agent"

def route_tools(state):
    """
    Routes to the ToolNode if the Booking Agent requested a tool execution.
    """
    last_message = state["messages"][-1]
    
    # Check if the LLM invoked a tool call
    if last_message.tool_calls:
        return "tools"
    return END

# Initialize the state graph
workflow = StateGraph(AgentState)

# Add agent and tool nodes
workflow.add_node("triage_agent", triage_node)
workflow.add_node("booking_agent", booking_node)

# Include all three tools in the ToolNode for execution
workflow.add_node("tools", ToolNode([check_availability, reserve_slot, send_booking_notification])) 

# Set the entry point logic
workflow.set_conditional_entry_point(
    router, 
    {"triage_agent": "triage_agent", "booking_agent": "booking_agent"}
)

# Triage agent ends the turn directly
workflow.add_edge("triage_agent", END)

# Booking agent conditionally routes to tools or ends
workflow.add_conditional_edges("booking_agent", route_tools)

# Return control to the booking agent after executing tools
workflow.add_edge("tools", "booking_agent")

# Set up SQLite memory for state persistence
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# Compile the final graph
graph_app = workflow.compile(checkpointer=memory)