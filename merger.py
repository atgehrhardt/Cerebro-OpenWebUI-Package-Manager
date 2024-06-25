import os
import re
import sys

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def merge_files(path):
    # Remove any surrounding quotes from the path
    path = path.strip("'\"")
    
    try:
        if os.path.isfile(path) and path.lower().endswith('.html'):
            html_file = path
            directory = os.path.dirname(path)
        elif os.path.isdir(path):
            directory = path
            html_file = None
            for filename in os.listdir(directory):
                if filename.lower().endswith('.html'):
                    html_file = os.path.join(directory, filename)
                    break
        else:
            print(f"Error: '{path}' is neither a valid HTML file nor a directory.")
            print(f"File exists: {os.path.exists(path)}")
            print(f"Is file: {os.path.isfile(path)}")
            print(f"Is directory: {os.path.isdir(path)}")
            return

        if not html_file:
            print("No HTML file found.")
            return

        html_content = read_file(html_file)
        if html_content is None:
            return

        css_content = ""
        js_content = ""

        # Find and read CSS and JS files
        for filename in os.listdir(directory):
            if filename.lower().endswith('.css'):
                content = read_file(os.path.join(directory, filename))
                if content:
                    css_content += content
            elif filename.lower().endswith('.js'):
                content = read_file(os.path.join(directory, filename))
                if content:
                    js_content += content

        # Replace CSS link with inline styles
        html_content = re.sub(
            r'<link\s+rel="stylesheet"\s+href="[^"]*"\s*/>',
            f'<style>{css_content}</style>',
            html_content
        )

        # Replace JS script tag with inline script
        html_content = re.sub(
            r'<script\s+src="[^"]*"\s*></script>',
            f'<script>{js_content}</script>',
            html_content
        )

        # Generate output filename
        base_name = os.path.basename(html_file)
        name_without_ext = os.path.splitext(base_name)[0]
        output_filename = f"{name_without_ext}_capp.html"
        output_file = os.path.join(directory, output_filename)

        # Write the merged content to the new file
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(html_content)
            print(f"Merged file created: {output_file}")
        except IOError as e:
            print(f"Error writing merged file: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    path = input("Please enter the path to your HTML file or the directory containing your HTML, CSS, and JS files: ").strip()
    merge_files(path)