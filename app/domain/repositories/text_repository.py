from abc import ABC, abstractmethod
from app.domain.entities.text import Text as TextEntity

class TextRepository(ABC):
    """Abstract repository for text operations"""
    
    @abstractmethod
    def create(self, text: TextEntity) -> TextEntity:
        """Create a new text entry"""
        pass
    
    @abstractmethod
    def get_text(self, hash_value: str) -> TextEntity:
        """Get text by hash value"""
        pass
    
    @abstractmethod
    def health_check(self) -> dict:
        """Check repository health"""
        pass
