"""Claude API integration for the Howl AI Helper."""

from howl.config import get_api_key
from howl.ai.prompts import SYSTEM_PROMPT, build_hint_prompt, build_chat_prompt
from howl.ai.context import build_hint_context
from howl.engine.session import HuntSession
from howl.ui.theme import console


class AIHelper:
    """AI-powered hint and chat system using Anthropic Claude."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            api_key = get_api_key()
            if not api_key:
                return None
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                console.print("[red]Anthropic SDK not installed. Run: pip install anthropic[/red]")
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if AI helper is available (API key set)."""
        return get_api_key() is not None

    def get_static_hint(self, session: HuntSession, level: int) -> str | None:
        """Get a pre-written static hint from the target definition.

        Returns:
            Hint text if available, None otherwise.
        """
        stage = session.current_stage_obj
        if not stage:
            return None

        for hint in stage.hints:
            if hint.level == level:
                return hint.text

        return None

    def get_ai_hint(self, session: HuntSession, level: int, target_ip: str = "127.0.0.1", command_history: str | None = None) -> str | None:
        """Get an AI-generated hint using the Claude API.

        Returns:
            AI hint text, or None if unavailable.
        """
        client = self._get_client()
        if not client:
            return None

        context = build_hint_context(session, level, target_ip=target_ip)
        context["command_history"] = command_history
        user_message = build_hint_prompt(**context)

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except Exception as e:
            console.print(f"[red]AI Helper error: {e}[/red]")
            return None

    def get_hint(self, session: HuntSession, level: int = 1, target_ip: str = "127.0.0.1", command_history: str | None = None) -> tuple[str, str]:
        """Get a hint, preferring static then falling back to AI.

        Returns:
            Tuple of (hint_text, source) where source is 'static' or 'ai'.
        """
        # Try static hint first
        static = self.get_static_hint(session, level)
        if static:
            # Replace placeholder IPs in static hints with the real target IP
            static = static.replace("<target_ip>", target_ip).replace("<ip>", target_ip).replace("<target>", target_ip)
            return static, "static"

        # Fall back to AI
        if self.is_available():
            ai_hint = self.get_ai_hint(session, level, target_ip=target_ip, command_history=command_history)
            if ai_hint:
                return ai_hint, "ai"

        return "No hint available for this level. Try a different level or check the target briefing.", "none"

    def chat(self, session: HuntSession, question: str, target_ip: str = "127.0.0.1", command_history: str | None = None) -> str:
        """Free-form chat with the AI helper."""
        client = self._get_client()
        if not client:
            return "AI Helper is not available. Set your Anthropic API key with: howl config --set-api-key"

        stage = session.current_stage_obj
        target_ports = [
            {"name": svc.name, "port": svc.port, "protocol": svc.protocol}
            for svc in session.target.services
        ]
        user_message = build_chat_prompt(
            target_name=session.target.name,
            current_stage=stage.name if stage else "Unknown",
            stage_description=stage.description if stage else "",
            user_question=question,
            target_ip=target_ip,
            target_ports=target_ports,
            tools_suggested=stage.tools_suggested if stage else [],
            command_history=command_history,
        )

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except Exception as e:
            return f"AI Helper error: {e}"
