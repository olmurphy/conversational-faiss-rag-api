import json
from logging import Logger
from typing import TypeVar, Generic, Type
from attr import dataclass
from jsonschema import ValidationError as JsonSchemaValidationError, validate
from pydantic import ValidationError as PydanticValidationError, BaseModel

from infrastructure.config_manager.errors import ConfigValidationError, ModelValidationError

T = TypeVar('T', bound=BaseModel)


@dataclass
class ConfigManagerParams:
    config_path: str
    config_schema_path: str
    model: Type[T]
    logger: Logger


class ConfigManager(Generic[T]):

    def __init__(self, params: ConfigManagerParams):
        self.config_path = params.config_path
        self.config_schema_path = params.config_schema_path
        self.model = params.model
        self.logger = params.logger
        self.config: T = None
        self.schema = None

        self.load_config_file()
        self.config = self.convert_to_pydantic()

    def load_config_file(self):
        try:
            with open(self.config_path, "r", encoding="UTF-8") as file:
                self.config = json.load(file)
        except FileNotFoundError as err:
            self.logger.error(
                f'Error on loading the config from {self.config_path}')
            raise err

    def convert_to_pydantic(self) -> T:
        """Convert the loaded config dictionary to a Pydantic model."""
        try:
            return self.model(**self.config)
        except PydanticValidationError as err:
            self.logger.error(
                f'Pydantic model validation error: {err.errors()}')
            raise ModelValidationError(err.errors())

    def get_configuration(self) -> T:
        return self.config
