from django.shortcuts import render

# Create your views here.
import os
import easyocr
import google.generativeai as genai
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)


reader = easyocr.Reader(['en'])

def extract_text_and_feedback(image_path):
    text = "\n".join(reader.readtext(image_path, detail=0))
    prompt = f"Explain this text in simple and clear language:\n{text}"
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return text, format_text(response.text)

def home(request):
    if request.method == "POST" and request.FILES.get("screenshot"):
        uploaded = request.FILES["screenshot"]
        fs = FileSystemStorage()
        filename = fs.save(uploaded.name, uploaded)
        image_path = fs.path(filename)
        image_url = fs.url(filename)

        text, feedback = extract_text_and_feedback(image_path)

        return render(request, "index.html", {
            "image_url": image_url,
            "text": text,
            "feedback": feedback,
        })

    return render(request, "index.html")


import re

def format_text(text):
    lines = text.split("\n")
    html_output = []
    in_list = False

    for line in lines:
        line = line.strip()

        # Heading (lines starting with numbers or **)
        if re.match(r"^\*\*(.+?)\*\*$", line):
            content = re.findall(r"\*\*(.+?)\*\*", line)[0]
            html_output.append(f"<h2 class='text-xl font-bold mt-4'>{content}</h2>")

        elif re.match(r"^(\d+\.)", line):
            html_output.append(f"<h3 class='text-lg font-semibold mt-4'>{line}</h3>")

        # Bullet list
        elif line.startswith("* "):
            if not in_list:
                html_output.append("<ul class='list-disc pl-6 mt-2'>")
                in_list = True
            content = line[2:].strip()
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", content)
            html_output.append(f"<li class='mb-1'>{content}</li>")

        # End of list
        elif not line and in_list:
            html_output.append("</ul>")
            in_list = False

        # Paragraphs or normal lines
        elif line:
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
            html_output.append(f"<p class='mb-2'>{line}</p>")

    # Close open list
    if in_list:
        html_output.append("</ul>")

    return "\n".join(html_output)