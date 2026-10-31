"""
run.py
-------
Single launcher for the Restaurant Management System.
Just run this file and choose whether you want the
Console version or the Window (GUI) version.

    python run.py
"""

import sys
import database as db


def main():
    db.init_db()
    print("=" * 55)
    print("   RESTAURANT MANAGEMENT SYSTEM - LAUNCHER")
    print("=" * 55)
    print("1. Console (Command Line) App")
    print("2. Window (GUI) App")
    print("0. Exit")
    choice = input("\nChoose an option: ").strip()

    if choice == "1":
        import console_app
        console_app.main_menu()
    elif choice == "2":
        try:
            import gui_app
        except ModuleNotFoundError:
            print("\n[Error] tkinter is not installed on this system.")
            print("Install it and try again (see requirements.txt for instructions).")
            sys.exit(1)
        app = gui_app.RestaurantApp()
        app.mainloop()
    elif choice == "0":
        print("Goodbye!")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
