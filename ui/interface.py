"""
Graphical User Interface for Tlama Caller
A modern window-based interface for checking board game deals
"""
import customtkinter as ctk
from tkinter import ttk
import threading
from typing import Optional, List
import webbrowser
import platform

from website_caller import WebsiteCaller
from utils.search import search_for_game
from model.board_game import BoardGame
from database import get_all_games, search_games_in_db, get_game_count, load_game, update_game_boolean, save_game
from config import FILTERS, CATEGORY_FILTERS, MECHANIC_FILTERS, FILTER_GROUPS

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GameDetailsWindow(ctk.CTkToplevel):
    """Window to display detailed game information"""
    
    def __init__(self, parent, game: BoardGame):
        super().__init__(parent)
        self.game = game
        self.title(f"Game Details: {game.name}")
        self.geometry("800x700")
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            scroll_frame,
            text=self.game.name,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # URL button
        url_button = ctk.CTkButton(
            scroll_frame,
            text=f"🔗 {self.game.url}",
            command=lambda: webbrowser.open(self.game.url),
            fg_color="transparent",
            text_color="lightblue"
        )
        url_button.pack(pady=(0, 20))
        
        # Info frame
        info_frame = ctk.CTkFrame(scroll_frame)
        info_frame.pack(fill="x", pady=10)
        
        # Create info rows
        info_items = [
            ("💰 Price", f"{self.game.final_price} Kč" if self.game.final_price else "N/A"),
            ("📊 Your Rating", f"{self.game.my_rating:.1f}" if self.game.my_rating else "N/A"),
            ("⭐ BGG Rating", f"{self.game.bgg_rating:.1f} / 10" if self.game.bgg_rating else "N/A"),
            ("🏢 Distributor", self.game.distributor or "N/A"),
            ("📦 Type", self.game.game_type or "N/A"),
            ("👥 Players", f"{self.game.min_players}-{self.game.max_players}" if self.game.min_players and self.game.max_players else "N/A"),
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
        
        # Categories
        if self.game.game_categories:
            cat_text = ", ".join(self.game.game_categories)
            cat_label = ctk.CTkLabel(
                scroll_frame,
                text=f"🎯 Categories: {cat_text}",
                wraplength=700,
                justify="left"
            )
            cat_label.pack(pady=10, anchor="w")
        
        # Mechanics
        if self.game.game_mechanics:
            mech_text = ", ".join(self.game.game_mechanics)
            mech_label = ctk.CTkLabel(
                scroll_frame,
                text=f"⚙️ Mechanics: {mech_text}",
                wraplength=700,
                justify="left"
            )
            mech_label.pack(pady=10, anchor="w")
        
        # Send notification button
        if self.game.my_rating and self.game.my_rating > 140:
            notify_button = ctk.CTkButton(
                scroll_frame,
                text="🔔 Send OneSignal Notification",
                command=self._send_notification,
                fg_color="green"
            )
            notify_button.pack(pady=20)


class TlamaCallerGUI(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🎲 Tlama Games Deal Finder")
        self.geometry("1200x800")
        
        self.caller: Optional[WebsiteCaller] = None
        self.current_games: List[BoardGame] = []
        
        self._create_widgets()
        self._init_caller()
    
    def _init_caller(self):
        """Initialize website caller in background"""
        def init():
            self.caller = WebsiteCaller(timeout=30, use_browser=True)
            self.status_label.configure(text="✅ Ready")
        
        thread = threading.Thread(target=init, daemon=True)
        thread.start()
        self.status_label.configure(text="⏳ Initializing...")
    
    def _create_widgets(self):
        # Title bar with close button
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=0, pady=0)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🎲 Tlama Games Deal Finder",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=10)
        
        close_btn = ctk.CTkButton(
            title_frame,
            text="✕",
            width=30,
            height=30,
            command=self.on_closing,
            fg_color="transparent",
            hover_color="#c42b1c",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        close_btn.pack(side="right", padx=10, pady=5)
        
        # Status bar (create first so it's available for other methods)
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=20, pady=(0, 0))
        
        self.status_label = ctk.CTkLabel(status_frame, text="⏳ Initializing...")
        self.status_label.pack(side="left", padx=20, pady=10)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabs
        self.db_tab = self.tabview.add("📚 Database")
        self.search_tab = self.tabview.add("🔍 Search")
        
        # Sorting state for tables
        self.db_sort_column = None
        self.db_sort_direction = None  # None, "DESC", "ASC"
        self.db_games = []  # Store games for sorting
        
        self.search_sort_column = None
        self.search_sort_direction = None
        self.search_games = []  # Store games for sorting
        
        self._create_database_tab()
        self._create_search_tab()
    
    def _create_database_tab(self):
        """Create database browser tab"""
        # Top frame with controls
        top_frame = ctk.CTkFrame(self.db_tab)
        top_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(top_frame, text="Database Browser", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=10)
        
        rerate_btn = ctk.CTkButton(top_frame, text="⭐ Rerate All", command=self._rerate_all_games, 
                                    fg_color="#d97706", hover_color="#b45309")
        rerate_btn.pack(side="right", padx=10)
        
        refresh_btn = ctk.CTkButton(top_frame, text="🔄 Refresh", command=self._refresh_database)
        refresh_btn.pack(side="right", padx=10)
        
        # Search frame
        search_frame = ctk.CTkFrame(self.db_tab)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=10)
        self.db_search_entry = ctk.CTkEntry(search_frame, placeholder_text="Game name...")
        self.db_search_entry.pack(side="left", padx=10, fill="x", expand=True)
        
        db_search_btn = ctk.CTkButton(search_frame, text="Search", command=self._search_database)
        db_search_btn.pack(side="left", padx=10)
        
        # Games list frame
        list_frame = ctk.CTkFrame(self.db_tab)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Treeview for games
        columns = ("Name", "Price", "Rating", "BGG", "Evil", "Owned", "Link")
        self.db_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            # Link column is not sortable
            if col == "Link":
                self.db_tree.heading(col, text=col)
            else:
                self.db_tree.heading(col, text=col, command=lambda c=col: self._sort_db_table(c))
            self.db_tree.column(col, width=200)
        
        self.db_tree.column("Name", width=300)
        self.db_tree.column("Price", width=100)
        self.db_tree.column("Rating", width=100)
        self.db_tree.column("BGG", width=80)
        self.db_tree.column("Evil", width=60)
        self.db_tree.column("Owned", width=70)
        self.db_tree.column("Link", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.db_tree.yview)
        self.db_tree.configure(yscrollcommand=scrollbar.set)
        
        self.db_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.db_tree.bind("<Double-1>", self._on_db_game_select)
        self.db_tree.bind("<Button-1>", self._on_db_tree_click)
        self.db_tree.bind("<Motion>", self._on_db_tree_motion)
        self.db_tree.bind("<Leave>", lambda e: self.db_tree.configure(cursor=""))
        
        # Load initial data after a short delay to ensure everything is initialized
        self.after(100, self._refresh_database)
    
    def _create_search_tab(self):
        """Create search tab with dropdown-based filter selection"""
        # Top section: Dropdowns and selected filters
        top_frame = ctk.CTkFrame(self.search_tab)
        top_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(top_frame, text="Search Filters", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=10, pady=(0, 15))
        
        # Dropdowns frame - horizontal layout
        dropdowns_frame = ctk.CTkFrame(top_frame)
        dropdowns_frame.pack(fill="x", padx=10, pady=10)
        
        self.filter_vars = {}
        self.selected_filters = []  # Track selected filters as list of filter keys
        self.filter_dropdowns = {}  # Store dropdown widgets
        
        # Create dropdowns for each filter group
        row = 0
        col = 0
        max_cols = 3  # 3 dropdowns per row (label + dropdown = 2 columns each)
        
        # Regular filter groups
        for group_name, group_filters in FILTER_GROUPS.items():
            valid_filters = [f for f in group_filters if f in FILTERS]
            if not valid_filters:
                continue
            
            # Create dropdown with "Select..." placeholder
            dropdown_options = ["Select..."] + [f.replace("_", " ").title() for f in valid_filters]
            dropdown = ctk.CTkComboBox(
                dropdowns_frame,
                values=dropdown_options,
                command=lambda value, group=group_name, filters=valid_filters: self._on_filter_selected(value, group, filters),
                width=150
            )
            dropdown.set("Select...")
            
            label = ctk.CTkLabel(dropdowns_frame, text=f"{group_name}:", width=100, anchor="w")
            label.grid(row=row, column=col*2, padx=5, pady=5, sticky="w")
            dropdown.grid(row=row, column=col*2+1, padx=5, pady=5, sticky="w")
            
            self.filter_dropdowns[group_name] = dropdown
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Categories dropdown
        if CATEGORY_FILTERS:
            cat_options = ["Select..."] + [f.replace("_", " ").title() for f in CATEGORY_FILTERS]
            cat_dropdown = ctk.CTkComboBox(
                dropdowns_frame,
                values=cat_options,
                command=lambda value, filters=CATEGORY_FILTERS: self._on_category_selected(value, filters),
                width=150
            )
            cat_dropdown.set("Select...")
            
            cat_label = ctk.CTkLabel(dropdowns_frame, text="Category:", width=100, anchor="w")
            cat_label.grid(row=row, column=col*2, padx=5, pady=5, sticky="w")
            cat_dropdown.grid(row=row, column=col*2+1, padx=5, pady=5, sticky="w")
            
            self.filter_dropdowns["Category"] = cat_dropdown
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Mechanics dropdown
        if MECHANIC_FILTERS:
            mech_options = ["Select..."] + [f.replace("_", " ").title() for f in MECHANIC_FILTERS]
            mech_dropdown = ctk.CTkComboBox(
                dropdowns_frame,
                values=mech_options,
                command=lambda value, filters=MECHANIC_FILTERS: self._on_mechanic_selected(value, filters),
                width=150
            )
            mech_dropdown.set("Select...")
            
            mech_label = ctk.CTkLabel(dropdowns_frame, text="Mechanic:", width=100, anchor="w")
            mech_label.grid(row=row, column=col*2, padx=5, pady=5, sticky="w")
            mech_dropdown.grid(row=row, column=col*2+1, padx=5, pady=5, sticky="w")
            
            self.filter_dropdowns["Mechanic"] = mech_dropdown
        
        # Selected filters display area
        selected_frame = ctk.CTkFrame(top_frame)
        selected_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(selected_frame, text="Selected Filters:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.selected_filters_frame = ctk.CTkFrame(selected_frame)
        self.selected_filters_frame.pack(fill="x", padx=10, pady=5)
        
        # Clear all button
        clear_btn = ctk.CTkButton(
            selected_frame,
            text="Clear All",
            command=self._clear_all_filters,
            width=100,
            fg_color="gray",
            height=30
        )
        clear_btn.pack(anchor="e", padx=10, pady=5)
        
        # Search button - add it right after selected filters
        search_btn_frame = ctk.CTkFrame(top_frame)
        search_btn_frame.pack(fill="x", padx=10, pady=15)
        
        search_btn = ctk.CTkButton(
            search_btn_frame,
            text="🔍 Search Games",
            command=self._search_games,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        search_btn.pack(pady=10)
        
        # Progress bar frame
        self.progress_frame = ctk.CTkFrame(top_frame)
        self.progress_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="", font=ctk.CTkFont(size=12))
        self.progress_label.pack(anchor="w", padx=10, pady=(5, 0))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=600)
        self.progress_bar.pack(fill="x", padx=10, pady=(5, 10))
        self.progress_bar.set(0)
        
        # Initially hide progress bar
        self.progress_frame.pack_forget()
        
        # Results frame - create it here, not in _clear_all_filters
        results_frame = ctk.CTkFrame(self.search_tab)
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Name", "Price", "Rating", "BGG", "Link")
        self.search_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            # Link column is not sortable
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
    
    def _on_filter_selected(self, value, group_name, valid_filters):
        """Handle filter selection from dropdown"""
        if value == "Select...":
            return
        
        # Find the filter key from the display name
        filter_key = None
        for f in valid_filters:
            if f.replace("_", " ").title() == value:
                filter_key = f
                break
        
        if filter_key and filter_key not in self.selected_filters:
            self.selected_filters.append(filter_key)
            self._update_selected_filters_display()
    
    def _on_category_selected(self, value, valid_filters):
        """Handle category selection"""
        if value == "Select...":
            return
        
        filter_key = None
        for f in valid_filters:
            if f.replace("_", " ").title() == value:
                filter_key = f"cat:{f}"
                break
        
        if filter_key and filter_key not in self.selected_filters:
            self.selected_filters.append(filter_key)
            self._update_selected_filters_display()
    
    def _on_mechanic_selected(self, value, valid_filters):
        """Handle mechanic selection"""
        if value == "Select...":
            return
        
        filter_key = None
        for f in valid_filters:
            if f.replace("_", " ").title() == value:
                filter_key = f"mech:{f}"
                break
        
        if filter_key and filter_key not in self.selected_filters:
            self.selected_filters.append(filter_key)
            self._update_selected_filters_display()
    
    def _update_selected_filters_display(self):
        """Update the display of selected filters as tags"""
        # Clear existing tags
        for widget in self.selected_filters_frame.winfo_children():
            widget.destroy()
        
        if not self.selected_filters:
            label = ctk.CTkLabel(self.selected_filters_frame, text="No filters selected", fg_color="transparent", text_color="gray")
            label.pack(anchor="w", padx=10, pady=5)
            return
        
        # Display filters as tags in a flow layout
        row = 0
        col = 0
        max_cols = 6
        
        for filter_key in self.selected_filters:
            # Create tag frame
            tag_frame = ctk.CTkFrame(self.selected_filters_frame, fg_color="#1f538d", corner_radius=10)
            
            # Get display name
            if filter_key.startswith("cat:"):
                display_name = filter_key.replace("cat:", "").replace("_", " ").title()
                prefix = "📁"
            elif filter_key.startswith("mech:"):
                display_name = filter_key.replace("mech:", "").replace("_", " ").title()
                prefix = "⚙️"
            else:
                display_name = filter_key.replace("_", " ").title()
                prefix = "🏷️"
            
            tag_label = ctk.CTkLabel(tag_frame, text=f"{prefix} {display_name}", font=ctk.CTkFont(size=11))
            tag_label.pack(side="left", padx=8, pady=3)
            
            # Remove button
            remove_btn = ctk.CTkButton(
                tag_frame,
                text="×",
                width=20,
                height=20,
                command=lambda fk=filter_key: self._remove_filter(fk),
                fg_color="transparent",
                hover_color="#c42b1c",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            remove_btn.pack(side="left", padx=(0, 5))
            
            tag_frame.grid(row=row, column=col, padx=5, pady=5, sticky="w")
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def _remove_filter(self, filter_key):
        """Remove a filter from selection"""
        if filter_key in self.selected_filters:
            self.selected_filters.remove(filter_key)
            self._update_selected_filters_display()
            # Reset the corresponding dropdown
            self._reset_dropdown_for_filter(filter_key)
    
    def _reset_dropdown_for_filter(self, filter_key):
        """Reset the dropdown that corresponds to a filter"""
        # Find which dropdown this filter belongs to
        for group_name, group_filters in FILTER_GROUPS.items():
            if filter_key in group_filters:
                if group_name in self.filter_dropdowns:
                    self.filter_dropdowns[group_name].set("Select...")
                return
        
        if filter_key.startswith("cat:") and "Category" in self.filter_dropdowns:
            self.filter_dropdowns["Category"].set("Select...")
        elif filter_key.startswith("mech:") and "Mechanic" in self.filter_dropdowns:
            self.filter_dropdowns["Mechanic"].set("Select...")
    
    def _clear_all_filters(self):
        """Clear all selected filters"""
        self.selected_filters.clear()
        self._update_selected_filters_display()
        # Reset all dropdowns
        for dropdown in self.filter_dropdowns.values():
            dropdown.set("Select...")
    
    def _refresh_database(self):
        """Refresh database view"""
        self.db_tree.delete(*self.db_tree.get_children())
        
        try:
            games = get_all_games(limit=1000)
            self.db_games = games  # Store for sorting
            count = get_game_count()
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=f"📚 Database: {count} games")
            
            # Apply current sort if any
            self._apply_db_sort()
        except Exception as err:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=f"❌ Error: {err}")
    
    def _apply_db_sort(self):
        """Apply current sort to database table"""
        self.db_tree.delete(*self.db_tree.get_children())
        
        games = self.db_games.copy()
        
        if self.db_sort_column and self.db_sort_direction:
            games = self._sort_games(games, self.db_sort_column, self.db_sort_direction)
        
        for game in games:
            self.db_tree.insert("", "end", values=(
                game.name or "N/A",
                f"{game.final_price} Kč" if game.final_price else "N/A",
                f"{game.my_rating:.1f}" if game.my_rating else "N/A",
                f"{game.bgg_rating:.1f}" if game.bgg_rating else "N/A",
                "☑" if getattr(game, 'has_demonic_vibe', False) else "☐",
                "☑" if getattr(game, 'owned', False) else "☐",
                "🔗 Open" if game.url else "N/A"
            ), tags=(game.url,))
    
    def _sort_db_table(self, column):
        """Sort database table by column"""
        # Cycle: None -> DESC -> ASC -> None
        if self.db_sort_column != column:
            self.db_sort_column = column
            self.db_sort_direction = "DESC"
        elif self.db_sort_direction == "DESC":
            self.db_sort_direction = "ASC"
        elif self.db_sort_direction == "ASC":
            self.db_sort_column = None
            self.db_sort_direction = None
        
        # Update header indicators
        self._update_db_headers()
        
        # Apply sort
        self._apply_db_sort()
    
    def _update_db_headers(self):
        """Update database table headers with sort indicators"""
        columns = ("Name", "Price", "Rating", "BGG", "Evil", "Owned", "Link")
        for col in columns:
            text = col
            if col == self.db_sort_column:
                if self.db_sort_direction == "DESC":
                    text = f"{col} ▼"
                elif self.db_sort_direction == "ASC":
                    text = f"{col} ▲"
            self.db_tree.heading(col, text=text)
    
    def _rerate_all_games(self):
        """Rerate all games in the database"""
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.configure(text="⏳ Loading games for rerating...")
        
        def rerate():
            try:
                # Get all games
                games = get_all_games(limit=None)
                total = len(games)
                
                if total == 0:
                    self.after(0, lambda: self.status_label.configure(text="⚠️ No games found in database"))
                    return
                
                self.after(0, lambda: self.status_label.configure(text=f"⭐ Rerating {total} games..."))
                
                updated_count = 0
                for idx, game in enumerate(games, 1):
                    # Load the game (this will recalculate the rating)
                    reloaded_game = load_game(game.url)
                    if reloaded_game:
                        # Save it back (save_game will save the new rating)
                        save_game(reloaded_game)
                        updated_count += 1
                    
                    # Update status every 10 games or on last game
                    if idx % 10 == 0 or idx == total:
                        self.after(0, lambda i=idx, t=total: 
                                  self.status_label.configure(text=f"⭐ Rerating: {i}/{t} games..."))
                
                # Refresh the display
                self.after(0, lambda: self._refresh_database())
                self.after(0, lambda: self.status_label.configure(
                    text=f"✅ Rerated {updated_count} games successfully"))
            except Exception as err:
                error_msg = str(err)
                self.after(0, lambda msg=error_msg: self.status_label.configure(text=f"❌ Error: {msg}"))
        
        thread = threading.Thread(target=rerate, daemon=True)
        thread.start()
    
    def _search_database(self):
        """Search database by name"""
        self.db_tree.delete(*self.db_tree.get_children())
        
        search_term = self.db_search_entry.get().strip()
        
        try:
            if search_term:
                games = search_games_in_db(name=search_term, limit=500)
            else:
                games = get_all_games(limit=500)
            
            self.db_games = games  # Store for sorting
            
            # Apply current sort if any
            self._apply_db_sort()
            
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=f"📚 Found {len(games)} games")
        except Exception as err:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=f"❌ Error: {err}")
    
    def _search_games(self):
        """Search games online with selected filters"""
        if not self.caller:
            self.status_label.configure(text="⏳ Please wait, initializing...")
            return
        
        # Use selected_filters list instead of filter_vars
        selected_filters = self.selected_filters.copy()
        
        if not selected_filters:
            self.status_label.configure(text="⚠️ Please select at least one filter")
            return
        
        self.status_label.configure(text=f"🔍 Searching with {len(selected_filters)} filters...")
        self.search_tree.delete(*self.search_tree.get_children())
        
        # Show progress bar
        self.progress_frame.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting search...")
        
        def progress_callback(stage, current, total, message):
            """Update progress bar from search thread"""
            if stage == "pages":
                # Stage 1: Fetching pages - show indeterminate progress (0-20%)
                # We don't know total pages, so show a pulsing effect
                self.after(0, lambda: self.progress_label.configure(text=message))
                # Pulse the progress bar between 0 and 0.2 (20%)
                current_progress = self.progress_bar.get()
                if current_progress >= 0.18:
                    self.after(0, lambda: self.progress_bar.set(0.02))
                else:
                    self.after(0, lambda: self.progress_bar.set(current_progress + 0.02))
            elif stage == "pages_complete":
                # Transition between stages - set to 20%
                self.after(0, lambda: self.progress_bar.set(0.2))
                self.after(0, lambda: self.progress_label.configure(text=message))
            elif stage == "games":
                # Stage 2: Fetching games - show actual progress (20-100%)
                if total and total > 0:
                    progress = current / total
                    # Scale from 0.2 to 1.0 (since pages took 0-20%, games take 20-100%)
                    scaled_progress = 0.2 + (progress * 0.8)
                    self.after(0, lambda p=scaled_progress: self.progress_bar.set(p))
                    self.after(0, lambda m=message: self.progress_label.configure(text=m))
        
        def search():
            try:
                games = search_for_game(self.caller, filters=selected_filters, progress_callback=progress_callback)
                self.current_games = games
                
                # Hide progress bar and show results
                self.after(0, lambda: self.progress_frame.pack_forget())
                self.after(0, lambda: self._display_search_results(games))
            except Exception as err:
                error_msg = str(err)
                self.after(0, lambda: self.progress_frame.pack_forget())
                self.after(0, lambda msg=error_msg: self.status_label.configure(text=f"❌ Error: {msg}"))
        
        thread = threading.Thread(target=search, daemon=True)
        thread.start()
    
    def _display_search_results(self, games: List[BoardGame]):
        """Display search results in treeview"""
        self.search_tree.delete(*self.search_tree.get_children())
        
        # Store games for sorting (limit to 100)
        self.search_games = games[:100]
        
        # Apply current sort if any
        self._apply_search_sort()
        
        self.status_label.configure(text=f"✅ Found {len(games)} games")
    
    def _apply_search_sort(self):
        """Apply current sort to search table"""
        self.search_tree.delete(*self.search_tree.get_children())
        
        games = self.search_games.copy()
        
        if self.search_sort_column and self.search_sort_direction:
            games = self._sort_games(games, self.search_sort_column, self.search_sort_direction)
        
        for game in games:
            self.search_tree.insert("", "end", values=(
                game.name or "N/A",
                f"{game.final_price} Kč" if game.final_price else "N/A",
                f"{game.my_rating:.1f}" if game.my_rating else "N/A",
                f"{game.bgg_rating:.1f}" if game.bgg_rating else "N/A",
                "🔗 Open" if game.url else "N/A"
            ), tags=(game.url,))
    
    def _sort_search_table(self, column):
        """Sort search table by column"""
        # Cycle: None -> DESC -> ASC -> None
        if self.search_sort_column != column:
            self.search_sort_column = column
            self.search_sort_direction = "DESC"
        elif self.search_sort_direction == "DESC":
            self.search_sort_direction = "ASC"
        elif self.search_sort_direction == "ASC":
            self.search_sort_column = None
            self.search_sort_direction = None
        
        # Update header indicators
        self._update_search_headers()
        
        # Apply sort
        self._apply_search_sort()
    
    def _update_search_headers(self):
        """Update search table headers with sort indicators"""
        columns = ("Name", "Price", "Rating", "BGG", "Link")
        for col in columns:
            text = col
            if col == self.search_sort_column:
                if self.search_sort_direction == "DESC":
                    text = f"{col} ▼"
                elif self.search_sort_direction == "ASC":
                    text = f"{col} ▲"
            self.search_tree.heading(col, text=text)
    
    def _sort_games(self, games: List[BoardGame], column: str, direction: str) -> List[BoardGame]:
        """Sort games list by column and direction"""
        def get_sort_key(game):
            if column == "Name":
                return (game.name or "").lower()
            elif column == "Price":
                # Ensure numeric sorting - use final_price as integer, default to 0
                price = game.final_price
                if price is None:
                    return 0
                # Convert to int if it's not already, handle string prices if any
                try:
                    return int(float(price))
                except (ValueError, TypeError):
                    return 0
            elif column == "Rating":
                return game.my_rating if game.my_rating else 0
            elif column == "BGG":
                return game.bgg_rating if game.bgg_rating else 0
            elif column == "Evil":
                return 1 if getattr(game, 'has_demonic_vibe', False) else 0
            elif column == "Owned":
                return 1 if getattr(game, 'owned', False) else 0
            # Link column should not be sortable, but handle it just in case
            elif column == "Link":
                return game.url or ""
            return ""
        
        sorted_games = sorted(games, key=get_sort_key, reverse=(direction == "DESC"))
        return sorted_games
    
    def _format_game_info(self, game: BoardGame, title: str) -> str:
        """Format game information as text"""
        info = f"{title}\n{'='*60}\n\n"
        info += f"Name: {game.name}\n"
        info += f"URL: {game.url}\n\n"
        
        if game.final_price:
            info += f"Price: {game.final_price} Kč\n"
        if game.my_rating:
            info += f"Your Rating: {game.my_rating:.1f}\n"
        if game.bgg_rating:
            info += f"BGG Rating: {game.bgg_rating:.1f} / 10\n"
        if game.distributor:
            info += f"Distributor: {game.distributor}\n"
        if game.min_players and game.max_players:
            info += f"Players: {game.min_players}-{game.max_players}\n"
        if game.play_time_minutes:
            info += f"Play Time: {game.play_time_minutes} min\n"
        if game.complexity:
            info += f"Complexity: {game.complexity:.1f} / 5\n"
        if game.game_categories:
            info += f"\nCategories: {', '.join(game.game_categories)}\n"
        if game.game_mechanics:
            info += f"Mechanics: {', '.join(game.game_mechanics)}\n"
        
        return info
    
    def _on_db_tree_motion(self, event):
        """Change cursor to pointer when hovering over clickable columns"""
        # Use platform-appropriate pointer cursor
        pointer_cursor = "pointinghand" if platform.system() == "Darwin" else "hand2"
        region = self.db_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.db_tree.identify_column(event.x)
            item = self.db_tree.identify_row(event.y)
            if item:
                url = self.db_tree.item(item)['tags'][0]
                if url and url != "N/A":
                    # Evil (#5), Owned (#6), or Link (#7) columns are clickable
                    if column in ["#5", "#6", "#7"]:
                        self.db_tree.configure(cursor=pointer_cursor)
                        return
        self.db_tree.configure(cursor="")
    
    def _on_search_tree_motion(self, event):
        """Change cursor to pointer when hovering over Link column"""
        # Use platform-appropriate pointer cursor
        pointer_cursor = "pointinghand" if platform.system() == "Darwin" else "hand2"
        region = self.search_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.search_tree.identify_column(event.x)
            if column == "#5":  # Link column (5th column, 1-indexed)
                item = self.search_tree.identify_row(event.y)
                if item:
                    url = self.search_tree.item(item)['tags'][0]
                    if url and url != "N/A":
                        self.search_tree.configure(cursor=pointer_cursor)
                        return
        self.search_tree.configure(cursor="")
    
    def _on_db_tree_click(self, event):
        """Handle clicks on database tree, toggle checkboxes or open link"""
        region = self.db_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.db_tree.identify_column(event.x)
            item = self.db_tree.identify_row(event.y)
            if not item:
                return
            
            url = self.db_tree.item(item)['tags'][0]
            if not url or url == "N/A":
                return
            
            # Column indices: Name=#1, Price=#2, Rating=#3, BGG=#4, Evil=#5, Owned=#6, Link=#7
            if column == "#5":  # Evil column
                # Toggle has_demonic_vibe - get current value from tree, don't reload game
                item_values = self.db_tree.item(item)['values']
                current_value = item_values[4] == "☑"  # Evil is 5th column (index 4)
                new_value = not current_value
                update_game_boolean(url, 'has_demonic_vibe', new_value)
                # Update the game object in our stored list
                game = next((g for g in self.db_games if g.url == url), None)
                if game:
                    game.has_demonic_vibe = new_value
                self._apply_db_sort()  # Refresh display without reloading from DB
            elif column == "#6":  # Owned column
                # Toggle owned - get current value from tree, don't reload game
                item_values = self.db_tree.item(item)['values']
                current_value = item_values[5] == "☑"  # Owned is 6th column (index 5)
                new_value = not current_value
                update_game_boolean(url, 'owned', new_value)
                # Update the game object in our stored list
                game = next((g for g in self.db_games if g.url == url), None)
                if game:
                    game.owned = new_value
                self._apply_db_sort()  # Refresh display without reloading from DB
            elif column == "#7":  # Link column
                # Open link in browser
                if url and url != "N/A":
                    webbrowser.open(url)
    
    def _on_search_tree_click(self, event):
        """Handle clicks on search tree, open link if Link column clicked"""
        region = self.search_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.search_tree.identify_column(event.x)
            if column == "#5":  # Link column (5th column, 1-indexed)
                item = self.search_tree.identify_row(event.y)
                if item:
                    url = self.search_tree.item(item)['tags'][0]
                    if url and url != "N/A":
                        webbrowser.open(url)
    
    def _on_db_game_select(self, event):
        """Handle database game selection"""
        selection = self.db_tree.selection()
        if selection:
            item = self.db_tree.item(selection[0])
            url = item['tags'][0]
            game = load_game(url)
            if game:
                GameDetailsWindow(self, game)
    
    def _on_search_game_select(self, event):
        """Handle search game selection"""
        selection = self.search_tree.selection()
        if selection:
            item = self.search_tree.item(selection[0])
            url = item['tags'][0]
            # Find game in current_games
            game = next((g for g in self.current_games if g.url == url), None)
            if game:
                GameDetailsWindow(self, game)
    
    def on_closing(self):
        """Handle window closing"""
        # Try to close the caller, but don't block if it fails
        # (browser context might be in a different thread)
        if self.caller:
            try:
                self.caller.close()
            except Exception:
                # If closing fails (e.g., thread issues), just continue
                # The browser will be cleaned up when the process exits
                pass
        self.destroy()


def run_interface():
    """Run the GUI application"""
    app = TlamaCallerGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    run_interface()

