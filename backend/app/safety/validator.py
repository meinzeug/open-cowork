import re
import os
from typing import Tuple
from app.models.actions import Action
from app.safety.policy import BLOCKED_SHELL_PATTERNS, MEDIUM_SHELL_PATTERNS, SENSITIVE_UI_KEYWORDS, BLOCKED_DOMAINS

class SafetyValidator:
    @staticmethod
    def validate_action(action: Action, risk_policy: str = "confirm_high") -> Tuple[str, bool, str]:
        """
        Validates an action against safety policies.
        Returns:
            (risk_level, requires_confirmation, reason)
        """
        action_type = action.type
        params = action.params
        
        # Default safety status
        risk_level = "low"
        requires_confirmation = False
        reason = "Aktion als sicher eingestuft."

        # Explicit user confirmation tool
        if action_type == "ask_user_confirmation":
            return "high", True, f"Agent bittet explizit um Freigabe: {params.get('message', 'Keine Nachricht hinterlassen')}"

        # 1. Shell command safety
        if action_type == "shell_command":
            cmd = params.get("command", "")
            
            # Check critical blocks
            for pattern in BLOCKED_SHELL_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    return "high", True, f"Kritischer Systembefehl blockiert durch Regel: {pattern}"
            
            # Check medium blocks
            for pattern in MEDIUM_SHELL_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    risk_level = "high"
                    reason = f"Sensibler Befehl erkannt: {cmd} (Muster: {pattern})"
                    break
            
            # Enforce policy checks
            if risk_level == "high":
                if risk_policy in ["confirm_high", "confirm_medium_high"]:
                    requires_confirmation = True
                return risk_level, requires_confirmation, reason

        # 2. File systems safety
        if action_type in ["read_file", "write_file", "list_files"]:
            path = params.get("path", "")
            
            # Normalize path
            # If path points to system folders like /etc, /var/run, ~/.ssh etc.
            resolved_path = os.path.abspath(path)
            
            sensitive_paths = [
                "/etc/", "/var/", "/usr/", "/boot/", "/opt/", "/sys/", "/proc/", "/dev/", 
                "/home/dennis/.ssh", "/root/.ssh", ".env", ".git"
            ]
            
            for sens in sensitive_paths:
                if sens in resolved_path:
                    risk_level = "medium"
                    reason = f"Zugriff auf sensibles Systemverzeichnis: {path}"
                    
                    if risk_policy == "confirm_medium_high":
                        requires_confirmation = True
                    break
                    
            if action_type == "write_file" and risk_level == "medium":
                risk_level = "high"
                requires_confirmation = True
                reason = f"Schreibzugriff auf sensibles Systemverzeichnis blockiert/bestätigungspflichtig: {path}"
                
            return risk_level, requires_confirmation, reason

        # 3. Interactive Web & Text typing
        if action_type == "type_text":
            text = params.get("text", "")
            # Check if typing credit card or similar
            if re.search(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", text):
                return "high", True, "Eingabe von Kreditkartennummern erfordert immer eine Bestätigung."
            
            # Check if typing passwords
            for word in SENSITIVE_UI_KEYWORDS:
                if word in text.lower():
                    risk_level = "medium"
                    reason = f"Sensibles Wort '{word}' in Eingabetext erkannt."
                    if risk_policy == "confirm_medium_high":
                        requires_confirmation = True
                    break

        # 4. Opening potentially critical websites or apps
        if action_type == "open_app":
            app_name = params.get("text", "")
            if any(term in app_name.lower() for term in ["rm", "dd", "mkfs", "gparted"]):
                return "high", True, f"Ausführen einer potenziell destruktiven App blockiert: {app_name}"
            
            # Firefox opening sensitive links
            if "firefox" in app_name.lower():
                for dom in BLOCKED_DOMAINS:
                    if re.search(dom, app_name, re.IGNORECASE):
                        return "high", True, f"Zugriff auf blockierte/zahlungspflichtige Domain verweigert: {app_name}"

        return risk_level, requires_confirmation, reason
