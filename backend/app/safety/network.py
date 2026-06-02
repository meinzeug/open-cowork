import re
import threading
from urllib.parse import urlparse
from typing import Dict, List, Tuple

from app.safety.policy import BLOCKED_DOMAINS

# Regex to extract full http(s) URLs from arbitrary text (e.g. shell commands).
_URL_PATTERN = re.compile(r"https?://[^\s'\"<>|]+", re.IGNORECASE)

# Network related shell tools that can cause outbound traffic / data exfiltration.
_NETWORK_TOOLS = ("curl", "wget", "nc", "ncat", "ssh", "scp", "rsync", "ftp", "telnet")

# Bare host/domain extraction for tools invoked like `curl example.com/path`.
_HOST_PATTERN = re.compile(
    r"\b((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,})\b",
    re.IGNORECASE,
)


def _normalize_domain(value: str) -> str:
    """Reduce an arbitrary URL or host string to a bare lowercase hostname."""
    value = (value or "").strip().lower()
    if not value:
        return ""
    if "://" not in value:
        value = f"https://{value}"
    netloc = urlparse(value).netloc or ""
    # Strip credentials and port.
    netloc = netloc.split("@")[-1].split(":")[0]
    return netloc.strip()


class NetworkPolicy:
    """
    Central, thread-safe outbound-network access policy for the agent.

    Two enforcement modes are supported:
      - ``blocklist``: every domain is allowed except those that match a
        blocklist entry (default, backwards compatible behaviour).
      - ``allowlist``: only domains that match an allowlist entry are allowed;
        every other outbound destination is rejected. This makes silent data
        exfiltration through the agent effectively impossible.

    Entries are matched as case-insensitive substrings against the destination
    hostname, which keeps the existing ``BLOCKED_DOMAINS`` semantics intact.
    """

    VALID_MODES = ("blocklist", "allowlist")

    def __init__(self, mode: str = "blocklist") -> None:
        self._lock = threading.RLock()
        self._mode = mode if mode in self.VALID_MODES else "blocklist"
        # Seed the blocklist from the static policy so existing behaviour holds.
        self._blocklist: List[str] = [p for p in BLOCKED_DOMAINS]
        self._allowlist: List[str] = []

    # -- configuration ----------------------------------------------------
    @property
    def mode(self) -> str:
        with self._lock:
            return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in self.VALID_MODES:
            raise ValueError(f"Ungültiger Netzwerkmodus: {mode}")
        with self._lock:
            self._mode = mode

    def _add(self, target: List[str], domain: str) -> None:
        domain = (domain or "").strip().lower()
        if domain and domain not in target:
            target.append(domain)

    def add_blocked(self, domain: str) -> None:
        with self._lock:
            self._add(self._blocklist, domain)

    def remove_blocked(self, domain: str) -> None:
        domain = (domain or "").strip().lower()
        with self._lock:
            self._blocklist = [d for d in self._blocklist if d != domain]

    def add_allowed(self, domain: str) -> None:
        with self._lock:
            self._add(self._allowlist, domain)

    def remove_allowed(self, domain: str) -> None:
        domain = (domain or "").strip().lower()
        with self._lock:
            self._allowlist = [d for d in self._allowlist if d != domain]

    def update(
        self,
        mode: str = None,
        blocklist: List[str] = None,
        allowlist: List[str] = None,
    ) -> None:
        with self._lock:
            if mode is not None:
                self.set_mode(mode)
            if blocklist is not None:
                self._blocklist = []
                for d in blocklist:
                    self._add(self._blocklist, d)
            if allowlist is not None:
                self._allowlist = []
                for d in allowlist:
                    self._add(self._allowlist, d)

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            return {
                "mode": self._mode,
                "blocklist": list(self._blocklist),
                "allowlist": list(self._allowlist),
            }

    # -- evaluation -------------------------------------------------------
    def evaluate_domain(self, domain: str) -> Tuple[bool, str]:
        """
        Decide whether a single destination domain may be reached.

        Returns ``(allowed, reason)``.
        """
        host = _normalize_domain(domain)
        if not host:
            return True, "Keine Zieladresse erkannt."

        with self._lock:
            mode = self._mode
            blocklist = list(self._blocklist)
            allowlist = list(self._allowlist)

        if mode == "allowlist":
            for entry in allowlist:
                if entry and re.search(re.escape(entry), host, re.IGNORECASE):
                    return True, f"Domain '{host}' steht auf der Allowlist."
            return False, (
                f"Allowlist aktiv: Verbindung zu '{host}' nicht erlaubt. "
                "Ziel zuerst zur Allowlist hinzufügen."
            )

        # blocklist mode
        for entry in blocklist:
            if entry and re.search(entry, host, re.IGNORECASE):
                return False, f"Domain '{host}' ist durch die Blocklist gesperrt (Regel: {entry})."
        return True, f"Domain '{host}' ist nicht gesperrt."

    def evaluate_url(self, url: str) -> Tuple[bool, str]:
        return self.evaluate_domain(url)

    def evaluate_text(self, text: str) -> Tuple[bool, str]:
        """
        Inspect arbitrary text (e.g. a shell command) for outbound network
        destinations and evaluate each against the policy. Returns the first
        blocked destination, otherwise an allow decision.
        """
        text = text or ""
        candidates: List[str] = []

        # 1. Explicit http(s) URLs anywhere in the text.
        candidates.extend(_URL_PATTERN.findall(text))

        # 2. Bare hosts following known network tools (e.g. `curl example.com`).
        lowered = text.lower()
        if any(tool in lowered for tool in _NETWORK_TOOLS):
            for match in _HOST_PATTERN.findall(text):
                candidates.append(match)

        seen = set()
        for candidate in candidates:
            host = _normalize_domain(candidate)
            if not host or host in seen:
                continue
            seen.add(host)
            allowed, reason = self.evaluate_domain(host)
            if not allowed:
                return False, reason

        return True, "Keine gesperrten Netzwerkziele erkannt."


# Singleton instance shared across the backend.
try:
    from app.config import settings as _settings
    network_policy = NetworkPolicy(mode=_settings.NETWORK_POLICY_MODE)
except Exception:  # pragma: no cover - defensive fallback if settings unavailable
    network_policy = NetworkPolicy()
