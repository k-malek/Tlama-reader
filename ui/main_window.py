"""Main application window for Tlama Caller GUI."""

import platform
import threading
import webbrowser
from typing import List, Optional

import customtkinter as ctk
from tkinter import ttk

from config import CATEGORY_FILTERS, FILTER_GROUPS, FILTERS, MECHANIC_FILTERS
from database import (
    get_all_games,
    get_game_count,
    load_game,
    save_game,
    search_games_in_db,
    update_game_boolean,
)
from model.board_game import BoardGame
from ui.game_details import GameDetailsWindow
from utils.search import search_for_game
from website_caller import WebsiteCaller


class TlamaCallerGUI(ctk.CTk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title("🎲 Tlama Games Deal Finder")
        self.geometry("1200x800")
        self._center_on_screen()

        self.caller: Optional[WebsiteCaller] = None
        self.current_games: List[BoardGame] = []

        self._create_widgets()
        self._init_caller()

    @staticmethod
    def _format_price(game: BoardGame) -> str:
        """Format price for table: show discount % only when applicable."""
        if not game.final_price:
            return "N/A"
        base = f"{game.final_price} Kč"
        if game.discount_percent and game.discount_percent > 0:
            return f"{base} (−{game.discount_percent}%)"
        return base

    def _center_on_screen(self) -> None:
        """Center the window on the primary/main screen."""
        self.update_idletasks()
        width, height = 1200, 800
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _init_caller(self) -> None:
        """Initialize website caller in background."""
        def init() -> None:
            self.caller = WebsiteCaller(timeout=30, use_browser=True)
            self.after(0, lambda: self.status_label.configure(text="✅ Ready"))

        thread = threading.Thread(target=init, daemon=True)
        thread.start()
        self.status_label.configure(text="⏳ Initializing...")

    def _create_widgets(self) -> None:
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            title_frame,
            text="🎲 Tlama Games Deal Finder",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=20, pady=10)

        close_btn = ctk.CTkButton(
            title_frame,
            text="✕",
            width=30,
            height=30,
            command=self.on_closing,
            fg_color="transparent",
            hover_color="#c42b1c",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        )
        close_btn.pack(side="right", padx=10, pady=5)

        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=20, pady=(0, 0))

        self.status_label = ctk.CTkLabel(status_frame, text="⏳ Initializing...")
        self.status_label.pack(side="left", padx=20, pady=10)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.db_tab = self.tabview.add("📚 Database")
        self.search_tab = self.tabview.add("🔍 Search")

        self.db_sort_column: Optional[str] = None
        self.db_sort_direction: Optional[str] = None
        self.db_games: List[BoardGame] = []

        self.search_sort_column: Optional[str] = None
        self.search_sort_direction: Optional[str] = None
        self.search_games: List[BoardGame] = []

        self._create_database_tab()
        self._create_search_tab()

    def _create_database_tab(self) -> None:
        top_frame = ctk.CTkFrame(self.db_tab)
        top_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(top_frame, text="Database Browser", font=ctk.CTkFont(size=20, weight="bold")).pack(
            side="left", padx=10
        )

        ctk.CTkButton(
            top_frame, text="⭐ Rerate All", command=self._rerate_all_games,
            fg_color="#d97706", hover_color="#b45309"
        ).pack(side="right", padx=10)
        ctk.CTkButton(top_frame, text="🔄 Refresh", command=self._refresh_database).pack(side="right", padx=10)

        search_frame = ctk.CTkFrame(self.db_tab)
        search_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=10)
        self.db_search_entry = ctk.CTkEntry(search_frame, placeholder_text="Game name...")
        self.db_search_entry.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(search_frame, text="Search", command=self._search_database).pack(side="left", padx=10)

        list_frame = ctk.CTkFrame(self.db_tab)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("Name", "Price", "Rating", "BGG", "Evil", "Owned", "Link")
        self.db_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)

        style = ttk.Style()
        style.configure("Treeview", font=("TkDefaultFont", 16))
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))

        for col in columns:
            if col == "Link":
                self.db_tree.heading(col, text=col)
            else:
                self.db_tree.heading(col, text=col, command=lambda c=col: self._sort_db_table(c))
            self.db_tree.column(col, width=200)

        self.db_tree.column("Name", width=300)
        self.db_tree.column("Price", width=100)
        self.db_tree.column("Rating", width=100)
        self.db_tree.column("BGG", width=80)
        self.db_tree.column("Evil", width=60, anchor="center")
        self.db_tree.column("Owned", width=70, anchor="center")
        self.db_tree.column("Link", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.db_tree.yview)
        self.db_tree.configure(yscrollcommand=scrollbar.set)
        self.db_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.db_tree.bind("<Double-1>", self._on_db_game_select)
        self.db_tree.bind("<Button-1>", self._on_db_tree_click)
        self.db_tree.bind("<Motion>", self._on_db_tree_motion)
        self.db_tree.bind("<Leave>", lambda e: self.db_tree.configure(cursor=""))

        self.after(100, self._refresh_database)

    def _create_search_tab(self) -> None:
        top_frame = ctk.CTkFrame(self.search_tab)
        top_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(top_frame, text="Search Filters", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", padx=10, pady=(0, 15)
        )

        dropdowns_frame = ctk.CTkFrame(top_frame)
        dropdowns_frame.pack(fill="x", padx=10, pady=10)

        self.selected_filters: List[str] = []
        self.filter_dropdowns: dict = {}

        row, col, max_cols = 0, 0, 3
        for group_name, group_filters in FILTER_GROUPS.items():
            valid_filters = [f for f in group_filters if f in FILTERS]
            if not valid_filters:
                continue
            dropdown_options = ["Select..."] + [f.replace("_", " ").title() for f in valid_filters]
            dropdown = ctk.CTkComboBox(
                dropdowns_frame,
                values=dropdown_options,
                command=lambda v, g=group_name, f=valid_filters: self._on_filter_selected(v, g, f),
                width=150,
            )
            dropdown.set("Select...")
            ctk.CTkLabel(dropdowns_frame, text=f"{group_name}:", width=100, anchor="w").grid(
                row=row, column=col * 2, padx=5, pady=5, sticky="w"
            )
            dropdown.grid(row=row, column=col * 2 + 1, padx=5, pady=5, sticky="w")
            self.filter_dropdowns[group_name] = dropdown
            col += 1
            if col >= max_cols:
                col, row = 0, row + 1

        if CATEGORY_FILTERS:
            cat_options = ["Select..."] + [f.replace("_", " ").title() for f in CATEGORY_FILTERS]
            cat_dropdown = ctk.CTkComboBox(
                dropdowns_frame,
                values=cat_options,
                command=lambda v, f=CATEGORY_FILTERS: self._on_category_selected(v, f),
                width=150,
            )
            cat_dropdown.set("Select...")
            ctk.CTkLabel(dropdowns_frame, text="Category:", width=100, anchor="w").grid(
                row=row, column=col * 2, padx=5, pady=5, sticky="w"
            )
            cat_dropdown.grid(row=row, column=col * 2 + 1, padx=5, pady=5, sticky="w")
            self.filter_dropdowns["Category"] = cat_dropdown
            col += 1
            if col >= max_cols:
                col, row = 0, row + 1

        if MECHANIC_FILTERS:
            mech_options = ["Select..."] + [f.replace("_", " ").title() for f in MECHANIC_FILTERS]
            mech_dropdown = ctk.CTkComboBox(
                dropdowns_frame,
                values=mech_options,
                command=lambda v, f=MECHANIC_FILTERS: self._on_mechanic_selected(v, f),
                width=150,
            )
            mech_dropdown.set("Select...")
            ctk.CTkLabel(dropdowns_frame, text="Mechanic:", width=100, anchor="w").grid(
                row=row, column=col * 2, padx=5, pady=5, sticky="w"
            )
            mech_dropdown.grid(row=row, column=col * 2 + 1, padx=5, pady=5, sticky="w")
            self.filter_dropdowns["Mechanic"] = mech_dropdown

        selected_frame = ctk.CTkFrame(top_frame)
        selected_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(selected_frame, text="Selected Filters:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            anchor="w", padx=10, pady=(10, 5)
        )
        self.selected_filters_frame = ctk.CTkFrame(selected_frame)
        self.selected_filters_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(selected_frame, text="Clear All", command=self._clear_all_filters, width=100, fg_color="gray", height=30).pack(
            anchor="e", padx=10, pady=5
        )

        search_btn_frame = ctk.CTkFrame(top_frame)
        search_btn_frame.pack(fill="x", padx=10, pady=15)
        ctk.CTkButton(
            search_btn_frame,
            text="🔍 Search Games",
            command=self._search_games,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            fg_color="#1f538d",
            hover_color="#14375e",
        ).pack(pady=10)

        self.progress_frame = ctk.CTkFrame(top_frame)
        self.progress_frame.pack(fill="x", padx=10, pady=10)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="", font=ctk.CTkFont(size=12))
        self.progress_label.pack(anchor="w", padx=10, pady=(5, 0))
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=600)
        self.progress_bar.pack(fill="x", padx=10, pady=(5, 10))
        self.progress_bar.set(0)
        self.progress_frame.pack_forget()

        results_frame = ctk.CTkFrame(self.search_tab)
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("Name", "Price", "Rating", "BGG", "Link")
        self.search_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        for col in columns:
            if col == "Link":
                self.search_tree.heading(col, text=col)
            else:
                self.search_tree.heading(col, text=col, command=lambda c=col: self._sort_search_table(c))
            self.search_tree.column(col, width=200)
        self.search_tree.column("Name", width=400)
        self.search_tree.column("Price", width=100)
        self.search_tree.column("Rating", width=100)
        self.search_tree.column("BGG", width=80)
        self.search_tree.column("Link", width=100)
        search_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=search_scrollbar.set)
        self.search_tree.pack(side="left", fill="both", expand=True)
        search_scrollbar.pack(side="right", fill="y")
        self.search_tree.bind("<Double-1>", self._on_search_game_select)
        self.search_tree.bind("<Button-1>", self._on_search_tree_click)
        self.search_tree.bind("<Motion>", self._on_search_tree_motion)
        self.search_tree.bind("<Leave>", lambda e: self.search_tree.configure(cursor=""))

    def _on_filter_selected(self, value: str, group_name: str, valid_filters: List[str]) -> None:
        if value == "Select...":
            return
        filter_key = next((f for f in valid_filters if f.replace("_", " ").title() == value), None)
        if filter_key and filter_key not in self.selected_filters:
            self.selected_filters.append(filter_key)
            self._update_selected_filters_display()

    def _on_category_selected(self, value: str, valid_filters: List[str]) -> None:
        if value == "Select...":
            return
        filter_key = next((f"cat:{f}" for f in valid_filters if f.replace("_", " ").title() == value), None)
        if filter_key and filter_key not in self.selected_filters:
            self.selected_filters.append(filter_key)
            self._update_selected_filters_display()

    def _on_mechanic_selected(self, value: str, valid_filters: List[str]) -> None:
        if value == "Select...":
            return
        filter_key = next((f"mech:{f}" for f in valid_filters if f.replace("_", " ").title() == value), None)
        if filter_key and filter_key not in self.selected_filters:
            self.selected_filters.append(filter_key)
            self._update_selected_filters_display()

    def _update_selected_filters_display(self) -> None:
        for widget in self.selected_filters_frame.winfo_children():
            widget.destroy()
        if not self.selected_filters:
            ctk.CTkLabel(self.selected_filters_frame, text="No filters selected", fg_color="transparent", text_color="gray").pack(
                anchor="w", padx=10, pady=5
            )
            return
        row, col, max_cols = 0, 0, 6
        for filter_key in self.selected_filters:
            if filter_key.startswith("cat:"):
                display_name = filter_key.replace("cat:", "").replace("_", " ").title()
                prefix = "📁"
            elif filter_key.startswith("mech:"):
                display_name = filter_key.replace("mech:", "").replace("_", " ").title()
                prefix = "⚙️"
            else:
                display_name = filter_key.replace("_", " ").title()
                prefix = "🏷️"
            tag_frame = ctk.CTkFrame(self.selected_filters_frame, fg_color="#1f538d", corner_radius=10)
            ctk.CTkLabel(tag_frame, text=f"{prefix} {display_name}", font=ctk.CTkFont(size=11)).pack(side="left", padx=8, pady=3)
            ctk.CTkButton(
                tag_frame, text="×", width=20, height=20,
                command=lambda fk=filter_key: self._remove_filter(fk),
                fg_color="transparent", hover_color="#c42b1c", font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(side="left", padx=(0, 5))
            tag_frame.grid(row=row, column=col, padx=5, pady=5, sticky="w")
            col += 1
            if col >= max_cols:
                col, row = 0, row + 1

    def _remove_filter(self, filter_key: str) -> None:
        if filter_key in self.selected_filters:
            self.selected_filters.remove(filter_key)
            self._update_selected_filters_display()
            self._reset_dropdown_for_filter(filter_key)

    def _reset_dropdown_for_filter(self, filter_key: str) -> None:
        for group_name, group_filters in FILTER_GROUPS.items():
            if filter_key in group_filters:
                if group_name in self.filter_dropdowns:
                    self.filter_dropdowns[group_name].set("Select...")
                return
        if filter_key.startswith("cat:") and "Category" in self.filter_dropdowns:
            self.filter_dropdowns["Category"].set("Select...")
        elif filter_key.startswith("mech:") and "Mechanic" in self.filter_dropdowns:
            self.filter_dropdowns["Mechanic"].set("Select...")

    def _clear_all_filters(self) -> None:
        self.selected_filters.clear()
        self._update_selected_filters_display()
        for dropdown in self.filter_dropdowns.values():
            dropdown.set("Select...")

    def _refresh_database(self) -> None:
        self.db_tree.delete(*self.db_tree.get_children())
        try:
            self.db_games = get_all_games(limit=1000)
            count = get_game_count()
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.configure(text=f"📚 Database: {count} games")
            self._apply_db_sort()
        except Exception as err:
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.configure(text=f"❌ Error: {err}")

    def _apply_db_sort(self) -> None:
        self.db_tree.delete(*self.db_tree.get_children())
        games = self.db_games.copy()
        if self.db_sort_column and self.db_sort_direction:
            games = self._sort_games(games, self.db_sort_column, self.db_sort_direction)
        for game in games:
            self.db_tree.insert("", "end", values=(
                game.name or "N/A",
                self._format_price(game),
                f"{game.my_rating:.1f}" if game.my_rating else "N/A",
                f"{game.bgg_rating:.1f}" if game.bgg_rating else "N/A",
                "■" if getattr(game, "has_demonic_vibe", False) else "□",
                "■" if getattr(game, "owned", False) else "□",
                "🔗 Open" if game.url else "N/A",
            ), tags=(game.url,))

    def _sort_db_table(self, column: str) -> None:
        if self.db_sort_column != column:
            self.db_sort_column = column
            self.db_sort_direction = "DESC"
        elif self.db_sort_direction == "DESC":
            self.db_sort_direction = "ASC"
        elif self.db_sort_direction == "ASC":
            self.db_sort_column = None
            self.db_sort_direction = None
        self._update_db_headers()
        self._apply_db_sort()

    def _update_db_headers(self) -> None:
        columns = ("Name", "Price", "Rating", "BGG", "Evil", "Owned", "Link")
        for col in columns:
            text = col
            if col == self.db_sort_column:
                text = f"{col} ▼" if self.db_sort_direction == "DESC" else f"{col} ▲"
            self.db_tree.heading(col, text=text)

    def _rerate_all_games(self) -> None:
        if hasattr(self, "status_label") and self.status_label:
            self.status_label.configure(text="⏳ Loading games for rerating...")

        def rerate() -> None:
            try:
                games = get_all_games(limit=None)
                total = len(games)
                if total == 0:
                    self.after(0, lambda: self.status_label.configure(text="⚠️ No games found in database"))
                    return
                self.after(0, lambda: self.status_label.configure(text=f"⭐ Rerating {total} games..."))
                updated_count = 0
                for idx, game in enumerate(games, 1):
                    reloaded = load_game(game.url)
                    if reloaded:
                        save_game(reloaded)
                        updated_count += 1
                    if idx % 10 == 0 or idx == total:
                        self.after(0, lambda i=idx, t=total: self.status_label.configure(text=f"⭐ Rerating: {i}/{t} games..."))
                self.after(0, lambda: self._refresh_database())
                self.after(0, lambda: self.status_label.configure(text=f"✅ Rerated {updated_count} games successfully"))
            except Exception as err:
                self.after(0, lambda msg=str(err): self.status_label.configure(text=f"❌ Error: {msg}"))

        threading.Thread(target=rerate, daemon=True).start()

    def _search_database(self) -> None:
        self.db_tree.delete(*self.db_tree.get_children())
        search_term = self.db_search_entry.get().strip()
        try:
            self.db_games = search_games_in_db(name=search_term, limit=500) if search_term else get_all_games(limit=500)
            self._apply_db_sort()
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.configure(text=f"📚 Found {len(self.db_games)} games")
        except Exception as err:
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.configure(text=f"❌ Error: {err}")

    def _search_games(self) -> None:
        if not self.caller:
            self.status_label.configure(text="⏳ Please wait, initializing...")
            return
        if not self.selected_filters:
            self.status_label.configure(text="⚠️ Please select at least one filter")
            return
        self.status_label.configure(text=f"🔍 Searching with {len(self.selected_filters)} filters...")
        self.search_tree.delete(*self.search_tree.get_children())
        self.progress_frame.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting search...")

        def progress_callback(stage: str, current: int, total: Optional[int], message: str) -> None:
            if stage == "pages":
                self.after(0, lambda: self.progress_label.configure(text=message))
                cp = self.progress_bar.get()
                self.after(0, lambda: self.progress_bar.set(0.02 if cp >= 0.18 else cp + 0.02))
            elif stage == "pages_complete":
                self.after(0, lambda: self.progress_bar.set(0.2))
                self.after(0, lambda: self.progress_label.configure(text=message))
            elif stage == "games" and total and total > 0:
                scaled = 0.2 + (current / total * 0.8)
                self.after(0, lambda p=scaled: self.progress_bar.set(p))
                self.after(0, lambda m=message: self.progress_label.configure(text=m))

        def search() -> None:
            try:
                games = search_for_game(self.caller, filters=self.selected_filters.copy(), progress_callback=progress_callback)
                self.current_games = games
                self.after(0, lambda: self.progress_frame.pack_forget())
                self.after(0, lambda: self._display_search_results(games))
            except Exception as err:
                self.after(0, lambda: self.progress_frame.pack_forget())
                self.after(0, lambda msg=str(err): self.status_label.configure(text=f"❌ Error: {msg}"))

        threading.Thread(target=search, daemon=True).start()

    def _display_search_results(self, games: List[BoardGame]) -> None:
        self.search_tree.delete(*self.search_tree.get_children())
        self.search_games = games[:100]
        self._apply_search_sort()
        self.status_label.configure(text=f"✅ Found {len(games)} games")

    def _apply_search_sort(self) -> None:
        self.search_tree.delete(*self.search_tree.get_children())
        games = self.search_games.copy()
        if self.search_sort_column and self.search_sort_direction:
            games = self._sort_games(games, self.search_sort_column, self.search_sort_direction)
        for game in games:
            self.search_tree.insert("", "end", values=(
                game.name or "N/A",
                self._format_price(game),
                f"{game.my_rating:.1f}" if game.my_rating else "N/A",
                f"{game.bgg_rating:.1f}" if game.bgg_rating else "N/A",
                "🔗 Open" if game.url else "N/A",
            ), tags=(game.url,))

    def _sort_search_table(self, column: str) -> None:
        if self.search_sort_column != column:
            self.search_sort_column = column
            self.search_sort_direction = "DESC"
        elif self.search_sort_direction == "DESC":
            self.search_sort_direction = "ASC"
        elif self.search_sort_direction == "ASC":
            self.search_sort_column = None
            self.search_sort_direction = None
        self._update_search_headers()
        self._apply_search_sort()

    def _update_search_headers(self) -> None:
        columns = ("Name", "Price", "Rating", "BGG", "Link")
        for col in columns:
            text = col
            if col == self.search_sort_column:
                text = f"{col} ▼" if self.search_sort_direction == "DESC" else f"{col} ▲"
            self.search_tree.heading(col, text=text)

    def _sort_games(self, games: List[BoardGame], column: str, direction: str) -> List[BoardGame]:
        def get_sort_key(game: BoardGame):
            if column == "Name":
                return (game.name or "").lower()
            elif column == "Price":
                try:
                    return int(float(game.final_price)) if game.final_price else 0
                except (ValueError, TypeError):
                    return 0
            elif column == "Rating":
                return game.my_rating if game.my_rating else 0
            elif column == "BGG":
                return game.bgg_rating if game.bgg_rating else 0
            elif column == "Evil":
                return 1 if getattr(game, "has_demonic_vibe", False) else 0
            elif column == "Owned":
                return 1 if getattr(game, "owned", False) else 0
            elif column == "Link":
                return game.url or ""
            return ""

        return sorted(games, key=get_sort_key, reverse=(direction == "DESC"))

    def _on_db_tree_motion(self, event: object) -> None:
        pointer = "pointinghand" if platform.system() == "Darwin" else "hand2"
        if self.db_tree.identify_region(event.x, event.y) == "cell":
            col = self.db_tree.identify_column(event.x)
            item = self.db_tree.identify_row(event.y)
            if item and col in ["#5", "#6", "#7"]:
                url = self.db_tree.item(item)["tags"][0]
                if url and url != "N/A":
                    self.db_tree.configure(cursor=pointer)
                    return
        self.db_tree.configure(cursor="")

    def _on_search_tree_motion(self, event: object) -> None:
        pointer = "pointinghand" if platform.system() == "Darwin" else "hand2"
        if self.search_tree.identify_region(event.x, event.y) == "cell":
            if self.search_tree.identify_column(event.x) == "#5":
                item = self.search_tree.identify_row(event.y)
                if item:
                    url = self.search_tree.item(item)["tags"][0]
                    if url and url != "N/A":
                        self.search_tree.configure(cursor=pointer)
                        return
        self.search_tree.configure(cursor="")

    def _on_db_tree_click(self, event: object) -> None:
        if self.db_tree.identify_region(event.x, event.y) != "cell":
            return
        col = self.db_tree.identify_column(event.x)
        item = self.db_tree.identify_row(event.y)
        if not item:
            return
        url = self.db_tree.item(item)["tags"][0]
        if not url or url == "N/A":
            return
        if col == "#5":
            vals = self.db_tree.item(item)["values"]
            new_val = vals[4] != "■"
            update_game_boolean(url, "has_demonic_vibe", new_val)
            g = next((x for x in self.db_games if x.url == url), None)
            if g:
                g.has_demonic_vibe = new_val
            self._apply_db_sort()
        elif col == "#6":
            vals = self.db_tree.item(item)["values"]
            new_val = vals[5] != "■"
            update_game_boolean(url, "owned", new_val)
            g = next((x for x in self.db_games if x.url == url), None)
            if g:
                g.owned = new_val
            self._apply_db_sort()
        elif col == "#7":
            webbrowser.open(url)

    def _on_search_tree_click(self, event: object) -> None:
        if self.search_tree.identify_region(event.x, event.y) != "cell" or self.search_tree.identify_column(event.x) != "#5":
            return
        item = self.search_tree.identify_row(event.y)
        if item:
            url = self.search_tree.item(item)["tags"][0]
            if url and url != "N/A":
                webbrowser.open(url)

    def _on_db_game_select(self, event: object) -> None:
        sel = self.db_tree.selection()
        if sel:
            url = self.db_tree.item(sel[0])["tags"][0]
            game = load_game(url)
            if game:
                GameDetailsWindow(self, game)

    def _on_search_game_select(self, event: object) -> None:
        sel = self.search_tree.selection()
        if sel:
            url = self.search_tree.item(sel[0])["tags"][0]
            game = next((g for g in self.current_games if g.url == url), None)
            if game:
                GameDetailsWindow(self, game)

    def on_closing(self) -> None:
        if self.caller:
            try:
                self.caller.close()
            except Exception:
                pass
        self.destroy()


def run_interface() -> None:
    """Run the GUI application."""
    app = TlamaCallerGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
