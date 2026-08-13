#!/usr/bin/env python3
import sys
import json
import re
import urllib.request
import os

def extract_spoken_part(text):
    if not text:
        return ""
    
    # 1. Check for explicit spoken tag pattern: [SPEAK]: or [SPOKEN]: or [VOICE]:
    match = re.search(r'(?:\[SPEAK\]|\[SPOKEN\]|\[VOICE\]):\s*(.*)', text, re.IGNORECASE | re.DOTALL)
    if match:
        # Stop at any double newlines inside the tag to keep it short
        tag_content = match.group(1).split("\n\n")[0].strip()
        return tag_content
    
    # 2. Check for HTML comment speaker block: <!-- speak: ... -->
    html_match = re.search(r'<!--\s*(?:speak|spoken)\s*:\s*(.*?)\s*-->', text, re.IGNORECASE | re.DOTALL)
    if html_match:
        return html_match.group(1).strip()

    # 3. Fallback: Parse paragraphs and take the first conversational sentences
    paragraphs = text.split("\n\n")
    for p in paragraphs:
        p = p.strip()
        # Skip empty paragraphs, headers, tables, lists, or code blocks
        if not p or p.startswith("#") or p.startswith("|") or p.startswith("```") or p.startswith("diff"):
            continue
        
        # Strip list bullets if the paragraph starts with a list bullet
        p = re.sub(r'^[-*+•\s]|\d+\.\s*', '', p).strip()
        
        # Split into sentences and take the first two sentences
        sentences = re.split(r'(?<=[.!?])\s+', p)
        spoken_sentences = []
        for s in sentences:
            s = s.strip()
            if s:
                spoken_sentences.append(s)
            if len(spoken_sentences) >= 2:
                break
        
        if spoken_sentences:
            return " ".join(spoken_sentences)
            
    return ""

def clean_markdown(text):
    if not text:
        return ""
    # Remove image links: ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Convert markdown links: [text](url) -> text
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Remove code blocks and inline code ticks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = text.replace('`', '')
    # Remove formatting asterisks
    text = text.replace('*', '')
    return text.strip()

def main():
    # Read the hook context from stdin
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        # Always output valid empty JSON on failure to avoid blocking
        print("{}")
        return

    transcript_path = payload.get("transcriptPath")
    if not transcript_path or not os.path.exists(transcript_path):
        print("{}")
        return

    # Find the last completion message in the transcript
    content_to_speak = ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Traverse backwards to find the last planner response with content
        for line in reversed(lines):
            try:
                step = json.loads(line)
                if step.get("type") == "PLANNER_RESPONSE" and step.get("content"):
                    content_to_speak = step.get("content")
                    break
            except Exception:
                continue
    except Exception:
        pass

    if content_to_speak:
        spoken_part = extract_spoken_part(content_to_speak)
        clean_text = clean_markdown(spoken_part)
        if clean_text:
            # Check for duplicate playback to prevent double-speaking on hook loop suspension
            last_spoken_path = os.path.expanduser("~/.jarvis/last_spoken.txt")
            try:
                os.makedirs(os.path.dirname(last_spoken_path), exist_ok=True)
                if os.path.exists(last_spoken_path):
                    with open(last_spoken_path, "r", encoding="utf-8") as lf:
                        if lf.read().strip() == clean_text:
                            print("{}")
                            return
                with open(last_spoken_path, "w", encoding="utf-8") as lf:
                    lf.write(clean_text)
            except Exception:
                pass

            # Post to the local TTS server on port 20129
            try:
                data = json.dumps({"text": clean_text}).encode("utf-8")
                req = urllib.request.Request(
                    "http://localhost:20129/speak",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    response.read()
            except Exception:
                # Silently fail if TTS server is offline
                pass

    # Return success response to the Agent hook system
    print("{}")

if __name__ == "__main__":
    import os
    main()
