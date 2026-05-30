"""Typed exception hierarchy for the Screenshot Tool backend.

Milestone A: introduce a central place for domain-specific exceptions
without changing runtime behaviour yet. Call sites will be migrated
incrementally in later milestones.
"""

from __future__ import annotations

from typing import Optional


class ScreenshotToolError(Exception):
    """Base class for all application-level errors in the backend.

    Use this as the common ancestor for any error that should be
    treated as a *domain* failure rather than a low-level programming
    error.

    This exception should never be raised directly. Instead, use one of
    the specific subclasses (CaptureError, QualityCheckError, etc.).

    Attributes:
        None (subclasses define their own attributes)

    Usage:
        # Don't do this
        raise ScreenshotToolError("Something failed")

        # Instead, catch all domain errors
        try:
            capture_screenshot(url)
        except ScreenshotToolError as e:
            # Handles ALL domain errors
            logger.error(f"Domain error: {e}")
    """


class CaptureError(ScreenshotToolError):
    """Generic error raised when a screenshot capture fails.

    This is the base class for all capture-related errors. Use specific
    subclasses (CaptureTimeoutError, CaptureCancelledError) when applicable.

    Attributes:
        url (str): The URL that failed to capture
        reason (str): Human-readable failure reason

    HTTP Mapping:
        500 Internal Server Error

    Example:
        raise CaptureError(
            url="https://example.com",
            reason="Browser process crashed"
        )
    """

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        message = f"Capture failed for {url}: {reason}"
        super().__init__(message)


class CaptureTimeoutError(CaptureError):
    """Raised when a capture operation exceeds its timeout budget.

    Use this when a screenshot capture takes longer than the configured
    timeout period. This helps distinguish timeout errors from other
    capture failures.

    Attributes:
        url (str): The URL that timed out
        timeout_s (float): Timeout value in seconds
        reason (str): Auto-generated message "timed out after {timeout_s}s"

    HTTP Mapping:
        500 Internal Server Error (or 504 Gateway Timeout)

    Example:
        raise CaptureTimeoutError(
            url="https://slow-site.com",
            timeout_s=30.0
        )
    """

    def __init__(self, url: str, timeout_s: float) -> None:
        self.timeout_s = timeout_s
        super().__init__(url, f"timed out after {timeout_s}s")


class CaptureCancelledError(CaptureError):
    """Raised when a capture is cancelled via the cancellation API.

    Use this when a user or client explicitly cancels an ongoing screenshot
    capture operation through the cancellation endpoint.

    Attributes:
        url (str): The URL being captured when cancelled
        request_id (Optional[str]): Request ID if available for tracking
        reason (str): Auto-generated with request_id context

    HTTP Mapping:
        499 Client Closed Request

    Example:
        raise CaptureCancelledError(
            url="https://example.com",
            request_id="req_abc123"
        )
    """

    def __init__(self, url: str, request_id: Optional[str] = None) -> None:
        self.request_id = request_id
        suffix = f" (request_id={request_id})" if request_id is not None else ""
        super().__init__(url, f"cancelled by client{suffix}")


class QualityCheckError(ScreenshotToolError):
    """Raised when the quality-check phase for a screenshot fails.

    Use this when screenshot quality validation detects issues such as:
    - Resolution below threshold
    - Image corruption or artifacts
    - File size validation failures
    - Quality score below acceptable level

    Attributes:
        None (can be extended with quality metrics in future)

    HTTP Mapping:
        500 Internal Server Error

    Example:
        raise QualityCheckError("Screenshot resolution too low: 100x100px")
    """


class SSRFAttemptError(ScreenshotToolError):
    """Raised when URL validation detects a potential SSRF attempt.

    This allows the validation layer to communicate intent without
    relying on string matching. Route handlers can translate this into
    the appropriate HTTP error response (e.g. 400/403) while keeping
    the core logic focused on domain rules.

    Use this when detecting security-sensitive URL patterns:
    - Private IP addresses (127.0.0.1, 10.x.x.x, 192.168.x.x)
    - Localhost variants (localhost, ::1)
    - File protocol (file://)
    - Other dangerous URL patterns

    Attributes:
        None (message contains the reason)

    HTTP Mapping:
        403 Forbidden (or 400 Bad Request)

    Example:
        raise SSRFAttemptError("Attempted to access private IP: 127.0.0.1")
    """


