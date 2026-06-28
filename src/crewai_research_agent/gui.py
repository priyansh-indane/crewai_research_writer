#!/usr/bin/env python
"""
Desktop GUI for crewai_research_agent — "Mission Control" theme.

Setup (one-time):
    pip install customtkinter

Run from your project root (crewai_research_writer/):
    python src/crewai_research_agent/gui.py
"""

import threading
import itertools
from datetime import datetime

import customtkinter as ctk

from dotenv import load_dotenv
load_dotenv()

from crewai_research_agent.crew import CrewaiResearchAgent

# ---------------------------------------------------------------------------
# Theme tokens
# ---------------------------------------------------------------------------
BG = "#0F1115"
PANEL = "#171A21"
PANEL_BORDER = "#262B36"
TEXT_PRIMARY = "#E6E9EF"
TEXT_MUTED = "#8B95A5"
ACCENT = "#3FE0C5"        # electric cyan — primary action
ACCENT_HOVER = "#34C7AE"
AMBER = "#F5A623"         # running / in-progress state
AMBER_DIM = "#7A5418"
DANGER = "#FF6B6B"
SUCCESS = "#3FE0C5"
MONO_FONT = "Consolas"
DISPLAY_FONT = "Segoe UI"

ctk.set_appearance_mode("dark")


class PulseDot(ctk.CTkCanvas):
    """A small animated status dot: pulses amber while running, solid otherwise."""

    def __init__(self, master, size=14, **kwargs):
        super().__init__(master, width=size, height=size,
                          bg=PANEL, highlightthickness=0, **kwargs)
        self.size = size
        self._radii = itertools.cycle([3, 4, 5, 6, 5, 4])
        self._pulsing = False
        self._color = TEXT_MUTED
        self._draw(4)

    def _draw(self, r):
        self.delete("all")
        cx = cy = self.size / 2
        self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=self._color, outline="")

    def set_state(self, state):
        # state: "idle" | "running" | "done" | "error"
        if state == "idle":
            self._pulsing = False
            self._color = TEXT_MUTED
            self._draw(4)
        elif state == "running":
            self._color = AMBER
            self._pulsing = True
            self._animate()
        elif state == "done":
            self._pulsing = False
            self._color = SUCCESS
            self._draw(6)
        elif state == "error":
            self._pulsing = False
            self._color = DANGER
            self._draw(6)

    def _animate(self):
        if not self._pulsing:
            return
        self._draw(next(self._radii))
        self.after(150, self._animate)


class CrewGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Research Agent — Mission Control")
        self.geometry("780x620")
        self.minsize(560, 420)
        self.configure(fg_color=BG)

        self._build_header()
        self._build_input_row()
        self._build_status_row()
        self._build_output_panel()

    # ---------------------------------------------------------------- header
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))

        eyebrow = ctk.CTkLabel(
            header, text="AUTONOMOUS RESEARCH CREW",
            font=(DISPLAY_FONT, 11, "bold"), text_color=ACCENT,
        )
        eyebrow.pack(anchor="w")

        title = ctk.CTkLabel(
            header, text="Mission Control",
            font=(DISPLAY_FONT, 26, "bold"), text_color=TEXT_PRIMARY,
        )
        title.pack(anchor="w", pady=(2, 0))

        subtitle = ctk.CTkLabel(
            header, text="Give it a topic. The crew researches, writes, and reports back.",
            font=(DISPLAY_FONT, 12), text_color=TEXT_MUTED,
        )
        subtitle.pack(anchor="w", pady=(2, 0))

    # ------------------------------------------------------------ input row
    def _build_input_row(self):
        card = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=14,
                             border_width=1, border_color=PANEL_BORDER)
        card.pack(fill="x", padx=28, pady=(16, 0))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)
        inner.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(inner, text="TOPIC", font=(DISPLAY_FONT, 10, "bold"),
                              text_color=TEXT_MUTED)
        label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.topic_entry = ctk.CTkEntry(
            inner, placeholder_text="e.g. GTA 6, quantum batteries, the future of remote work...",
            font=(DISPLAY_FONT, 13), fg_color=BG, border_color=PANEL_BORDER,
            border_width=1, corner_radius=10, height=42,
            text_color=TEXT_PRIMARY,
        )
        self.topic_entry.grid(row=1, column=0, sticky="ew", padx=(0, 12))
        self.topic_entry.insert(0, "GTA 6")
        self.topic_entry.bind("<Return>", lambda e: self.run_crew_threaded())

        self.run_button = ctk.CTkButton(
            inner, text="▶  Run Crew", command=self.run_crew_threaded,
            font=(DISPLAY_FONT, 13, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#0F1115", corner_radius=10, height=42, width=130,
        )
        self.run_button.grid(row=1, column=1)

    # ----------------------------------------------------------- status row
    def _build_status_row(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=32, pady=(14, 4))

        self.dot = PulseDot(row, size=14)
        self.dot.pack(side="left", padx=(0, 8))

        self.status_label = ctk.CTkLabel(
            row, text="Ready when you are.",
            font=(DISPLAY_FONT, 12), text_color=TEXT_MUTED,
        )
        self.status_label.pack(side="left")

        self.timer_label = ctk.CTkLabel(
            row, text="", font=(MONO_FONT, 11), text_color=TEXT_MUTED,
        )
        self.timer_label.pack(side="right")

    # --------------------------------------------------------- output panel
    def _build_output_panel(self):
        panel = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=14,
                              border_width=1, border_color=PANEL_BORDER)
        panel.pack(fill="both", expand=True, padx=28, pady=(8, 24))

        header_row = ctk.CTkFrame(panel, fg_color="transparent")
        header_row.pack(fill="x", padx=18, pady=(14, 6))

        ctk.CTkLabel(header_row, text="OUTPUT LOG", font=(DISPLAY_FONT, 10, "bold"),
                     text_color=TEXT_MUTED).pack(side="left")

        self.clear_button = ctk.CTkButton(
            header_row, text="Clear", width=60, height=24,
            font=(DISPLAY_FONT, 10), fg_color="transparent", hover_color=PANEL_BORDER,
            text_color=TEXT_MUTED, border_width=1, border_color=PANEL_BORDER,
            corner_radius=6, command=self.clear_output,
        )
        self.clear_button.pack(side="right")

        self.output_box = ctk.CTkTextbox(
            panel, fg_color=BG, text_color="#B7F5E8",
            font=(MONO_FONT, 12), corner_radius=10, wrap="word",
            border_width=0,
        )
        self.output_box.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.output_box.insert("1.0", "Output will appear here once the crew finishes its run.\n")
        self.output_box.configure(state="disabled")

    # -------------------------------------------------------------- actions
    def clear_output(self):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")

    def log(self, text):
        self.output_box.configure(state="normal")
        self.output_box.insert("end", text + "\n")
        self.output_box.see("end")
        self.output_box.configure(state="disabled")

    def run_crew_threaded(self):
        topic = self.topic_entry.get().strip()
        if not topic:
            self.status_label.configure(text="Enter a topic first.", text_color=DANGER)
            return

        self.run_button.configure(state="disabled", text="Running…",
                                   fg_color=AMBER_DIM, text_color=TEXT_MUTED)
        self.dot.set_state("running")
        self.status_label.configure(text=f"Researching “{topic}”…", text_color=AMBER)
        self.clear_output()

        self._start_time = datetime.now()
        self._tick()

        thread = threading.Thread(target=self.run_crew, args=(topic,), daemon=True)
        thread.start()

    def _tick(self):
        if self.dot._pulsing:
            elapsed = (datetime.now() - self._start_time).seconds
            self.timer_label.configure(text=f"{elapsed}s")
            self.after(1000, self._tick)
        else:
            self.timer_label.configure(text="")

    def run_crew(self, topic):
        try:
            inputs = {
                "topic": topic,
                "current_year": str(datetime.now().year),
            }
            result = CrewaiResearchAgent().crew().kickoff(inputs=inputs)
            self.after(0, self.on_success, result)
        except Exception as e:
            self.after(0, self.on_error, e)

    def on_success(self, result):
        self.log(str(result))
        self.dot.set_state("done")
        self.status_label.configure(text="Done. Report ready below.", text_color=SUCCESS)
        self.run_button.configure(state="normal", text="▶  Run Crew",
                                   fg_color=ACCENT, text_color="#0F1115")

    def on_error(self, error):
        self.log(f"⚠ ERROR\n{error}")
        self.dot.set_state("error")
        self.status_label.configure(text="Something went wrong. See log below.", text_color=DANGER)
        self.run_button.configure(state="normal", text="▶  Run Crew",
                                   fg_color=ACCENT, text_color="#0F1115")


def main():
    app = CrewGUI()
    app.mainloop()


if __name__ == "__main__":
    main()