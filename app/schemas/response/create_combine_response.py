from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class CreateCombineResponse(BaseModel):
    combine_id: str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True