import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import sys
import json
import ollama
import time
import math
import datetime
import re
import tkinter as tk
from threading import Thread
from AppOpener import open as open_app 
from AppOpener import close as close_app

# --- UI Window Configuration ---
root = tk.Tk()
root.title("JARVIS Taskbar Core")

# 1. Strip away all borders, title bars, and window buttons cleanly
root.overrideredirect(True)

# 2. Force the accent bar to always stay on top of open application frames
root.attributes("-topmost", True)

# 3. Detect screen geometry metrics dynamically
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set bar height profile (4px) and line it up perfectly right above the default taskbar edge
bar_height = 4
y_position = screen_height - bar_height - 55  # Adjust the '40' offset if your taskbar is thinner/thicker

root.geometry(f"{screen_width}x{bar_height}+0+{y_position}")

# Create canvas for drawing the flat neon audio strip
canvas = tk.Canvas(root, width=screen_width, height=bar_height, bg="#05050a", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Visual state control variables
is_talking = False

def draw_jarvis_core():
    """Draws and animates the thin taskbar line based on speech engine states"""
    global is_talking
    canvas.delete("all")
    
    if is_talking:
        # Pulses bright cyberpunk neon cyan/purple when speaking
        pulse = abs(math.sin(time.time() * 12))
        # Smoothly interpolates lighting values to simulate breathing energy
        green_blue_glow = f"#{int(0 + (100 * pulse)):02x}f0ff"
        canvas.create_rectangle(0, 0, screen_width, bar_height, fill=green_blue_glow, outline="")
    else:
        # Dims down to a calm, deep stealth blue line when waiting in standby
        canvas.create_rectangle(0, 0, screen_width, bar_height, fill="#003344", outline="")
        
    # Standard frame loop update cadence
    root.after(30, draw_jarvis_core)

# --- Core Voice Engine Logic ---
def speak(text):
    global is_talking
    if not text.strip():
        return
        
    # Clean markdown, characters, and extra spacing structures safely
    cleaned_text = text.replace("*", "").replace("-", "").replace("#", "")
    cleaned_text = re.sub(r'[^\w\s\d.,!?\']', '', cleaned_text) 
    cleaned_text = " ".join(cleaned_text.split()) 
    
    if not cleaned_text.strip():
        return

    print(f"Jarvis: {cleaned_text}")
    
    is_talking = True
    try:
        engine = pyttsx3.init()
        engine.say(cleaned_text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Audio Error: {e}")
        
    is_talking = False

def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)
    try:
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"You said: {query}")
        return query.lower()
    except:
        return "none"

def ask_jarvis_brain(user_query):
    """Uses local Ollama model to break down your sentence into explicit actions"""
    system_prompt = (
        "You are the executive brain of an autonomous AI Agent named Jarvis. Analyze the request.\n"
        "Respond ONLY with a JSON object containing 'action' and 'target'. Do not include any extra text.\n\n"
        "RULES & CRITICAL MAPPINGS:\n"
        "1. If the user wants a screenshot, photo of screen, or to capture the screen, use action 'take_screenshot' and target 'none'.\n"
        "2. If the user wants to change volume, increase volume, make it louder, use 'volume_up'. If quieter or decrease, use 'volume_down'. Target is always 'none'.\n"
        "3. If the user wants to adjust brightness higher, use 'brightness_up'. If lower, use 'brightness_down'. Target is always 'none'.\n"
        "4. If the user wants to find, locate, or open a file they forgot, use action 'find_file' and make the filename the target.\n"
        "5. If the user wants to send a WhatsApp message, use action 'send_message' and format the target as 'NameOrNumber:Message'.\n"
        "6. If explicitly naming a music track to play, use action 'play_specific'.\n"
        "7. Generic music controls: 'play music' -> 'play_song', 'stop music' -> 'pause_song', 'next' -> 'next_song', 'back' -> 'prev_song'.\n\n"
        "Allowed actions: 'open_app', 'close_app', 'open_web', 'play_song', 'play_specific', 'pause_song', 'next_song', 'prev_song', 'find_file', 'send_message', 'take_screenshot', 'volume_up', 'volume_down', 'brightness_up', 'brightness_down', 'exit', 'chat'\n"
    )

    try:
        response = ollama.chat(
            model='gemma2:2b', 
            format='json',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_query}
            ]
        )
        raw_content = response['message']['content'].strip()
        return json.loads(raw_content)
    except Exception as e:
        return {"action": "chat", "target": "none"}

