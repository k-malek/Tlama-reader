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

        game_data = caller.get_text("https://www.tlamagames.com/deskove-hry/cestou-pokroku/")
        board_game = BoardGame(game_data)

        board_game.print_info()
        print(board_game.rate())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        caller.close()

if __name__ == "__main__":
    main()
