import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.models.database_schema import UserStatus

logger = logging.getLogger(__name__)

class ApprovalHandler:
    """Handles admin approval of new users"""
    
    async def handle_approval(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, approved: bool):
        """Process approval or rejection of a user"""
        query = update.callback_query
        db_manager = context.bot_data.get('db_manager')
        admin_user = update.effective_user
        
        # Get participant
        participant = db_manager.get_participant(user_id)
        
        if not participant:
            await query.answer("User not found in database.")
            return
        
        if participant.status != UserStatus.PENDING.value:
            await query.answer(f"User already processed (status: {participant.status})")
            return
        
        if approved:
            # Approve user
            participant.status = UserStatus.APPROVED.value
            if db_manager.update_participant(participant):
                # Update the admin's message
                await query.edit_message_text(
                    f"✅ **Approved**\n\n"
                    f"**Name:** {participant.full_name}\n"
                    f"**Telegram ID:** {participant.telegram_id}\n"
                    f"**Approved by:** {admin_user.full_name} ({admin_user.id})\n\n"
                    f"User has been added to the rotation list.",
                    parse_mode='Markdown'
                )
                
                # Notify the user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "🎉 **Great news!**\n\n"
                            "Your registration has been approved!\n"
                            "You've been added to the refreshment rotation list.\n\n"
                            "You'll receive a notification when it's your turn to bring refreshments."
                        ),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to notify approved user {user_id}: {e}")
                
                logger.info(f"User {participant.full_name} approved by admin {admin_user.id}")
            else:
                await query.answer("Failed to update user status.")
        else:
            # Reject user
            participant.status = UserStatus.INACTIVE.value
            if db_manager.update_participant(participant):
                # Update the admin's message
                await query.edit_message_text(
                    f"❌ **Rejected**\n\n"
                    f"**Name:** {participant.full_name}\n"
                    f"**Telegram ID:** {participant.telegram_id}\n"
                    f"**Rejected by:** {admin_user.full_name} ({admin_user.id})\n\n"
                    f"User registration has been rejected.",
                    parse_mode='Markdown'
                )
                
                # Notify the user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "Unfortunately, your registration has been rejected.\n\n"
                            "If you believe this is an error, please contact an administrator."
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to notify rejected user {user_id}: {e}")
                
                logger.info(f"User {participant.full_name} rejected by admin {admin_user.id}")
            else:
                await query.answer("Failed to update user status.")
        
        await query.answer()