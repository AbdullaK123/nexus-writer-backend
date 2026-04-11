from src.infrastructure.di.containers import ApplicationContainer, wire_circular_deps

container = ApplicationContainer()

__all__ = ["container", "ApplicationContainer", "wire_circular_deps"]