class URLValidationError(ScreenshotToolError):
    """Raised when URL validation fails for non-security reasons.

    Use this for general URL validation failures like:
    - Invalid URL format
    - Missing protocol
    - URL too long
    - Empty URL list
    - Too many URLs in batch

    Attributes:
        url (Optional[str]): The URL that failed validation (if single URL)
        reason (str): Human-readable validation failure reason

    HTTP Mapping:
        400 Bad Request

    Example:
        raise URLValidationError(
            url="ftp://example.com",
            reason="Invalid protocol (must be http:// or https://)"
        )
    """

    def __init__(self, reason: str, url: Optional[str] = None) -> None:
        self.reason = reason
        self.url = url
        if url:
            message = f"URL validation failed for {url}: {reason}"
        else:
            message = f"URL validation failed: {reason}"
        super().__init__(message)


class PathValidationError(ScreenshotToolError):
    """Raised when file path validation fails.

    Use this for path validation failures like:
    - Path outside allowed directory
    - File not found
    - Invalid path format
    - Path traversal attempt

    Attributes:
        path (str): The path that failed validation
        reason (str): Human-readable validation failure reason

    HTTP Mapping:
        400 Bad Request

    Example:
        raise PathValidationError(
            path="/etc/passwd",
            reason="Path outside screenshots directory"
        )
    """

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        message = f"Path validation failed for {path}: {reason}"
        super().__init__(message)


class BrowserError(ScreenshotToolError):
    """Raised when browser automation fails.

    Use this for browser-related failures like:
    - Cannot connect to Chrome CDP
    - No browser contexts found
    - No tabs found
    - Failed to create tab
    - Browser process crashed

    Attributes:
        reason (str): Human-readable failure reason
        browser_type (Optional[str]): Browser type (chrome, firefox, etc.)

    HTTP Mapping:
        500 Internal Server Error

    Example:
        raise BrowserError(
            reason="Cannot connect to Chrome via CDP",
            browser_type="chrome"
        )
    """

    def __init__(self, reason: str, browser_type: Optional[str] = None) -> None:
        self.reason = reason
        self.browser_type = browser_type
        if browser_type:
            message = f"Browser error ({browser_type}): {reason}"
        else:
            message = f"Browser error: {reason}"
        super().__init__(message)


class AuthenticationError(ScreenshotToolError):
    """Raised when authentication or session management fails.

    Use this for authentication-related failures like:
    - Timeout waiting for login
    - Failed to save auth state
    - Session expired
    - Invalid credentials

    Attributes:
        reason (str): Human-readable failure reason
        url (Optional[str]): URL where authentication failed

    HTTP Mapping:
        500 Internal Server Error

    Example:
        raise AuthenticationError(
            reason="Timeout waiting for login",
            url="https://example.com/login"
        )
    """

    def __init__(self, reason: str, url: Optional[str] = None) -> None:
        self.reason = reason
        self.url = url
        if url:
            message = f"Authentication failed for {url}: {reason}"
        else:
            message = f"Authentication failed: {reason}"
        super().__init__(message)


class DocumentGenerationError(ScreenshotToolError):
    """Raised when document generation fails.

    Use this for document generation failures like:
    - No valid screenshot files found
    - Document template error
    - File write error
    - Invalid document format

    Attributes:
        reason (str): Human-readable failure reason
        file_count (Optional[int]): Number of files involved

    HTTP Mapping:
        500 Internal Server Error

    Example:
        raise DocumentGenerationError(
            reason="No valid screenshot files found",
            file_count=0
        )
    """

    def __init__(self, reason: str, file_count: Optional[int] = None) -> None:
        self.reason = reason
        self.file_count = file_count
        if file_count is not None:
            message = f"Document generation failed ({file_count} files): {reason}"
        else:
            message = f"Document generation failed: {reason}"
        super().__init__(message)


__all__ = [
    "ScreenshotToolError",
    "CaptureError",
    "CaptureTimeoutError",
    "CaptureCancelledError",
    "QualityCheckError",
    "SSRFAttemptError",
    "URLValidationError",
    "PathValidationError",
    "BrowserError",
    "AuthenticationError",
    "DocumentGenerationError",
]

