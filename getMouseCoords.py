import pyautogui
import time

# Optional: Add a small delay before starting to give you time to switch windows
print("Starting in 2 seconds...")
time.sleep(2)

try:
    while True:
        # Get the current mouse position
        x, y = pyautogui.position()
        print(f"Mouse coordinates: x={x}, y={y}")
        
        # Wait for 3 seconds
        time.sleep(3)

except KeyboardInterrupt:
    print("\nScript stopped by user")
