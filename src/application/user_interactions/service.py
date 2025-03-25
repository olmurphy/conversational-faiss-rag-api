import asyncio
import uuid
from logging import Logger

from api.schemas.user_interactions_schema import UpdateInteractionInputSchema
from context import AppContext


class UserInteractionService:
    def __init__(
        self,
        app_context: AppContext,
    ):
        self.postgres_session = app_context.postgres_session
        self.logger: Logger = app_context.logger

    async def record_user_feedback(
        self, interaction_id: uuid.UUID, update_data: UpdateInteractionInputSchema
    ):
        asyncio.create_task(
            self.postgres_session.record_user_feedback(interaction_id, update_data)
        )
