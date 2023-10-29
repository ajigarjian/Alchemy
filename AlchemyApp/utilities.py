import re

def style_brackets(text):
    # Find text within square brackets and replace it with a contenteditable span having a data-placeholder value
    return re.sub(r'\[([^\]]+)\]', r'<span class="parameter-span bg-blue-100 text-gray-500 px-3 py-1 rounded-full" contenteditable="true" data-placeholder="\1">\1</span>', text)
