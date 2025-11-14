from website_caller import WebsiteCaller
from model.board_game import BoardGame

def main():
    # Use browser automation to execute JavaScript and wait for dynamic content
    caller = WebsiteCaller(timeout=30, use_browser=True)
    
    try:
        # caller.save_html(
        #     "https://www.tlamagames.com/", 
        #     "hra.html",
        #     output_dir="output",
        #     wait_for_selector="#fvStudio-component-topproduct")

        game_data = caller.get_text("https://www.tlamagames.com/deskove-hry/papyria/")
        board_game = BoardGame(game_data)
        print(board_game.final_price, board_game.distributor, board_game.min_players, board_game.max_players, board_game.play_time_minutes, board_game.bgg_rating, board_game.complexity, board_game.author, board_game.game_categories, board_game.game_mechanics, board_game.year_published, board_game.artists)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        caller.close()

if __name__ == "__main__":
    main()
