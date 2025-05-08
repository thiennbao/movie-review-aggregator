import json
import re
from typing import List, Dict

def split_by_punctuation(text: str) -> List[str]:
    """
    Split the text into segments at any punctuation mark.
    Args:
        text: The string of text to be split.
    Returns:
        A list of normalized segments.
    """
    # Split at punctuation marks: , . ! ? ; : or ...
    pattern = r'[,.!?;]|\.\.\.'
    segments = re.split(pattern, text)
    # Remove extra whitespace and empty segments
    segments = [seg.strip() for seg in segments if seg.strip()]
    return segments

def add_content_to_aspects(review: Dict) -> Dict:
    """
    Add a 'content' field to each aspect, where content is the segment containing the term.
    Args:
        review: A dictionary containing review information, including the sentence and aspects.
    Returns:
        The updated dictionary with a 'content' field for each aspect.
    """
    sentence = review["review"]
    
    # Split the sentence into segments at punctuation marks
    segments = split_by_punctuation(sentence)
    
    # Iterate through each aspect
    for aspect in review["aspects"]:
        term = aspect["term"]
        position = aspect.get("position", {})
        start_pos = position.get("start", -1)
        end_pos = position.get("end", -1)
        
        # Find the segment containing the term
        found_content = ""
        for seg in segments:
            # Check if the term is in the segment (case-insensitive)
            if re.search(re.escape(term), seg, re.IGNORECASE):
                # If position is provided, verify if the term is in the correct segment based on position
                if start_pos != -1 and end_pos != -1:
                    # Find the starting position of the segment in the original sentence
                    seg_start = sentence.find(seg)
                    if seg_start <= start_pos < seg_start + len(seg):
                        found_content = seg
                        break
                else:
                    # If no position is provided, take the first segment containing the term
                    found_content = seg
                    break
        
        # Assign the content to the aspect
        aspect["content"] = found_content if found_content else ""
        if not found_content:
            print(f"No segment found containing '{term}' in review: {sentence[:50]}...")
    
    return review