"""Screenshot-related Pydantic models.

Phase 2: these definitions were originally in backend.main and are
now the canonical source, with backend.main importing them from
backend.app.models.
"""

from typing import Any, List, Optional

import ipaddress
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator


# Keep this in sync with backend.main: MAX_BATCH_TIMEOUT_SECONDS
MAX_BATCH_TIMEOUT_SECONDS = 7200


def _validate_single_url(url: str) -> None:
	"""Shared URL validation logic to prevent SSRF and DoS.

	This mirrors backend.main._validate_single_url but lives here to
	avoid import-time circular dependencies between models and
	backend.main.
	"""

	blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
	blocked_schemes = {"file", "javascript", "data", "ftp"}

	private_networks = [
		ipaddress.ip_network("10.0.0.0/8"),
		ipaddress.ip_network("172.16.0.0/12"),
		ipaddress.ip_network("192.168.0.0/16"),
		ipaddress.ip_network("169.254.0.0/16"),  # link-local / AWS metadata
		ipaddress.ip_network("127.0.0.0/8"),
		ipaddress.ip_network("::1/128"),
		ipaddress.ip_network("fc00::/7"),  # unique local addresses
	]

	parsed = urlparse(url)

	# Check protocol
	if parsed.scheme not in ("http", "https"):
		raise ValueError(f"Invalid URL protocol (must be http or https): {url}")

	# Check length
	if len(url) > 2048:
		raise ValueError(f"URL too long (max 2048 characters): {url[:100]}...")

	# Block dangerous schemes explicitly (defence-in-depth)
	if parsed.scheme in blocked_schemes:
		raise ValueError(f"Blocked URL scheme: {parsed.scheme}")

	# Block localhost-style hosts to reduce SSRF risk
	hostname = (parsed.hostname or "").lower()
	if hostname in blocked_hosts:
		raise ValueError(f"Requests to host '{hostname}' are not allowed")

	# Block private/link-local IP literals (defence-in-depth)
	try:
		addr = ipaddress.ip_address(hostname)
	except ValueError:
		addr = None

	if addr and any(addr in net for net in private_networks):
		raise ValueError(f"Requests to private IP range are not allowed: {hostname}")


class CancelRequest(BaseModel):
    """Request model for cancelling screenshot captures.

    If request_id is omitted or null, all active requests are cancelled
    (backwards-compatible with existing behaviour).
    """

    request_id: Optional[str] = None


class URLRequest(BaseModel):
    urls: List[str]
    viewport_width: int = Field(default=1920, ge=800, le=7680, description="Viewport width (800-7680)")
    viewport_height: int = Field(default=1080, ge=600, le=4320, description="Viewport height (600-4320)")
    capture_mode: str = "viewport"  # "viewport", "fullpage", "segmented"
    use_stealth: bool = False
    use_real_browser: bool = False  # Use CDP to connect to existing Chrome (Active Tab Mode)
    headless: bool = False  # ✅ FIX: Default to headful (visible browser) - Real Browser Mode is always visible
    browser_engine: str = "playwright"  # "playwright" or "camoufox"
    base_url: str = ""  # Base URL for screenshot naming
    words_to_remove: str = ""  # Comma-separated words to remove from naming
    cookies: Optional[str] = ""  # JSON string of cookies for authentication
    local_storage: Optional[str] = ""  # JSON string of localStorage data for authentication
    # Advanced segmented settings
    segment_overlap: int = Field(default=20, ge=0, le=50, description="Percentage overlap (0-50%)")
    segment_scroll_delay: int = Field(default=1000, ge=0, le=10000, description="Scroll delay in ms (0-10000)")
    segment_max_segments: int = Field(default=50, ge=1, le=200, description="Max segments (1-200)")
    segment_skip_duplicates: bool = True  # Skip duplicate segments
    segment_smart_lazy_load: bool = True  # Wait for lazy-loaded content
    # ✅ NEW: Network event tracking
    track_network: bool = False  # Capture HTTP requests during page load
    # ✅ NEW: Per-request batch timeout (extended to support up to 2 hours)
    batch_timeout: Optional[int] = Field(
        default=90,
        ge=10,
        le=MAX_BATCH_TIMEOUT_SECONDS,
        description=f"Batch timeout in seconds (10-{MAX_BATCH_TIMEOUT_SECONDS}, up to 2 hours)",
    )
    # ✅ NEW: Max parallel URLs per text box (for Real Browser Mode)
    max_parallel_urls: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Max parallel URLs (1-10, Real Browser Mode only)",
    )
    # ✅ NEW: Auto expand dropdowns/collapsible sections
    auto_expand_dropdowns: bool = False  # Automatically expand all collapsed sections before screenshot
    # ✅ NEW: Click elements before screenshot
    click_elements: Optional[List[str]] = []  # List of text to search for and click before screenshot
    # ✅ NEW: Non-scrollable URLs list
    non_scrollable_urls: str = ""  # JSON string of URL patterns to treat as non-scrollable

    @validator("urls")
    def validate_urls(cls, v: List[str]) -> List[str]:
        """Validate URLs to prevent SSRF and DoS attacks."""

        if not v:
            raise ValueError("URL list cannot be empty")
        if len(v) > 500:
            raise ValueError("Too many URLs (max 500 per request)")

        for url in v:
            _validate_single_url(url)

        return v


class ScreenshotResult(BaseModel):
	url: str
	status: str  # "success", "failed", "pending"
	screenshot_path: Optional[str] = None
	screenshot_paths: Optional[List[str]] = None  # For segmented captures
	segment_count: Optional[int] = None  # Number of segments captured
	error: Optional[str] = None
	quality_score: Optional[float] = None
	quality_issues: Optional[List[str]] = None
	timestamp: str
	processing_time: Optional[float] = None  # Time taken to process this URL in seconds


class DocumentRequest(BaseModel):
	screenshot_paths: List[str]
	output_path: str
	title: str = "Screenshot Report"


__all__ = ["CancelRequest", "URLRequest", "ScreenshotResult", "DocumentRequest"]

