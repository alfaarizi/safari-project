from my_safari_project.view.main_menu_gui import main_menu
from my_safari_project.view.gamegui import GameGUI

def run_game():
    main_menu()

if __name__ == "__main__":
    run_game()
    controller = GameGUI()
    controller.run()
