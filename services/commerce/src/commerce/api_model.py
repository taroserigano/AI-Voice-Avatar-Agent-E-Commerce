from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    """Base for API schemas. Response schemas list defaulted fields as required, since the
    server always sends them, so the generated TypeScript types don't mark them optional."""

    model_config = ConfigDict(json_schema_serialization_defaults_required=True)
