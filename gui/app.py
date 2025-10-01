import customtkinter
from tkinter import filedialog
import threading
import os
import sys
import subprocess
import shutil
from PIL import Image

# Import the corrected and improved API functions
from api.video_search import get_video_info_list, download_videos_from_list, find_and_extract_expressive_clips
from api.audio import create_final_audio, OUTPUTS_PATH as AUDIO_OUTPUT_PATH
from api.video_assembly import assemble_video

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Anime Dubbing App v2 (Stylized)")
        self.geometry("1280x720")

        # --- App State Variables ---
        self.voice_sample_path = None
        self.background_music_path = None
        self.selected_clips = []
        self.clip_buttons = {}
        self.final_video_path = None

        # State for the new, efficient video search
        self.video_info_cache = []
        self.current_search_query = ""
        self.current_page = 0
        self.clips_per_page = 3

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # ============================
        # === Left Control Panel ===
        # ============================
        self.control_frame = customtkinter.CTkScrollableFrame(self, width=350, corner_radius=0)
        self.control_frame.grid(row=0, column=0, sticky="nsew")
        self.control_frame.grid_columnconfigure(0, weight=1)

        # --- Inputs Section ---
        self.inputs_label = customtkinter.CTkLabel(self.control_frame, text="1. Add Your Inputs", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.inputs_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.voice_button = customtkinter.CTkButton(self.control_frame, text="Upload Voice Sample", command=self.upload_voice_sample)
        self.voice_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.voice_label = customtkinter.CTkLabel(self.control_frame, text="Voice: None", text_color="gray")
        self.voice_label.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="w")

        self.music_button = customtkinter.CTkButton(self.control_frame, text="Upload Background Music", command=self.select_background_music)
        self.music_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.music_label = customtkinter.CTkLabel(self.control_frame, text="Music: None", text_color="gray")
        self.music_label.grid(row=4, column=0, padx=20, pady=(0, 5), sticky="w")

        self.trim_label = customtkinter.CTkLabel(self.control_frame, text="Trim Music (start/end in sec):")
        self.trim_label.grid(row=5, column=0, padx=20, pady=(5,0), sticky="w")
        self.trim_frame = customtkinter.CTkFrame(self.control_frame, fg_color="transparent")
        self.trim_frame.grid(row=6, column=0, padx=20, pady=(0,10), sticky="ew")
        self.trim_frame.columnconfigure((0,1), weight=1)
        self.trim_start_entry = customtkinter.CTkEntry(self.trim_frame, placeholder_text="0")
        self.trim_start_entry.grid(row=0, column=0, padx=(0,5), sticky="ew")
        self.trim_end_entry = customtkinter.CTkEntry(self.trim_frame, placeholder_text="end")
        self.trim_end_entry.grid(row=0, column=1, padx=(5,0), sticky="ew")

        self.script_textbox = customtkinter.CTkTextbox(self.control_frame, height=200)
        self.script_textbox.grid(row=7, column=0, padx=20, pady=(10, 10), sticky="ew")
        self.script_textbox.insert("0.0", "Enter your script here...")

        # --- Video Clip Search Section ---
        self.search_label = customtkinter.CTkLabel(self.control_frame, text="2. Find Video Clips", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.search_label.grid(row=8, column=0, padx=20, pady=(20, 10), sticky="w")
        self.search_entry = customtkinter.CTkEntry(self.control_frame, placeholder_text="Enter character name...")
        self.search_entry.grid(row=9, column=0, padx=20, pady=10, sticky="ew")
        self.search_button = customtkinter.CTkButton(self.control_frame, text="Search for Clips", command=self.on_search_button_click)
        self.search_button.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        # --- Effects Section ---
        self.effects_label = customtkinter.CTkLabel(self.control_frame, text="3. Add Effects", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.effects_label.grid(row=11, column=0, padx=20, pady=(20, 10), sticky="w")
        self.effects_switch = customtkinter.CTkSwitch(self.control_frame, text="Apply Rounded Frame & Filter", onvalue=True, offvalue=False)
        self.effects_switch.grid(row=12, column=0, padx=20, pady=10, sticky="w")
        self.effects_switch.select()

        # --- Generate Section ---
        self.render_label = customtkinter.CTkLabel(self.control_frame, text="4. Generate Video", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.render_label.grid(row=13, column=0, padx=20, pady=(20, 10), sticky="w")
        self.render_button = customtkinter.CTkButton(self.control_frame, text="Generate Video", command=self.start_generation_thread)
        self.render_button.grid(row=14, column=0, padx=20, pady=10, sticky="ew")
        self.status_label = customtkinter.CTkLabel(self.control_frame, text="Status: Idle", anchor="w")
        self.status_label.grid(row=15, column=0, padx=20, pady=10, sticky="ew")
        self.progressbar = customtkinter.CTkProgressBar(self.control_frame, mode='determinate')
        self.progressbar.grid(row=16, column=0, padx=20, pady=(0,10), sticky="ew")
        self.progressbar.set(0)

        # ============================
        # === Right Content Area ===
        # ============================
        self.content_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.tab_view = customtkinter.CTkTabview(self.content_frame)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tab_view.add("Clip Gallery")
        self.tab_view.add("Preview & Edit")

        self.gallery_container = customtkinter.CTkFrame(self.tab_view.tab("Clip Gallery"), fg_color="transparent")
        self.gallery_container.pack(expand=True, fill="both")
        self.gallery_container.grid_rowconfigure(0, weight=1)
        self.gallery_container.grid_columnconfigure(0, weight=1)

        self.gallery_frame = customtkinter.CTkScrollableFrame(self.gallery_container, label_text="Search results will appear here.")
        self.gallery_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.load_more_button = customtkinter.CTkButton(self.gallery_container, text="Load More Clips", command=self.on_load_more_click, state="disabled")
        self.load_more_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.preview_frame = customtkinter.CTkFrame(self.tab_view.tab("Preview & Edit"), fg_color="transparent")
        self.preview_frame.pack(expand=True, fill="both", padx=10, pady=10)
        self.preview_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.preview_frame.grid_rowconfigure(1, weight=1)

        self.preview_label = customtkinter.CTkLabel(self.preview_frame, text="Video preview will be available here after generation.", font=customtkinter.CTkFont(size=14))
        self.preview_label.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        self.subtitle_editor = customtkinter.CTkTextbox(self.preview_frame, height=200, state="disabled")
        self.subtitle_editor.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.play_button = customtkinter.CTkButton(self.preview_frame, text="Play Video", command=self.play_final_video, state="disabled")
        self.play_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.rerender_button = customtkinter.CTkButton(self.preview_frame, text="Update Subtitles", command=self.rerender_video, state="disabled")
        self.rerender_button.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.save_as_button = customtkinter.CTkButton(self.preview_frame, text="Save As...", command=self.save_as, state="disabled")
        self.save_as_button.grid(row=2, column=2, padx=10, pady=10, sticky="ew")

    def upload_voice_sample(self):
        path = filedialog.askopenfilename(title="Select Voice Sample", filetypes=(("Audio Files", "*.mp3 *.wav"),))
        if path:
            self.voice_sample_path = path
            self.voice_label.configure(text=f"Voice: {os.path.basename(path)}", text_color="white")

    def select_background_music(self):
        path = filedialog.askopenfilename(title="Select Background Music", filetypes=(("Audio Files", "*.mp3 *.wav"),))
        if path:
            self.background_music_path = path
            self.music_label.configure(text=f"Music: {os.path.basename(path)}", text_color="white")

    def on_search_button_click(self):
        query = self.search_entry.get()
        if not query:
            return self.update_status("Status: Please enter a character name.")

        self.current_search_query = query
        self.current_page = 0
        for widget in self.gallery_frame.winfo_children(): widget.destroy()
        self.selected_clips.clear()
        self.clip_buttons.clear()

        self.update_status("Status: Fetching video list from YouTube...")
        self.search_button.configure(state="disabled")
        threading.Thread(target=self.run_get_video_list, daemon=True).start()

    def run_get_video_list(self):
        self.video_info_cache = get_video_info_list(self.current_search_query)
        self.after(0, self.search_button.configure, state="normal")
        if not self.video_info_cache:
            self.after(0, self.update_status, f"Status: No videos found for '{self.current_search_query}'.")
        else:
            self.after(0, self.update_status, "Status: Video list fetched. Ready to load clips.")
            self.after(0, self.load_more_button.configure, state="normal")
            self.after(0, self.on_load_more_click)

    def on_load_more_click(self):
        start_index = self.current_page * self.clips_per_page
        end_index = start_index + self.clips_per_page

        if start_index >= len(self.video_info_cache):
            self.update_status("Status: No more videos to load.")
            self.load_more_button.configure(state="disabled")
            return

        videos_to_process = self.video_info_cache[start_index:end_index]
        self.current_page += 1

        self.update_status(f"Status: Downloading and processing page {self.current_page}...")
        self.progressbar.configure(mode='indeterminate')
        self.progressbar.start()
        self.search_button.configure(state="disabled")
        self.load_more_button.configure(state="disabled")
        threading.Thread(target=self.run_clip_extraction, args=(videos_to_process,), daemon=True).start()

    def run_clip_extraction(self, video_entries):
        downloaded_paths = download_videos_from_list(video_entries)
        extracted_clips = find_and_extract_expressive_clips(downloaded_paths)
        self.after(0, self.update_gallery, extracted_clips)

    def update_gallery(self, clip_paths):
        self.progressbar.stop()
        self.progressbar.configure(mode='determinate')
        self.search_button.configure(state="normal")
        self.load_more_button.configure(state="normal")

        if not clip_paths:
            self.update_status(f"Status: No expressive clips found on this page.")
        else:
            self.update_status(f"Status: Found {len(clip_paths)} new clips.")

        for clip_path in clip_paths:
            thumbnail_path = self.generate_thumbnail(clip_path)
            if thumbnail_path:
                pil_image = Image.open(thumbnail_path)
                ctk_image = customtkinter.CTkImage(pil_image, size=(160, 90))
                btn = customtkinter.CTkButton(self.gallery_frame, image=ctk_image, text="", width=160, height=90, fg_color="transparent", border_width=2, border_color="gray", command=lambda p=clip_path: self.toggle_clip_selection(p))
                btn.pack(side="left", padx=10, pady=10, expand=True)
                self.clip_buttons[clip_path] = btn

    def generate_thumbnail(self, video_path):
        try:
            from moviepy.editor import VideoFileClip
            thumbnail_dir = "thumbnails"
            os.makedirs(thumbnail_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            thumbnail_path = os.path.join(thumbnail_dir, f"{base_name}.jpg")
            if not os.path.exists(thumbnail_path):
                with VideoFileClip(video_path) as clip:
                    clip.save_frame(thumbnail_path, t=min(0.5, clip.duration - 0.1))
            return thumbnail_path
        except Exception as e:
            print(f"Error generating thumbnail for {video_path}: {e}")
            return None

    def toggle_clip_selection(self, clip_path):
        if clip_path in self.selected_clips:
            self.selected_clips.remove(clip_path)
            self.clip_buttons[clip_path].configure(border_color="gray")
        else:
            self.selected_clips.append(clip_path)
            self.clip_buttons[clip_path].configure(border_color="#3498db")

    def start_generation_thread(self):
        self.update_status("Status: Starting generation...")
        self.progressbar.set(0)
        self.render_button.configure(state="disabled")
        threading.Thread(target=self.run_video_generation, daemon=True).start()

    def run_video_generation(self):
        script_text = self.script_textbox.get("1.0", "end-1c")
        if not all([self.voice_sample_path, script_text, self.selected_clips]):
            return self.after(0, self.update_status_and_reenable, "Status: Error - Missing voice, script, or selected clips.")

        trim_start = float(self.trim_start_entry.get() or 0)
        trim_end_str = self.trim_end_entry.get() or "None"
        trim_end = float(trim_end_str) if trim_end_str.lower() != "none" else None

        self.after(0, lambda: self.progressbar.set(0.1))
        self.after(0, self.update_status, "Status: Generating audio...")
        final_audio_path = create_final_audio(script_text, self.voice_sample_path, self.background_music_path, trim_start, trim_end)
        if not final_audio_path:
            return self.after(0, self.update_status_and_reenable, "Status: Error - Audio generation failed.")

        self.after(0, lambda: self.progressbar.set(0.5))
        self.after(0, self.update_status, "Status: Assembling video...")
        apply_fx = self.effects_switch.get()
        self.final_video_path = assemble_video(self.selected_clips, final_audio_path, script_text, apply_effects=apply_fx)
        if not self.final_video_path:
            return self.after(0, self.update_status_and_reenable, "Status: Error - Video assembly failed.")

        self.after(0, lambda: self.progressbar.set(1))
        self.after(0, self.update_status, f"Status: Done! Video saved to {self.final_video_path}")
        self.after(0, self.setup_preview_tab, script_text)
        self.after(0, self.render_button.configure, state="normal")

    def setup_preview_tab(self, script_to_edit):
        self.preview_label.configure(text=f"Video generated! Edit subtitles below or save.")
        self.subtitle_editor.configure(state="normal")
        self.subtitle_editor.delete("1.0", "end")
        self.subtitle_editor.insert("1.0", script_to_edit)
        for btn in [self.play_button, self.rerender_button, self.save_as_button]:
            btn.configure(state="normal")
        self.tab_view.set("Preview & Edit")

    def play_final_video(self):
        if not self.final_video_path or not os.path.exists(self.final_video_path): return
        if sys.platform == "win32": os.startfile(self.final_video_path)
        elif sys.platform == "darwin": subprocess.Popen(["open", self.final_video_path])
        else: subprocess.Popen(["xdg-open", self.final_video_path])

    def rerender_video(self):
        new_script = self.subtitle_editor.get("1.0", "end-1c")
        final_audio_path = os.path.join(AUDIO_OUTPUT_PATH, "final_audio.mp3")
        if not new_script or not os.path.exists(final_audio_path):
            return self.update_status("Status: Error - Missing script or audio for re-render.")
        self.update_status("Status: Re-rendering with new subtitles...")
        self.progressbar.configure(mode='indeterminate')
        self.progressbar.start()
        apply_fx = self.effects_switch.get()
        threading.Thread(target=self.run_rerender_thread, args=(new_script, final_audio_path, apply_fx), daemon=True).start()

    def run_rerender_thread(self, script, audio_path, apply_fx):
        self.final_video_path = assemble_video(self.selected_clips, audio_path, script, apply_effects=apply_fx)
        self.progressbar.stop()
        self.progressbar.configure(mode='determinate')
        if not self.final_video_path:
            self.after(0, self.update_status, "Status: Error - Failed to re-render video.")
        else:
            self.after(0, self.update_status, "Status: Re-render complete!")

    def save_as(self):
        if not self.final_video_path or not os.path.exists(self.final_video_path): return
        save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")], title="Save Video As...")
        if save_path:
            try:
                self.update_status(f"Status: Saving video to {save_path}...")
                shutil.copy(self.final_video_path, save_path)
                self.update_status(f"Status: Video successfully saved!")
            except Exception as e:
                self.update_status(f"Status: Error saving file - {e}")

    def update_status_and_reenable(self, text):
        self.update_status(text)
        self.render_button.configure(state="normal")

    def update_status(self, text):
        self.status_label.configure(text=text)
        if self.progressbar.cget("mode") == 'indeterminate':
            self.progressbar.stop()
            self.progressbar.configure(mode='determinate')

if __name__ == "__main__":
    app = App()
    app.mainloop()