import requests
import sqlite3
from langchain_core.tools import tool

@tool
def check_availability(date: str):
    """
    Checks the database for booked appointments on a specific date.
    Returns the times that are already booked.
    """
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM bookings WHERE date = ?", (date,))
    booked_slots = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not booked_slots:
        return "All slots are available."
    return f"The following slots are already booked: {booked_slots}"

@tool
def reserve_slot(date: str, time: str, email: str):
    """
    Books an appointment for the user at a specific date and time.
    Saves the user's email as well.
    """
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    
    # Insert the new booking into the database
    cursor.execute(
        "INSERT INTO bookings (date, time, email) VALUES (?, ?, ?)", 
        (date, time, email)
    )
    conn.commit()
    conn.close()
    
    return f"Successfully booked the appointment on {date} at {time} for {email}."

@tool
def send_booking_notification(email: str, details: str):
    """
    Simulates sending a booking confirmation email/WhatsApp message.
    Always call this tool IMMEDIATELY AFTER successfully reserving a slot.
    """
    # Webhook endpoint URL for mock notifications
    webhook_url = "https://webhook.site/00000000-0000-0000-0000-000000000000"
    
    payload = {
        "email": email,
        "message": f"Booking Confirmed: {details}"
    }
    
    try:
        # Send a POST request to the mock webhook
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            return "Notification sent successfully to the user."
        else:
            return f"Notification trigger failed with status: {response.status_code}"
    except Exception as e:
        return f"Failed to send notification: {str(e)}"