from pynput.mouse import Controller, Listener
import re
import threading

mouse = Controller()
locked_position = (0, 0)  # default until first input
lock_enabled = True

def keep_mouse_locked():
    """Listener that snaps the mouse back if moved manually."""
    def on_move(x, y):
        if lock_enabled:
            mouse.position = locked_position
    def on_click(x, y, button, pressed):
        if lock_enabled:
            mouse.position = locked_position
    return Listener(on_move=on_move, on_click=on_click)

def coordinate_input():
    global locked_position, lock_enabled
    print("Mouse locked. Type coordinates like '500 300' (x y).")
    print("Type 'exit' to quit.")
    while True:
        coords = input("Enter coordinates: ").strip()
        if coords.lower() == "exit":
            lock_enabled = False
            break

        match = re.match(r"^(\d+)\s+(\d+)$", coords)
        if match:
            x, y = map(int, match.groups())
            locked_position = (x, y)
            mouse.position = locked_position
            print(f"Moved mouse to: {x}, {y}")
        else:
            print("Invalid input. Use format: x y")

if __name__ == "__main__":
    # Start mouse listener in background
    with keep_mouse_locked() as listener:
        coordinate_input()
        listener.stop()