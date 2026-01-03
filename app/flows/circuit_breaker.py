"""
Circuit Breaker implementation for protecting against cascading failures.

Uses Redis for state storage to ensure consistency across multiple workers.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failures exceeded threshold, requests rejected immediately
- HALF_OPEN: Testing recovery, limited requests allowed

Usage:
    breaker = CircuitBreaker(name="gemini-api", redis=redis_client)
    
    if not  breaker.can_execute():
        raise CircuitOpenError("Circuit is OPEN")
    
    try:
        result =  call_api()
         breaker.record_success()
        return result
    except Exception as e:
         breaker.record_failure()
        raise
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from redis.asyncio import Redis
from loguru import logger
from app.core.redis import get_redis
from app.config.prefect import (
    CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS,
)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and rejecting requests"""
    def __init__(self, breaker_name: str, time_to_recovery: int):
        self.breaker_name = breaker_name
        self.time_to_recovery = time_to_recovery
        super().__init__(
            f"Circuit breaker '{breaker_name}' is OPEN. "
            f"Recovery in {time_to_recovery}s"
        )


@dataclass
class CircuitBreakerStatus:
    """Status information for API responses"""
    name: str
    state: CircuitState
    failure_count: int
    last_failure_at: Optional[datetime]
    time_to_recovery: Optional[int]  # seconds until half-open, if open
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "time_to_recovery": self.time_to_recovery,
        }


class CircuitBreaker:
    """
    Redis-backed circuit breaker for distributed systems.
    
    All state is stored in Redis to ensure consistency across workers.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout: int = CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        half_open_max_calls: int = CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        # Redis keys
        self._key_prefix = f"circuit_breaker:{name}"
        self._state_key = f"{self._key_prefix}:state"
        self._failures_key = f"{self._key_prefix}:failures"
        self._last_failure_key = f"{self._key_prefix}:last_failure"
        self._opened_at_key = f"{self._key_prefix}:opened_at"
        self._half_open_calls_key = f"{self._key_prefix}:half_open_calls"
    
    def _get_redis(self) -> Redis:
        """Get Redis connection"""
        redis = get_redis()
        return redis
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        redis = self._get_redis()
        state = redis.get(self._state_key)
        
        if state is None:
            return CircuitState.CLOSED
        
        state_str = state.decode() if isinstance(state, bytes) else state
        
        # Check if OPEN circuit should transition to HALF_OPEN
        if state_str == CircuitState.OPEN.value:
            opened_at =  redis.get(self._opened_at_key)
            if opened_at:
                opened_at_ts = float(opened_at.decode() if isinstance(opened_at, bytes) else opened_at)
                if datetime.utcnow().timestamp() - opened_at_ts >= self.recovery_timeout:
                    self._transition_to_half_open(redis)
                    return CircuitState.HALF_OPEN
        
        return CircuitState(state_str)
    
    def can_execute(self) -> bool:
        """Check if request should be allowed through"""
        state =  self.get_state()
        
        if state == CircuitState.CLOSED:
            return True
        
        if state == CircuitState.OPEN:
            return False
        
        # HALF_OPEN: Allow limited calls
        redis =  self._get_redis()
        calls =  redis.incr(self._half_open_calls_key)
        
        if calls <= self.half_open_max_calls:
            return True
        
        # Too many half-open calls, reject
        return False
    
    def record_success(self) -> None:
        """Record successful execution"""
        redis =  self._get_redis()
        state =  self.get_state()
        
        if state == CircuitState.HALF_OPEN:
            # Success in half-open: close the circuit
            self._transition_to_closed(redis)
            logger.info(f"Circuit breaker '{self.name}' CLOSED after successful recovery")
        elif state == CircuitState.CLOSED:
            # Reset failure count on success
             redis.set(self._failures_key, 0)
    
    def record_failure(self) -> None:
        """Record failed execution"""
        redis =  self._get_redis()
        state =  self.get_state()
        
        if state == CircuitState.HALF_OPEN:
            # Failure in half-open: back to open
            self._transition_to_open(redis)
            logger.warning(f"Circuit breaker '{self.name}' re-OPENED after half-open failure")
            return
        
        # Increment failure count
        failures =  redis.incr(self._failures_key)
        redis.set(self._last_failure_key, datetime.utcnow().timestamp())

        if failures >= self.failure_threshold:
            self._transition_to_open(redis)
            logger.warning(
                f"Circuit breaker '{self.name}' OPENED after {failures} failures. "
                f"Recovery in {self.recovery_timeout}s"
            )
    
    def _transition_to_open(self, redis: Redis) -> None:
        """Transition to OPEN state"""
        redis.set(self._state_key, CircuitState.OPEN.value)
        redis.set(self._opened_at_key, datetime.utcnow().timestamp())
        redis.delete(self._half_open_calls_key)
    
    def _transition_to_half_open(self, redis: Redis) -> None:
        """Transition to HALF_OPEN state"""
        redis.set(self._state_key, CircuitState.HALF_OPEN.value)
        redis.set(self._half_open_calls_key, 0)
    
    def _transition_to_closed(self, redis: Redis) -> None:
        """Transition to CLOSED state"""
        redis.set(self._state_key, CircuitState.CLOSED.value)
        redis.set(self._failures_key, 0)
        redis.delete(self._opened_at_key)
        redis.delete(self._half_open_calls_key)
        redis.delete(self._last_failure_key)
    
    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state"""
        redis =  self._get_redis()
        self._transition_to_closed(redis)
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
    
    def time_to_recovery(self) -> Optional[int]:
        """Get seconds until circuit transitions to half-open (if open)"""
        state =  self.get_state()
        
        if state != CircuitState.OPEN:
            return None
        
        redis =  self._get_redis()
        opened_at =  redis.get(self._opened_at_key)
        
        if not opened_at:
            return None
        
        opened_at_ts = float(opened_at.decode() if isinstance(opened_at, bytes) else opened_at)
        elapsed = datetime.utcnow().timestamp() - opened_at_ts
        remaining = max(0, self.recovery_timeout - int(elapsed))
        
        return remaining
    
    def get_status(self) -> CircuitBreakerStatus:
        """Get comprehensive status for monitoring"""
        redis =  self._get_redis()
        
        state =  self.get_state()
        
        failures =  redis.get(self._failures_key)
        failure_count = int(failures.decode() if failures else 0)
        
        last_failure =  redis.get(self._last_failure_key)
        last_failure_at = None
        if last_failure:
            last_failure_ts = float(last_failure.decode() if isinstance(last_failure, bytes) else last_failure)
            last_failure_at = datetime.fromtimestamp(last_failure_ts)
        
        ttr =  self.time_to_recovery()
        
        return CircuitBreakerStatus(
            name=self.name,
            state=state,
            failure_count=failure_count,
            last_failure_at=last_failure_at,
            time_to_recovery=ttr,
        )


# Shared circuit breakers for different services
gemini_breaker = CircuitBreaker(
    name="gemini-api",
    failure_threshold=5,
    recovery_timeout=30,
)

database_breaker = CircuitBreaker(
    name="postgres",
    failure_threshold=3,
    recovery_timeout=15,
)


def get_all_breaker_statuses() -> list[CircuitBreakerStatus]:
    """Get status of all circuit breakers"""
    return [
         gemini_breaker.get_status(),
         database_breaker.get_status(),
    ]


def reset_breaker_by_name(name: str) -> bool:
    """Reset a circuit breaker by name"""
    breakers = {
        "gemini-api": gemini_breaker,
        "postgres": database_breaker,
    }
    
    if name not in breakers:
        return False
    
    breakers[name].reset()
    return True
