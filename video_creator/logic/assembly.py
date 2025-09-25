import re

def parse_script(script: str) -> list:
    """
    Parses a script with emotional cues into a structured list.

    Args:
        script: The input script, e.g., "Hello world (HAPPY). How are you? (NEUTRAL)"

    Returns:
        A list of tuples, where each tuple is (dialogue, emotion).
        e.g., [('Hello world', 'happy'), ('How are you?', 'neutral')]
    """
    structured_script = []
    last_index = 0

    # Find all emotion cues, e.g., (HAPPY)
    matches = list(re.finditer(r'\((.*?)\)', script))

    for match in matches:
        # The text before the current match
        start, end = match.span()
        dialogue = script[last_index:start].strip()
        emotion = match.group(1).strip().lower()

        if dialogue:
            structured_script.append((dialogue, emotion))

        last_index = end

    # Handle any remaining text after the last match
    remaining_text = script[last_index:].strip()
    if remaining_text:
        structured_script.append((remaining_text, "neutral"))

    return structured_script

if __name__ == '__main__':
    test_script_1 = "So I texted my brother something the other day and he replied with THIS (SURPRISE). Subaa.. sybuuu?? So I texted on Google about what that is yeah bruh? And guess what HE WAS TELLING ME TO SHUT MY BITCH ASS UP! (ANGRY). But did I do it? Hehehehe no (HAPPY)."
    test_script_2 = "This is a simple test. (HAPPY)"
    test_script_3 = "This is a test without a final emotion."

    print("--- Testing Script Parser ---")

    print("\nTest Case 1:")
    parsed_1 = parse_script(test_script_1)
    for segment in parsed_1:
        print(f"  Dialogue: '{segment[0]}', Emotion: '{segment[1]}'")

    print("\nTest Case 2:")
    parsed_2 = parse_script(test_script_2)
    for segment in parsed_2:
        print(f"  Dialogue: '{segment[0]}', Emotion: '{segment[1]}'")

    print("\nTest Case 3:")
    parsed_3 = parse_script(test_script_3)
    for segment in parsed_3:
        print(f"  Dialogue: '{segment[0]}', Emotion: '{segment[1]}'")

    # Expected output for Test Case 1:
    # ('So I texted my brother something the other day and he replied with THIS', 'surprise')
    # ('. Subaa.. sybuuu?? So I texted on Google about what that is yeah bruh? And guess what HE WAS TELLING ME TO SHUT MY BITCH ASS UP!', 'angry')
    # ('. But did I do it? Hehehehe no', 'happy')
    # ('.', 'neutral')

    # Expected output for Test Case 2:
    # ('This is a simple test.', 'happy')

    # Expected output for Test Case 3:
    # ('This is a test without a final emotion.', 'neutral')