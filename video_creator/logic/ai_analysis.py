import cv2
from transformers import pipeline
import operator

# Initialize the emotion detector using a Hugging Face model.
# This model is loaded only once when the module is first imported.
try:
    print("Initializing PyTorch-based emotion detection model...")
    emotion_detector = pipeline("image-classification", model="dima806/facial_emotions_image_detection")
    print("Emotion detection model loaded successfully.")
except Exception as e:
    print(f"Failed to load emotion detection model: {e}")
    emotion_detector = None

def analyze_clip_emotion(clip_path: str) -> str:
    """
    Analyzes a video clip to determine the dominant emotion using a PyTorch-based model.

    Args:
        clip_path: The file path to the video clip.

    Returns:
        The dominant emotion (e.g., 'happy', 'sad', 'angry') or 'neutral' if no
        strong emotion is detected.
    """
    if not emotion_detector:
        print("Emotion detector is not available. Skipping analysis.")
        return "unknown"

    try:
        cap = cv2.VideoCapture(clip_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {clip_path}")
            return "unknown"

        # We'll analyze the middle frame of the clip for efficiency
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        middle_frame_index = frame_count // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_index)

        ret, frame = cap.read()
        cap.release()

        if not ret:
            print(f"Could not read the middle frame from {clip_path}")
            return "neutral"

        # Convert the frame to a format the model expects (RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get emotion predictions for the frame
        emotions = emotion_detector(frame_rgb)

        # The model returns a list of dicts like [{'label': 'happy', 'score': 0.9...}]
        if not emotions:
            print(f"No emotion detected in {clip_path}")
            return "neutral"

        # Find the emotion with the highest score
        dominant_emotion = max(emotions, key=lambda x: x['score'])

        # Normalize the label to lowercase
        emotion_label = dominant_emotion['label'].lower()

        print(f"Dominant emotion for {clip_path}: {emotion_label}")
        return emotion_label

    except Exception as e:
        print(f"An error occurred during emotion analysis for {clip_path}: {e}")
        return "unknown"