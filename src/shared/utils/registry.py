from typing import Dict, Optional


class Registry[T]:

    _store: Dict[str, T]  = {}

    @classmethod
    def get(cls, key: str) -> Optional[T]:
        return cls._store.get(key)
    
    @classmethod
    def set(cls, key: str, value: T) -> None:
        cls._store[key] = value


