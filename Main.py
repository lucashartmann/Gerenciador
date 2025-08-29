from view.App import GerenciadorApp

#pyinstaller  --add-data "view;view"  Main.py

if __name__ == "__main__":
    app = GerenciadorApp()
    app.run()