def main_assistant_loop():
    """Runs the main processing commands on a separate thread to avoid freezing the UI"""
    time.sleep(1) 
    speak("Local systems are online. What do you need, sir?")
    
    while True:
        query = listen_command()
        
        if query == "none":
            continue
            
        intent = ask_jarvis_brain(query)
        action = intent.get("action")
        target = intent.get("target")

        # 1. Dynamic App Opener
        if action == "open_app":
            speak(f"Opening {target}.")
            try: open_app(target, match_closest=True) 
            except: speak(f"I couldn't locate {target}.")

        # 2. Dynamic App Closer
        elif action == "close_app":
            speak(f"Closing {target} window, sir.")
            try: close_app(target, match_closest=True)
            except: speak(f"I couldn't terminate {target}.")

        # 3. Simple Play Music Command (Resume current queue)
        elif action == "play_song":
            speak("Resuming playback on Spotify, sir.")
            try:
                import pyautogui
                open_app("spotify", match_closest=True)
                time.sleep(1.5)
                pyautogui.press('playpause')
            except:
                speak("I encountered an issue driving the music client.")

        # 4. Play Specific Named Song
        elif action == "play_specific":
            speak(f"Searching for {target} on Spotify, sir.")
            try:
                import pyautogui
                open_app("spotify", match_closest=True)
                time.sleep(1.5)
                pyautogui.hotkey('ctrl', 'k')
                time.sleep(0.5)
                pyautogui.write(target, interval=0.05)
                time.sleep(1.5)
                for _ in range(4):
                    pyautogui.press('down')
                    time.sleep(0.1)
                pyautogui.press('enter')
            except:
                speak("I couldn't trigger that track line item.")

        # 5. Pause/Stop Music Command
        elif action == "pause_song":
            speak("Stopping the music, sir.")
            try:
                import pyautogui
                pyautogui.press('playpause')  
            except:
                speak("I couldn't pause the player.")

        # 6. Next Track Command
        elif action == "next_song":
            speak("Skipping to the next track, sir.")
            try:
                import pyautogui
                pyautogui.press('nexttrack')  
            except:
                speak("I couldn't skip forward.")

        # 7. Previous Track Command
        elif action == "prev_song":
            speak("Playing the previous track, sir.")
            try:
                import pyautogui
                pyautogui.press('prevtrack')  
            except:
                speak("I couldn't skip backward.")

        elif action == "take_screenshot":
            speak("Capturing screen frame, sir.")
            try:
                import pyautogui
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Screenshot_{timestamp}.png"
                
                # Takes a snapshot image and writes it directly to your project root folder
                screenshot = pyautogui.screenshot()
                screenshot.save(filename)
                speak(f"Screenshot successfully logged as {filename}.")
            except Exception as e:
                speak("I failed to capture the display image array.")

        # --- System Master Volume Hotkeys ---
        elif action == "volume_up":
            speak("Increasing master volume level, sir.")
            try:
                import pyautogui
                for _ in range(5):
                    pyautogui.press("volumeup")
            except: speak("I couldn't modify the master audio gain.")

        elif action == "volume_down":
            speak("Lowering audio volume level, sir.")
            try:
                import pyautogui
                for _ in range(5):
                    pyautogui.press("volumedown")
            except: speak("I couldn't adjust the master audio attenuation.")

        # --- Laptop Monitor Brightness Hotkeys ---
        elif action == "brightness_up":
            speak("Bumping display panel brightness, sir.")
            try:
                import pyautogui
                for _ in range(4):
                    pyautogui.press("brightnessup")
            except:
                speak("Hardware display panel modifications are currently restricted.")

        elif action == "brightness_down":
            speak("Dimming display panel brightness, sir.")
            try:
                import pyautogui
                for _ in range(4):
                    pyautogui.press("brightnessdown")
            except:
                speak("Hardware display panel modifications are currently restricted.")

        # 8. Dynamic Web Opener
        elif action == "open_web":
            speak(f"Navigating to {target}.")
            webbrowser.open(target if target.startswith("http") else f"https://{target}")

        # 9. Exit Command
        elif action == "exit":
            speak("Goodbye, sir.")
            root.destroy() 
            sys.exit()
            
        # 10. OPTIMIZED: Streaming Fallback Chat Mode
        else:
            try:
                chat_prompt = (
                    "You are a spoken voice assistant named Jarvis. Answer the user's question clearly. "
                    "CRITICAL: Keep your answer incredibly brief (1-2 short sentences max). "
                    "Do NOT use markdown layout formatting like asterisks or bold text. "
                    "Do NOT use bullet points, lists, dashes, or emojis. Output only plain spoken English."
                )
                
                response_stream = ollama.chat(
                    model='gemma2:2b', 
                    messages=[
                        {'role': 'system', 'content': chat_prompt},
                        {'role': 'user', 'content': query}
                    ],
                    stream=True
                )
                
                sentence_buffer = ""
                print("Jarvis: ", end="", flush=True)
                
                for chunk in response_stream:
                    token = chunk['message']['content']
                    sentence_buffer += token
                    
                    if any(punc in token for punc in ['.', '!', '?']):
                        clean_segment = sentence_buffer.replace("*", "").replace("-", "")
                        clean_segment = re.sub(r'[^\w\s\d.,!?\']', '', clean_segment).strip()
                        
                        if clean_segment:
                            print(clean_segment, end=" ", flush=True)
                            
                            global is_talking
                            is_talking = True
                            engine = pyttsx3.init()
                            engine.say(clean_segment)
                            engine.runAndWait()
                            engine.stop()
                            is_talking = False
                            
                        sentence_buffer = "" 
                print() 
                
            except Exception as e:
                print(f"Chat Error: {e}")
                speak("I encountered an internal error processing that doubt.")

# --- Execution Setup ---
if __name__ == "__main__":
    # Start the assistant processing loop inside a background worker thread
    assistant_thread = Thread(target=main_assistant_loop, daemon=True)
    assistant_thread.start()
    
    # Initialize the UI animation loop on the main frame thread
    draw_jarvis_core()
    root.mainloop()