# base_service.py

import abc

class BaseService(abc.ABC):
    def __init__(self, name: str):
        self.name = name

    @abc.abstractmethod
    async def handle(self, data: dict):
        """Handle incoming data based on type."""
        pass
