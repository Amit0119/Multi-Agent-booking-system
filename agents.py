from dotenv import load_dotenv
load_dotenv() 

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
import datetime

# Initialize the Groq model
llm = ChatGroq(model="llama-3.3-70b-versatile")

def triage_node(state):
    """
    Triage Agent: Handles general conversation and routes to booking if needed.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful receptionist. If the user asks a general question, answer it normally. If the user wants to book, schedule, or make an appointment, politely tell them that you are transferring them to the Booking Specialist."),
        MessagesPlaceholder(variable_name="messages")
    ])
    chain = prompt | llm
    response = chain.invoke(state)
    return {"messages": [response]}

def booking_node(state):
    """
    Booking Agent: Has access to database tools and notification webhooks.
    """
    # Import necessary tools
    from tools import check_availability, reserve_slot, send_booking_notification
    
    tools = [check_availability, reserve_slot, send_booking_notification]
    llm_with_tools = llm.bind_tools(tools)
    
    # Fetch the current date to resolve relative terms like "tomorrow"
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Strict validation, negotiation, and notification logic
    sys_msg = SystemMessage(
        content=f"You are a GigaCorp Booking Specialist. Today's current date is {current_date}. "
                "Follow these rules strictly: "
                "1. If a user asks for relative dates like 'tomorrow', convert them to YYYY-MM-DD format based on today's date before passing to tools. "
                "2. ALWAYS check availability first using the check_availability tool. "
                "3. If a slot is taken or tool execution fails, DO NOT fail silently. Negotiate alternative available slots with the user. "
                "4. Once a time is agreed upon and you have their email, use the reserve_slot tool. "
                "5. IMMEDIATELY after a successful reservation, execute the send_booking_notification tool to trigger a confirmation."
    )
    
    # Append system instructions to the conversation history
    messages = [sys_msg] + state["messages"]
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}