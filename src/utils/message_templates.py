from typing import Optional
from datetime import datetime

class MessageTemplates:
    """Centralized message templates for bot communications"""
    
    @staticmethod
    def welcome_message() -> str:
        return (
            "Welcome to the Happy Hour Duty Bot! 🎉\n\n"
            "To get started, please tell me your full name.\n"
            "This will be used to identify you in the rotation schedule."
        )
    
    @staticmethod
    def registration_submitted(name: str) -> str:
        return (
            f"Thank you, {name}! ✅\n\n"
            "Your registration has been submitted for admin approval.\n"
            "You'll be notified once an admin reviews your request."
        )
    
    @staticmethod
    def already_registered(name: str, status: str) -> str:
        if status == "approved":
            return (
                f"👋 Hello {name}!\n\n"
                "You're already registered and approved for Happy Hour Duty.\n"
                "You'll receive notifications when it's your turn."
            )
        elif status == "pending":
            return (
                f"Hello {name}!\n\n"
                "Your registration is pending admin approval.\n"
                "You'll be notified once an admin reviews your request."
            )
        else:
            return "Your account is currently inactive. Please contact an admin."
    
    @staticmethod
    def duty_notification(name: str, meeting_date: str) -> str:
        return (
            f"🔔 **Happy Hour Duty Reminder**\n\n"
            f"Hello {name}!\n\n"
            f"You're scheduled for Happy Hour Duty for the meeting on:\n"
            f"📅 **{meeting_date}**\n\n"
            f"Please confirm whether you can fulfill this responsibility."
        )
    
    @staticmethod
    def duty_confirmed(name: str, meeting_date: str) -> str:
        return (
            f"✅ **Confirmed!**\n\n"
            f"Thank you {name}!\n\n"
            f"You're all set for Happy Hour Duty on {meeting_date}.\n"
            f"See you at the meeting! ☕️🍪"
        )
    
    @staticmethod
    def duty_declined(name: str) -> str:
        return (
            f"Understood, {name}.\n\n"
            "I'll assign this duty to the next person in the rotation.\n"
            "You'll remain in your regular position for next week's assignment."
        )
    
    @staticmethod
    def escalation_alert(meeting_date: str) -> str:
        return (
            "⚠️ **ESCALATION ALERT**\n\n"
            f"No one has confirmed Happy Hour Duty for the meeting on {meeting_date}.\n\n"
            "The entire rotation list has been exhausted.\n"
            "Manual intervention required."
        )
    
    @staticmethod
    def admin_approval_request(name: str, telegram_id: int) -> str:
        return (
            "🔔 **New User Registration**\n\n"
            f"**Name:** {name}\n"
            f"**Telegram ID:** {telegram_id}\n"
            f"**Status:** Pending Approval\n\n"
            "Please review and approve or reject this registration."
        )
    
    @staticmethod
    def approval_notification() -> str:
        return (
            "🎉 **Great news!**\n\n"
            "Your registration has been approved!\n"
            "You've been added to the Happy Hour Duty list.\n\n"
            "You'll receive a notification when it's your turn to bring refreshments."
        )
    
    @staticmethod
    def rejection_notification() -> str:
        return (
            "Unfortunately, your registration has been rejected.\n\n"
            "If you believe this is an error, please contact an administrator."
        )
    
    @staticmethod
    def timeout_warning(hours_remaining: int) -> str:
        return (
            f"⏰ **Reminder**\n\n"
            f"You have {hours_remaining} hours remaining to respond to your happy hour duty assignment.\n"
            f"Please confirm or decline soon."
        )
    
    @staticmethod
    def format_participant_list(participants: list) -> str:
        if not participants:
            return "No participants found."
        
        text = "**Participant List:**\n\n"
        for i, p in enumerate(participants, 1):
            text += f"{i}. {p.full_name} (ID: {p.telegram_id}) - Status: {p.status}\n"
        return text
    
    @staticmethod
    def format_rotation_status(current_assigned: Optional[str], next_person: Optional[str], meeting_date: Optional[str]) -> str:
        text = "**📊 Rotation Status**\n\n"
        
        if current_assigned:
            text += f"**Currently Assigned:** {current_assigned}\n"
        else:
            text += "**Currently Assigned:** None\n"
        
        if meeting_date:
            text += f"**Meeting Date:** {meeting_date}\n"
        else:
            text += "**Meeting Date:** Not set\n"
        
        if next_person:
            text += f"**Next in Line:** {next_person}\n"
        else:
            text += "**Next in Line:** Rotation list empty\n"
        
        return text