from datetime import datetime

from app.models.combine_model import Combine
from app.repository.combine_repository import CombineRepository
from app.schemas.request.create_combine_request import CreateCombineRequest
from app.schemas.response.create_combine_response import CreateCombineResponse


class CombineService:
    repo = CombineRepository()

    @staticmethod
    async def create_combine(create_combine_request: CreateCombineRequest) -> CreateCombineResponse:
        combine = Combine(
            university=create_combine_request.university,
            department=create_combine_request.department,
            question_count=create_combine_request.question_count,
            interview_date=create_combine_request.interview_date,
            persona=create_combine_request.persona,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        new_combine_id = await CombineService.repo.insert(combine)

        return CreateCombineResponse(
            combineId=new_combine_id,
        )
