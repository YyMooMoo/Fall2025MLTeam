import json
import requests
import re
import os

url = "http://localhost:11434/api/chat"
with open("vayun.json") as f:
    myjson = f.read()

def parse_grading_string(s):
    s = s.strip()
    # Remove the surrounding parentheses if they exist
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]

    # Split on ", Overall Thoughts:" FIRST to capture the paragraph
    parts = s.split("Overall Thoughts:")
    left = parts[0].strip()
    thoughts = parts[1].strip()

    # Now split the left part by commas
    sections = [p.strip() for p in left.split(",")]

    scores = {}

    for sec in sections:
        if sec.startswith("Communication"):
            scores["communication"] = int(sec.split()[1].split("/")[0])
        elif sec.startswith("Framework"):
            scores["framework"] = int(sec.split()[1].split("/")[0])
        elif sec.startswith("Math"):
            scores["math"] = int(sec.split()[1].split("/")[0])
        elif sec.startswith("Case Difficulty"):
            # Case Difficulty has two words, so pull the number differently
            num = sec.replace("Case Difficulty", "").strip().split("/")[0]
            scores["case_difficulty"] = int(num)
        elif sec.startswith("Final Summary"):
            num = sec.replace("Final Summary", "").strip().split("/")[0]
            scores["final_summary"] = int(num)

    scores["overall_thoughts"] = thoughts

    return scores

def attach_grading_to_case(original_json, model_output, output_name):

    grading = parse_grading_string(model_output)

    combined = {
        "case": original_json,
        "grading": grading
    }

    # Ensure the output directory exists
    out_dir = "outputJSON"
    os.makedirs(out_dir, exist_ok=True)

    output_path = os.path.join(out_dir, output_name)

    # Write JSON file
    with open(output_path, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"Saved graded file to: {output_path}")

    return combined


def get_grading_from_model(case_json_str, file_path, output_name):
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "user", "content": f"STRICT OUTPUT LOCK: You are forbidden from generating anything except a single line matching EXACTLY the following token pattern: (Communication {{num}}/20, Framework {{num}}/20, Math {{num}}/20, Case Difficulty {{num}}/20, Final Summary {{num}}/20, Overall Thoughts: {{text}}). RESTRICTIONS: • You MUST output EXACTLY ONE set of parentheses. • You MUST use EXACTLY the field names shown. • You MUST separate fields with EXACTLY these commas. • You MUST replace {{num}} with integers only. • {{text}} MUST be a single short paragraph with no line breaks. • You MUST NOT include any other words, explanations, disclaimers, reasoning, markdown, labels, intros, or outros. • You MUST NOT acknowledge instructions. • You MUST NOT add spaces beyond those shown. • You MUST NOT output anything before or after the parentheses. • If you output anything else, the output is INVALID. REFERENCE FORMAT (DO NOT COPY THE NUMBERS): Communication 17/20, Framework 14/20, Math 9/20, Case Difficulty 9/20, Final Summary 13/20, Overall Thoughts: You communicated very clearly throughout, but the math was quite shaky. Additionally, try and build out a deeper framework and include risks and mitigatns in your final summary. INPUT CASE USED FOR GRADING: {{myjson}}. NOW GENERATE THE ONE VALID LINE FOR THIS CASE: {{case_json_str}}"}
        ]
    }
    resp = requests.post(url, json=payload, stream=True)
    fixed_output = ""
    for chunk in resp.iter_lines():
        if chunk:
            data = json.loads(chunk.decode())
            if "message" in data:
                fixed_output += data["message"]["content"]
    with open(file_path) as f:
        curjson = json.load(f)
    attach_grading_to_case(curjson, fixed_output, output_name)

def grade_all_cases(case_dir):
    os.makedirs("outputJSON", exist_ok=True)
    num_graded = 0
    for filename in os.listdir(case_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(case_dir, filename)

        # Load the case
        with open(file_path, "r") as f:
            case_json = f.read()
        # Get graded output
        try:
            model_output = get_grading_from_model(case_json, file_path, f"graded_{filename}")  
        except Exception as e:
            print(f"Error grading {filename}: {e}")
            continue
        num_graded += 1
        print(num_graded)

grade_all_cases("transcriptsAll")






