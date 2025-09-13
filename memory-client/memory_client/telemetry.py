import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def capture_client_event(event: str, client: Any, data: Optional[Dict[str, Any]] = None, extra: Optional[Dict[str, Any]] = None) -> None:
    """No-op telemetry stub; keeps API surface compatible without external side-effects."""
    logger.debug("telemetry event=%s data=%s extra=%s", event, data, extra)

