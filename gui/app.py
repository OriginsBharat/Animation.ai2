import customtkinter
from tkinter import filedialog
from api.image_search import search_for_character_images
from api.animation import generate_keyframe, interpolate_frames
from video.processing import create_animation_video
from PIL import Image
import requests
from io import BytesIO
import threading

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Puppet Animator")
        self.geometry("1280x720")

        self.reference_image = None
        self.animation_script = []
        self.background_image_path = None
        self.audio_path = None

        # Main layout
        self.grid_columnconfigure(0, weight=1) # Control panel
        self.grid_columnconfigure(1, weight=3) # Main content area
        self.grid_rowconfigure(0, weight=1)

        # === Left Control Panel ===
        self.control_frame = customtkinter.CTkScrollableFrame(self, width=350, corner_radius=0)
        self.control_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 2), pady=0)

        # --- Image Search Section ---
        self.search_label = customtkinter.CTkLabel(self.control_frame, text="1. Find Character", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.search_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        self.search_entry = customtkinter.CTkEntry(self.control_frame, placeholder_text="Enter character name...")
        self.search_entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.search_button = customtkinter.CTkButton(self.control_frame, text="Search for Images", command=self.on_search_button_click)
        self.search_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.selected_image_label = customtkinter.CTkLabel(self.control_frame, text="Selected Reference:")
        self.selected_image_label.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")
        self.selected_image_display = customtkinter.CTkLabel(self.control_frame, text="None", width=250, height=250)
        self.selected_image_display.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # --- Animation Script Section ---
        self.script_label = customtkinter.CTkLabel(self.control_frame, text="2. Create Animation Script", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.script_label.grid(row=5, column=0, padx=20, pady=(20, 10), sticky="w")
        self.pose_prompt_entry = customtkinter.CTkEntry(self.control_frame, placeholder_text="Describe the pose...")
        self.pose_prompt_entry.grid(row=6, column=0, padx=20, pady=5, sticky="ew")
        self.style_menu = customtkinter.CTkOptionMenu(self.control_frame, values=["detailed", "chibi"])
        self.style_menu.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
        self.duration_entry = customtkinter.CTkEntry(self.control_frame, placeholder_text="Duration (s)")
        self.duration_entry.grid(row=8, column=0, padx=20, pady=5, sticky="ew")
        self.add_pose_button = customtkinter.CTkButton(self.control_frame, text="Add Pose to Script", command=self.add_pose_to_script)
        self.add_pose_button.grid(row=9, column=0, padx=20, pady=10, sticky="ew")
        self.script_display = customtkinter.CTkTextbox(self.control_frame, height=150)
        self.script_display.grid(row=10, column=0, padx=20, pady=10, sticky="ew")
        self.script_display.insert("0.0", "Animation Script will appear here...")
        self.script_display.configure(state="disabled")

        # --- Assets Section ---
        self.assets_label = customtkinter.CTkLabel(self.control_frame, text="3. Add Assets (Optional)", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.assets_label.grid(row=11, column=0, padx=20, pady=(20, 10), sticky="w")
        self.audio_button = customtkinter.CTkButton(self.control_frame, text="Select Audio File", command=self.select_audio_file)
        self.audio_button.grid(row=12, column=0, padx=20, pady=10, sticky="ew")
        self.audio_label = customtkinter.CTkLabel(self.control_frame, text="Audio: None")
        self.audio_label.grid(row=13, column=0, padx=20, pady=5, sticky="w")
        self.lyrics_label = customtkinter.CTkLabel(self.control_frame, text="Lyrics (format: start_time,text)")
        self.lyrics_label.grid(row=14, column=0, padx=20, pady=(10, 5), sticky="w")
        self.lyrics_textbox = customtkinter.CTkTextbox(self.control_frame, height=100)
        self.lyrics_textbox.grid(row=15, column=0, padx=20, pady=5, sticky="ew")
        self.lyrics_textbox.insert("0.0", "0.5,Hello\n2.0,World!")


        # --- Render Section ---
        self.render_label = customtkinter.CTkLabel(self.control_frame, text="4. Generate Video", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.render_label.grid(row=16, column=0, padx=20, pady=(20, 10), sticky="w")
        self.render_button = customtkinter.CTkButton(self.control_frame, text="Generate Animation", command=self.start_generation_thread)
        self.render_button.grid(row=17, column=0, padx=20, pady=10, sticky="ew")
        self.status_label = customtkinter.CTkLabel(self.control_frame, text="Status: Idle")
        self.status_label.grid(row=18, column=0, padx=20, pady=10, sticky="w")


        # === Right Content Area ===
        self.content_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.results_label = customtkinter.CTkLabel(self.content_frame, text="Search Results / Video Preview", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.results_label.grid(row=0, column=0, pady=(20,10))
        self.results_frame = customtkinter.CTkScrollableFrame(self.content_frame, label_text="Click an image to select it as the reference")
        self.results_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    def select_audio_file(self):
        self.audio_path = filedialog.askopenfilename(title="Select Audio File", filetypes=(("Audio Files", "*.mp3 *.wav"), ("All files", "*.*")))
        if self.audio_path:
            filename = self.audio_path.split('/')[-1]
            self.audio_label.configure(text=f"Audio: {filename}")
            print(f"Selected audio file: {self.audio_path}")

    def parse_lyrics(self):
        lyrics_text = self.lyrics_textbox.get("1.0", "end-1c")
        overlays = []
        total_script_duration = sum(pose['duration'] for pose in self.animation_script) if self.animation_script else 0

        for line in lyrics_text.split('\n'):
            if ',' in line:
                try:
                    time_str, text = line.split(',', 1)
                    start_time = float(time_str)
                    # Simple heuristic for duration: last until next lyric or for 2s
                    overlays.append({'text': text.strip(), 'start': start_time, 'duration': 2})
                except ValueError:
                    print(f"Could not parse lyric line: {line}")
        # Adjust durations
        for i in range(len(overlays) - 1):
            overlays[i]['duration'] = overlays[i+1]['start'] - overlays[i]['start']
        if overlays and total_script_duration > 0 and overlays[-1]['start'] + overlays[-1]['duration'] > total_script_duration:
            overlays[-1]['duration'] = total_script_duration - overlays[-1]['start']
        return overlays

    def add_pose_to_script(self):
        prompt = self.pose_prompt_entry.get()
        style = self.style_menu.get()
        duration_str = self.duration_entry.get()
        if not prompt or not duration_str: return
        try:
            duration = float(duration_str)
        except ValueError: return
        self.animation_script.append({"prompt": prompt, "style": style, "duration": duration})
        self.update_script_display()
        self.pose_prompt_entry.delete(0, "end")
        self.duration_entry.delete(0, "end")

    def update_script_display(self):
        self.script_display.configure(state="normal")
        self.script_display.delete("1.0", "end")
        if not self.animation_script:
            self.script_display.insert("0.0", "Animation Script will appear here...")
        else:
            text = ""
            current_time = 0.0
            for i, pose in enumerate(self.animation_script):
                text += f"{i+1}. [{current_time:.1f}s-{(current_time + pose['duration']):.1f}s] ({pose['style']}): {pose['prompt']}\n"
                current_time += pose['duration']
            self.script_display.insert("0.0", text)
        self.script_display.configure(state="disabled")

    def start_generation_thread(self):
        self.status_label.configure(text="Status: Generating...")
        threading.Thread(target=self.run_animation_generation, daemon=True).start()

    def run_animation_generation(self):
        if not self.animation_script:
            print("Cannot generate: Animation script is empty.")
            self.status_label.configure(text="Status: Error - Script is empty")
            return

        # --- This is the main pipeline ---
        self.status_label.configure(text="Status: Generating keyframes...")
        keyframe_images = [generate_keyframe(p['prompt'], style_prompt=p['style']) for p in self.animation_script]
        if not all(keyframe_images):
            self.status_label.configure(text="Status: Error - Failed to generate keyframes")
            return

        self.status_label.configure(text="Status: Interpolating frames...")
        final_frames = []
        fps = 24
        for i in range(len(keyframe_images) - 1):
            num_steps = int(self.animation_script[i]['duration'] * fps)
            interpolated = interpolate_frames(keyframe_images[i], keyframe_images[i+1], num_steps)
            final_frames.extend(interpolated)
        final_frames.append(keyframe_images[-1]) # Add last frame

        self.status_label.configure(text="Status: Parsing lyrics...")
        text_overlays = self.parse_lyrics()

        self.status_label.configure(text="Status: Creating video file...")
        create_animation_video(final_frames, "animation_output.mp4", fps, self.audio_path, text_overlays)
        self.status_label.configure(text="Status: Done! Saved to animation_output.mp4")

    # --- Methods from previous step (need to be included in the final file) ---
    def on_search_button_click(self):
        query = self.search_entry.get()
        if not query: return
        self.status_label.configure(text=f"Status: Searching for {query}...")
        for widget in self.results_frame.winfo_children(): widget.destroy()
        try:
            image_urls = search_for_character_images(query)
            if not image_urls:
                customtkinter.CTkLabel(self.results_frame, text=f"No results found for '{query}'").pack(pady=10)
                self.status_label.configure(text="Status: No results found.")
                return
            self.status_label.configure(text="Status: Displaying results...")
            for i, url in enumerate(image_urls[:12]): # limit results
                response = requests.get(url, timeout=10)
                pil_image = Image.open(BytesIO(response.content))
                ctk_image = customtkinter.CTkImage(pil_image, size=(120, 120))
                img_button = customtkinter.CTkButton(self.results_frame, image=ctk_image, text="", width=120, height=120, command=lambda img=pil_image: self.select_image(img))
                img_button.pack(side="left", padx=5, pady=5, expand=True)
            self.status_label.configure(text="Status: Idle")
        except Exception as e:
            self.status_label.configure(text=f"Status: Error - {e}")

    def select_image(self, image: Image):
        self.reference_image = image
        display_image = customtkinter.CTkImage(image, size=(250, 250))
        self.selected_image_display.configure(image=display_image, text="")
        self.status_label.configure(text="Status: Reference image selected.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
