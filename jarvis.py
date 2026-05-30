import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import sys
import json
import ollama
import time
import math
import re
import tkinter as tk
from threading import Thread
from AppOpener import open as open_app 
from AppOpener import close as close_app

# --- UI Window Configuration ---
root = tk.Tk()
root.title("JARVIS Core")
root.geometry("400x400")
root.configure(bg="#05050a")
root.attributes("-topmost", True)  # Keeps Jarvis on top of other windows

# Create canvas for drawing the neon audio rings
canvas = tk.Canvas(root, width=400, height=400, bg="#05050a", highlightthickness=0)
canvas.pack()

# Visual state control variables
is_talking = False
animation_angle = 0

def draw_jarvis_core():
    """Draws and animates the sci-fi ring interface based on speech states"""
    global animation_angle, is_talking
    canvas.delete("all")
    
    center_x, center_y = 200, 200
    base_radius = 80
    
    # Calculate dynamic pulsing metrics if speaking
    if is_talking:
        pulse = math.sin(time.time() * 15) * 15
        radius = base_radius + pulse
    else:
        radius = base_radius

    # 1. Outer Static Tech Ring
    canvas.create_oval(center_x - 110, center_y - 110, center_x + 110, center_y + 110, 
                       outline="#102030", width=2, dash=(10, 15))
    
    # 2. Glowing Audio/Status Ring
    color = "#00f0ff" if is_talking else "#005577"
    glow_width = 5 if is_talking else 2
    
    canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, 
                       outline=color, width=glow_width)
    
    # 3. Rotating Core Segments (Arc Reactor style)
    if is_talking:
        animation_angle += 5
    else:
        animation_angle += 0.5
        
    for i in range(8):
        angle_offset = i * 45 + animation_angle
        rad_start = math.radians(angle_offset)
        rad_end = math.radians(angle_offset + 25)
        
        # Inner Dash Segments
        x1 = center_x + (radius - 20) * math.cos(rad_start)
        y1 = center_y + (radius - 20) * math.sin(rad_start)
        x2 = center_x + (radius - 20) * math.cos(rad_end)
        y2 = center_y + (radius - 20) * math.sin(rad_end)
        canvas.create_line(x1, y1, x2, y2, fill=color, width=3)

    # 4. Center Core Glow Node
    node_radius = 15 if is_talking else 10
    canvas.create_oval(center_x - node_radius, center_y - node_radius, 
                       center_x + node_radius, center_y + node_radius, 
                       fill=color, outline="")

    # Continuous loop render trigger
    root.after(20, draw_jarvis_core)

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
        "You are the brain of a voice assistant. Analyze the user's request. "
        "Respond ONLY with a JSON object containing 'action' and 'target'.\n\n"
        "RULES:\n"
        "1. If the user explicitly names a song title or artist to play (e.g., 'play darkside'), use action 'play_specific'.\n"
        "2. If they say 'play music' or 'resume music', use action 'play_song'.\n"
        "3. If they say 'stop the music', 'stop it', or 'pause', use action 'pause_song'.\n"
        "4. If they say 'next song' or 'skip', use action 'next_song'.\n"
        "5. If they say 'previous song' or 'go back', use action 'prev_song'.\n\n"
        "Allowed actions: 'open_app', 'close_app', 'open_web', 'play_song', 'play_specific', 'pause_song', 'next_song', 'prev_song', 'exit', 'chat'\n"
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
                time.sleep(2.5)
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.5)
                pyautogui.write(target, interval=0.05)
                time.sleep(1.5)
                for _ in range(5):
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

        # 8. Dynamic Web Opener
        elif action == "open_web":
            speak(f"Navigating to {target}.")
            webbrowser.open(target if target.startswith("http") else f"https://{target}")

        # 9. Exit Command
        elif action == "exit":
            speak("Goodbye, sir.")
            root.destroy() 
            sys.exit()
            
        # 🔥 10. OPTIMIZED: Streaming Fallback Chat Mode
        else:
            try:
                chat_prompt = (
                    "You are a spoken voice assistant named Jarvis. Answer the user's question clearly. "
                    "CRITICAL: Keep your answer incredibly brief (1-2 short sentences max). "
                    "Do NOT use markdown layout formatting like asterisks or bold text. "
                    "Do NOT use bullet points, lists, dashes, or emojis. Output only plain spoken English."
                )
                
                # Turn on streaming behavior at the local model runner context level
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
                    
                    # If the model completes a clean punctuation thought, vocalize it instantly
                    if any(punc in token for punc in ['.', '!', '?']):
                        # Clear unwanted artifacts out of the working buffer segment
                        clean_segment = sentence_buffer.replace("*", "").replace("-", "")
                        clean_segment = re.sub(r'[^\w\s\d.,!?\']', '', clean_segment).strip()
                        
                        if clean_segment:
                            print(clean_segment, end=" ", flush=True)
                            
                            # Trigger speech execution on the active thread worker loop
                            global is_talking
                            is_talking = True
                            engine = pyttsx3.init()
                            engine.say(clean_segment)
                            engine.runAndWait()
                            engine.stop()
                            is_talking = False
                            
                        sentence_buffer = "" # Flush the buffer segment
                print() # New line in console terminal
                
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