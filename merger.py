import os
import re

def combine_files(html_file):
    # Clean up the file path
    html_file = html_file.strip("'\"")

    # Extract directory and filename
    directory = os.path.dirname(html_file)
    filename = os.path.basename(html_file)
    base_name, ext = os.path.splitext(filename)

    # New file name with '_capp'
    new_file = os.path.join(directory, f"{base_name}_capp.html")

    # Read the original HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Find and replace CSS links
    css_links = re.findall(r'<link.*?href="([^"]*\.css)".*?>', html_content)
    for css_link in css_links:
        css_path = os.path.join(directory, css_link)
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as file:
                css_content = file.read()
            css_tag = f"<style>\n{css_content}\n</style>"
            html_content = html_content.replace(f'<link href="{css_link}" rel="stylesheet">', css_tag)

    # Find and replace JS script tags
    js_links = re.findall(r'<script.*?src="([^"]*\.js)".*?></script>', html_content)
    for js_link in js_links:
        js_path = os.path.join(directory, js_link)
        if os.path.exists(js_path):
            with open(js_path, 'r', encoding='utf-8') as file:
                js_content = file.read()
            js_tag = f"<script>\n{js_content}\n</script>"
            html_content = html_content.replace(f'<script src="{js_link}"></script>', js_tag)

    # Write the combined content to a new file
    with open(new_file, 'w', encoding='utf-8') as file:
        file.write(html_content)

    print(f"Combined HTML file created at: {new_file}")

def main():
    # Ask the user for the HTML file path
    html_file_path = input("Please enter the path to your HTML file: ")
    combine_files(html_file_path)

if __name__ == "__main__":
    main()
