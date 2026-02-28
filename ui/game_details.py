"""Game details window for displaying board game information."""

import webbrowser
from typing import TYPE_CHECKING

import customtkinter as ctk

from config import MIN_RATING_FOR_NOTIFICATION
from integrations.onesignal_caller import send_custom_event

if TYPE_CHECKING:
    from model.board_game import BoardGame


class GameDetailsWindow(ctk.CTkToplevel):
    """Window to display detailed game information."""

    def __init__(self, parent, game: "BoardGame") -> None:
        super().__init__(parent)
        self.game = game
        self.title(f"Game Details: {game.name}")
        self.geometry("800x700")

        self._create_widgets()

    def _create_widgets(self) -> None:
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            scroll_frame,
            text=self.game.name,
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack(pady=(0, 10))

        url_button = ctk.CTkButton(
            scroll_frame,
            text=f"🔗 {self.game.url}",
            command=lambda: webbrowser.open(self.game.url),
            fg_color="transparent",
            text_color="lightblue",
        )
        url_button.pack(pady=(0, 20))

        info_frame = ctk.CTkFrame(scroll_frame)
        info_frame.pack(fill="x", pady=10)

        info_items = [
            ("💰 Price", f"{self.game.final_price} Kč" if self.game.final_price else "N/A"),
            ("📊 Your Rating", f"{self.game.my_rating:.1f}" if self.game.my_rating else "N/A"),
            ("⭐ BGG Rating", f"{self.game.bgg_rating:.1f} / 10" if self.game.bgg_rating else "N/A"),
            ("🏢 Distributor", self.game.distributor or "N/A"),
            ("📦 Type", self.game.game_type or "N/A"),
            (
                "👥 Players",
                f"{self.game.min_players}-{self.game.max_players}"
                if self.game.min_players and self.game.max_players
                else "N/A",
            ),
            ("⏱️ Play Time", f"{self.game.play_time_minutes} min" if self.game.play_time_minutes else "N/A"),
            ("🎂 Min Age", f"{self.game.min_age}+" if self.game.min_age else "N/A"),
            ("🧩 Complexity", f"{self.game.complexity:.1f} / 5" if self.game.complexity else "N/A"),
            ("✍️ Author", self.game.author or "N/A"),
            ("📅 Year", str(self.game.year_published) if self.game.year_published else "N/A"),
        ]

        for label, value in info_items:
            row_frame = ctk.CTkFrame(info_frame)
            row_frame.pack(fill="x", padx=10, pady=5)

            label_widget = ctk.CTkLabel(row_frame, text=label, width=150, anchor="w")
            label_widget.pack(side="left", padx=10)

            value_widget = ctk.CTkLabel(row_frame, text=str(value), anchor="w")
            value_widget.pack(side="left", padx=10, fill="x", expand=True)

        if self.game.game_categories:
            cat_text = ", ".join(self.game.game_categories)
            cat_label = ctk.CTkLabel(
                scroll_frame,
                text=f"🎯 Categories: {cat_text}",
                wraplength=700,
                justify="left",
            )
            cat_label.pack(pady=10, anchor="w")

        if self.game.game_mechanics:
            mech_text = ", ".join(self.game.game_mechanics)
            mech_label = ctk.CTkLabel(
                scroll_frame,
                text=f"⚙️ Mechanics: {mech_text}",
                wraplength=700,
                justify="left",
            )
            mech_label.pack(pady=10, anchor="w")

        if self.game.my_rating and self.game.my_rating > MIN_RATING_FOR_NOTIFICATION:
            notify_button = ctk.CTkButton(
                scroll_frame,
                text="🔔 Send OneSignal Notification",
                command=self._send_notification,
                fg_color="green",
            )
            notify_button.pack(pady=20)

    def _send_notification(self) -> None:
        """Send OneSignal notification for the current game."""
        send_custom_event(self.game.to_json())
