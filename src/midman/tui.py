"""Textual dashboard for MidMan interactive mode."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, Label, Log, RichLog, Static, Tree

from midman.ai_backends import chat_with_backend, configure_backend, resolve_ai_backend, test_backend_connection
from midman.connectors import ConnectorStatus, collect_connectors
from midman.executor import ExecutionReport, MidmanExecutor
from midman.profiles import Profile, load_profile
from midman.storage import load_backend_config, save_backend_config, save_profile_mapping


def now_stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def summarize_connector_counts(connectors: list[ConnectorStatus]) -> dict[str, int]:
    return {
        "linux": sum(1 for item in connectors if item.target_type == "linux"),
        "network": sum(1 for item in connectors if item.target_type == "network"),
        "management": sum(1 for item in connectors if item.target_type == "management"),
    }


class InfoPanel(Static):
    """Bordered panel widget."""


class MidmanDashboardApp(App[None]):
    """Textual-powered infrastructure operations dashboard."""

    CSS = """
    Screen {
        background: #0b1020;
        color: #f5f7fa;
    }
    Header {
        background: #101827;
        color: #7dd3fc;
    }
    Footer {
        background: #101827;
        color: #93c5fd;
    }
    #main-grid {
        layout: vertical;
        height: 1fr;
        padding: 1;
    }
    #top-row {
        layout: horizontal;
        height: 1fr;
    }
    #left-column {
        width: 56%;
        margin-right: 1;
    }
    #right-column {
        width: 44%;
    }
    .panel {
        border: round #4b5563;
        background: #0f172a;
        padding: 1;
        margin-bottom: 1;
    }
    .panel-title {
        color: #93c5fd;
        text-style: bold;
        margin-bottom: 1;
    }
    #connections-summary {
        height: 15;
    }
    #infra-map {
        height: 1fr;
    }
    #chat-panel {
        height: 1fr;
    }
    #activity-panel {
        height: 16;
    }
    #chat-log, #activity-log {
        height: 1fr;
        border: none;
        background: #020617;
    }
    #command-bar {
        dock: bottom;
        height: 3;
        border: round #4b5563;
        background: #020617;
        padding: 0 1;
    }
    #command-input {
        border: none;
        background: transparent;
        color: #f8fafc;
    }
    """

    BINDINGS = [("ctrl+c", "quit", "Quit")]

    def __init__(self, profile_name: str | None, mock: bool, base_path: Path | None = None) -> None:
        super().__init__()
        self.default_profile_name = profile_name
        self.mock = mock
        self.base_path = base_path or Path.cwd()
        self.executor = MidmanExecutor()
        self.connectors: list[ConnectorStatus] = []
        self.default_profile: Profile | None = None
        self.wizard_step: str | None = None
        self.pending_provider: str | None = None
        self.pending_endpoint: str | None = None
        self.pending_api_key: str | None = None
        self.pending_target: dict[str, str] = {}
        self.ai_connected = False
        self.ai_status_message = "Not configured"
        self.last_ai_request_status = "No requests yet"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-grid"):
            with Horizontal(id="top-row"):
                with Vertical(id="left-column"):
                    with InfoPanel(id="connections-summary", classes="panel"):
                        yield Label("AI Connections", classes="panel-title")
                        yield Static(id="connections-body")
                    with InfoPanel(id="infra-map", classes="panel"):
                        yield Label("Infrastructure Map", classes="panel-title")
                        yield Tree("AI Module", id="infra-tree")
                with Vertical(id="right-column"):
                    with InfoPanel(id="chat-panel", classes="panel"):
                        yield Label("AI Command Interface", classes="panel-title")
                        with VerticalScroll():
                            yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)
                    with InfoPanel(id="activity-panel", classes="panel"):
                        yield Label("Activity Log", classes="panel-title")
                        yield Log(id="activity-log", auto_scroll=True, highlight=True)
            with Container(id="command-bar"):
                yield Input(placeholder="Type a request or /help, /connect, /target-add, /use <name>, /exit", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "MidMan Dashboard"
        self.sub_title = "Infrastructure operations console"
        stored_backend = load_backend_config(self.base_path)
        if stored_backend:
            ok, message = test_backend_connection(stored_backend)
            self.ai_connected = ok
            self.ai_status_message = message
            self._log_activity(
                f"[{now_stamp()}] restored AI backend: {stored_backend.display_name} - {message}",
                severity="success" if ok else "warning",
            )
        self._refresh_connectors()
        if self.default_profile_name:
            try:
                self.default_profile = load_profile(self.default_profile_name, base_path=self.base_path)
                self._log_activity(f"[{now_stamp()}] default target set to {self.default_profile.name}", severity="success")
            except Exception as exc:  # noqa: BLE001
                self._log_activity(f"[{now_stamp()}] failed to load default profile: {exc}", severity="error")
        self._append_ai("AI", "Dashboard ready. Type /help for commands.", style="bold bright_green")
        self.query_one("#command-input", Input).focus()

    @on(Input.Submitted, "#command-input")
    def handle_command(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.query_one("#command-input", Input).value = ""
        if not value:
            return

        if self.wizard_step is not None:
            self._handle_wizard(value)
            return

        if value == "/exit":
            self.exit()
            return
        if value == "/help":
            self._append_ai(
                "AI",
                "Commands: /help, /connect, /targets, /probe, /target-add, /use <name>, /logs, /exit",
                style="bold yellow",
            )
            self._log_activity(f"[{now_stamp()}] help requested")
            return
        if value == "/connect":
            self.wizard_step = "provider"
            self._append_ai("AI", "Connect wizard: choose backend [ollama/openai/cloud].", style="bold magenta")
            self._log_activity(f"[{now_stamp()}] AI connect wizard started")
            return
        if value == "/targets":
            self._refresh_connectors()
            self._append_ai("AI", f"Loaded {len(self.connectors)} configured connectors.", style="bold bright_blue")
            self._log_activity(f"[{now_stamp()}] refreshed connector inventory")
            return
        if value == "/probe":
            self._refresh_connectors(probe=True)
            reachable = sum(1 for item in self.connectors if item.status == "reachable")
            unreachable = sum(1 for item in self.connectors if item.status == "unreachable")
            self._append_ai(
                "AI",
                f"Probe complete. Reachable: {reachable}, unreachable: {unreachable}.",
                style="bold bright_blue",
            )
            self._log_activity(
                f"[{now_stamp()}] connector probe complete: {reachable} reachable, {unreachable} unreachable",
                severity="success" if unreachable == 0 else "warning",
            )
            return
        if value == "/target-add":
            self.pending_target = {}
            self.wizard_step = "target_name"
            self._append_ai("AI", "Add target wizard: enter target name.", style="bold magenta")
            self._log_activity(f"[{now_stamp()}] target add wizard started")
            return
        if value.startswith("/use "):
            self._set_active_profile(value.split(" ", 1)[1].strip())
            return
        if value == "/logs":
            self._append_ai("AI", "Recent activity remains visible in the lower-right panel.", style="bold bright_blue")
            self._log_activity(f"[{now_stamp()}] log summary requested")
            return

        self._append_ai("User", value, style="bold cyan")
        if self.default_profile:
            try:
                report = self.executor.ask(value, self.default_profile, mock=self.mock)
            except Exception as exc:  # noqa: BLE001
                if not self._maybe_chat(value):
                    self._append_ai("AI", str(exc), style="bold red")
                    self._log_activity(f"[{now_stamp()}] request failed on {self.default_profile.name}: {exc}", severity="error")
            else:
                self._record_report(report)
            return

        if not self._maybe_chat(value):
            self._append_ai("AI", "No active target. Use /use <name> or /target-add, or configure AI chat with /connect.", style="bold yellow")
            self._log_activity(f"[{now_stamp()}] request skipped; no active target or AI backend", severity="warning")

    def _handle_wizard(self, value: str) -> None:
        step = self.wizard_step
        if step == "provider":
            provider = value.strip().lower()
            if provider not in {"ollama", "openai", "cloud"}:
                self._append_ai("AI", "Choose one of: ollama, openai, cloud.", style="bold red")
                return
            self.pending_provider = provider
            if provider == "ollama":
                self.wizard_step = "endpoint"
                self._append_ai("AI", "Enter Ollama host or IP:port, for example 100.123.179.111:11434", style="bold magenta")
                return
            if provider == "openai":
                self.wizard_step = "api_key"
                self._append_ai("AI", "Enter OpenAI API key.", style="bold magenta")
                return
            self.wizard_step = "endpoint"
            self._append_ai("AI", "Enter cloud endpoint URL.", style="bold magenta")
            return

        if step == "endpoint":
            self.pending_endpoint = value.strip()
            if self.pending_provider == "ollama":
                self.wizard_step = "model"
                self._append_ai("AI", "Enter Ollama model name, for example llama3.1", style="bold magenta")
                return
            self.wizard_step = "api_key"
            self._append_ai("AI", "Enter cloud API key or token.", style="bold magenta")
            return

        if step == "api_key":
            self.pending_api_key = value.strip()
            self.wizard_step = "model"
            if self.pending_provider == "openai":
                self._append_ai("AI", "Enter OpenAI model name, for example gpt-5-mini", style="bold magenta")
            else:
                self._append_ai("AI", "Enter cloud model or deployment name.", style="bold magenta")
            return

        if step == "model":
            provider = self.pending_provider or "cloud"
            endpoint = self.pending_endpoint
            if provider == "openai":
                endpoint = "api.openai.com"
            config = configure_backend(provider=provider, endpoint=endpoint, model=value.strip(), api_key=self.pending_api_key)
            save_backend_config(config, self.base_path)
            ok, message = test_backend_connection(config)
            self.ai_connected = ok
            self.ai_status_message = message
            self._append_ai(
                "AI",
                f"{'Connected' if ok else 'Connection failed'}: {config.display_name}. {message}",
                style="bold bright_green" if ok else "bold red",
            )
            self._log_activity(
                f"[{now_stamp()}] AI backend configured: {config.display_name} - {message}",
                severity="success" if ok else "error",
            )
            self._reset_ai_wizard()
            self._refresh_connectors()
            return

        if step == "target_name":
            self.pending_target["name"] = value.strip()
            self.wizard_step = "target_type"
            self._append_ai("AI", "Target type? [linux/network/management]", style="bold magenta")
            return
        if step == "target_type":
            if value.strip().lower() not in {"linux", "network", "management"}:
                self._append_ai("AI", "Choose one of: linux, network, management.", style="bold red")
                return
            self.pending_target["type"] = value.strip().lower()
            self.wizard_step = "target_host"
            self._append_ai("AI", "Enter host or IP address.", style="bold magenta")
            return
        if step == "target_host":
            self.pending_target["host"] = value.strip()
            self.wizard_step = "target_port"
            self._append_ai("AI", "Enter port. Use 22 for SSH or 443 for management.", style="bold magenta")
            return
        if step == "target_port":
            self.pending_target["port"] = value.strip()
            if self.pending_target["type"] == "management":
                self.wizard_step = "target_adapter"
                self._append_ai("AI", "Adapter type? [idrac/ilo/bmc/placeholder]", style="bold magenta")
            else:
                self.wizard_step = "target_username"
                self._append_ai("AI", "Enter SSH username.", style="bold magenta")
            return
        if step == "target_username":
            self.pending_target["username"] = value.strip()
            self._persist_target()
            return
        if step == "target_adapter":
            self.pending_target["adapter"] = value.strip() or "placeholder"
            self._persist_target()

    def _persist_target(self) -> None:
        payload: dict[str, object] = {
            "name": self.pending_target["name"],
            "type": self.pending_target["type"],
            "host": self.pending_target["host"],
            "port": int(self.pending_target["port"]),
        }
        if self.pending_target.get("username"):
            payload["username"] = self.pending_target["username"]
        if self.pending_target.get("adapter"):
            payload["adapter"] = self.pending_target["adapter"]
        save_profile_mapping(self.pending_target["name"], payload, self.base_path)
        self._set_active_profile(self.pending_target["name"])
        self._append_ai("AI", f"Saved target {self.pending_target['name']} and made it active.", style="bold bright_green")
        self._log_activity(f"[{now_stamp()}] saved target {self.pending_target['name']}", severity="success")
        self.pending_target = {}
        self.wizard_step = None
        self._refresh_connectors()

    def _set_active_profile(self, name: str) -> None:
        try:
            self.default_profile = load_profile(name, base_path=self.base_path)
        except Exception as exc:  # noqa: BLE001
            self._append_ai("AI", f"Could not load target '{name}': {exc}", style="bold red")
            self._log_activity(f"[{now_stamp()}] failed to load target {name}: {exc}", severity="error")
            return
        self._append_ai("AI", f"Active target set to {self.default_profile.name}.", style="bold bright_green")
        self._log_activity(f"[{now_stamp()}] active target set to {self.default_profile.name}", severity="success")

    def _maybe_chat(self, value: str) -> bool:
        config = load_backend_config(self.base_path)
        if not config or not self.ai_connected:
            return False
        response = chat_with_backend(config, value)
        if response.startswith("AI backend error:"):
            self.last_ai_request_status = response.removeprefix("AI backend error: ").strip()
            self._append_ai("AI", self.last_ai_request_status, style="bold red")
            self._log_activity(f"[{now_stamp()}] chat failed via {config.provider}: {self.last_ai_request_status}", severity="error")
        else:
            self.last_ai_request_status = f"OK via {config.provider}"
            self._append_ai("AI", response, style="bold bright_green")
            self._log_activity(f"[{now_stamp()}] chat completed via {config.provider}", severity="success")
        self._refresh_connectors()
        return True

    def _refresh_connectors(self, probe: bool = False) -> None:
        self.connectors = collect_connectors(base_path=self.base_path, probe=probe, timeout=1.5)
        counts = summarize_connector_counts(self.connectors)
        reachable = sum(1 for item in self.connectors if item.status == "reachable")
        unreachable = sum(1 for item in self.connectors if item.status == "unreachable")
        body = Text()
        body.append("AI API: ", style="bold white")
        body.append("Connected" if self.ai_connected else "Not connected", style="bold bright_green" if self.ai_connected else "bold red")
        body.append("\n")
        body.append("SSH servers: ", style="bold yellow")
        body.append(f"{counts['linux']}", style="bright_cyan")
        body.append("\n")
        body.append("iDRAC / iLO / BMC: ", style="bold yellow")
        body.append(f"{counts['management']}", style="bright_green")
        body.append("\n")
        body.append("Switches: ", style="bold yellow")
        body.append(f"{counts['network']}", style="bright_cyan")
        body.append("\n")
        body.append("Targets probe: ", style="bold white")
        if probe:
            body.append(f"{reachable} up / {unreachable} down", style="bright_green" if unreachable == 0 else "yellow")
        else:
            body.append("not run", style="dim")
        body.append("\n")
        body.append("AI Module: ", style="bold white")
        body.append(resolve_ai_backend(), style="bold bright_blue")
        body.append("\n")
        body.append("Status: ", style="bold white")
        body.append(self.ai_status_message, style="yellow")
        body.append("\n")
        body.append("Last request: ", style="bold white")
        body.append(self.last_ai_request_status, style="bright_magenta" if self.last_ai_request_status.startswith("OK") else "yellow")
        self.query_one("#connections-body", Static).update(body)
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        tree = self.query_one("#infra-tree", Tree)
        tree.clear()
        tree.root.label = Text("AI Module", style="bold bright_blue")
        groups = {
            "SSH Servers": [item for item in self.connectors if item.target_type == "linux"],
            "iDRAC Systems": [item for item in self.connectors if item.target_type == "management" and (item.adapter or "").lower() == "idrac"],
            "iLO Systems": [item for item in self.connectors if item.target_type == "management" and (item.adapter or "").lower() == "ilo"],
            "Switches": [item for item in self.connectors if item.target_type == "network"],
        }
        fallback_management = [
            item for item in self.connectors
            if item.target_type == "management" and (item.adapter or "").lower() not in {"idrac", "ilo"}
        ]
        if fallback_management:
            groups["Management Systems"] = fallback_management
        for group_name, items in groups.items():
            branch = tree.root.add(group_name)
            if not items:
                branch.add_leaf("No targets")
                continue
            for connector in items:
                active = " [active]" if self.default_profile and connector.name == self.default_profile.name else ""
                status_text, status_style = _connector_status_badge(connector.status)
                branch.add_leaf(Text.assemble(
                    (connector.name, "bold white"),
                    (active, "bold bright_cyan" if active else "white"),
                    (f" [{connector.endpoint}] ", "dim"),
                    (status_text, status_style),
                ))
        tree.root.expand_all()

    def _append_ai(self, speaker: str, message: str, style: str = "white") -> None:
        line = Text()
        line.append(f"{speaker}: ", style=style)
        line.append(message, style="white")
        self.query_one("#chat-log", RichLog).write(line)

    def _log_activity(self, message: str, severity: str = "info") -> None:
        styles = {"info": "cyan", "warning": "yellow", "error": "red", "success": "green"}
        self.query_one("#activity-log", Log).write_line(f"[{styles.get(severity, 'white')}]{message}[/{styles.get(severity, 'white')}]")

    def _record_report(self, report: ExecutionReport) -> None:
        self._append_ai("AI", report.summary, style="bold bright_green")
        self._log_activity(f"[{now_stamp()}] executed {report.action} on {report.profile}", severity="success")
        for result in report.results[:3]:
            preview = result.stdout.splitlines()[0] if result.stdout else "ok"
            severity = "success" if result.exit_status == 0 else "error"
            self._log_activity(f"[{now_stamp()}] {result.command} -> {preview}", severity=severity)

    def _reset_ai_wizard(self) -> None:
        self.wizard_step = None
        self.pending_provider = None
        self.pending_endpoint = None
        self.pending_api_key = None


def _connector_status_badge(status: str) -> tuple[str, str]:
    mapping = {
        "reachable": ("[up]", "bold bright_green"),
        "unreachable": ("[down]", "bold red"),
        "configured": ("[saved]", "yellow"),
    }
    return mapping.get(status, (f"[{status}]", "white"))
