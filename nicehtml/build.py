import re

def format_css_inline(css_string):
    styles = []
    for part in css_string.split(','):
        if ':' in part:
            key, value = part.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key == "size":
                key = "font-size"
            styles.append(f"{key}: {value}")
    return "; ".join(styles)

def format_css_properties(css_block):
    lines = css_block.strip().splitlines()
    props = []
    for line in lines:
        if ':' in line or ';' in line:
            props.append(line.strip())
        else:
            parts = line.strip().split()
            if len(parts) == 2:
                props.append(f"{parts[0]}: {parts[1]};")
    return ' '.join(props)

def convert_nh_to_html(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        code = f.read()

    head_elements = []

    # <title>
    title_match = re.search(r'<title>(.*?)</title>', code, flags=re.DOTALL)
    title_html = f"<title>{title_match.group(1).strip()}</title>" if title_match else "<title>NH Page</title>"
    head_elements.append(title_html)

    # <css href="..."/>
    css_links = re.findall(r'<css href="(.*?)"\s*/?>', code)
    for href in css_links:
        head_elements.append(f'<link rel="stylesheet" href="{href}">')

    # <js src="..."/>
    js_links = re.findall(r'<js src="(.*?)"\s*/?>', code)
    for src in js_links:
        head_elements.append(f'<script src="{src}"></script>')

    # internal <css>...</css>
    internal_css_match = re.search(r'<css>(.*?)</css>', code, flags=re.DOTALL)
    if internal_css_match:
        raw_css = internal_css_match.group(1).strip()
        formatted_css = re.sub(
            r'(\S+)\s*\{(.*?)\}',
            lambda m: f".{m.group(1).strip()} {{{format_css_properties(m.group(2))}}}",
            raw_css,
            flags=re.DOTALL
        )
        head_elements.append(f"<style>\n{formatted_css}\n</style>")

    body = code

    # <txt css="class">...</txt>
    body = re.sub(
        r'<txt(?:\s+css="(.*?)")?>(.*?)</txt>',
        lambda m: f'<p class="{m.group(1)}">{m.group(2)}</p>' if m.group(1) else f'<p>{m.group(2)}</p>',
        body,
        flags=re.DOTALL
    )

    # <prompt>...</prompt>
    body = re.sub(r'<prompt>(.*?)</prompt>', r'<label>\1 <input type="text" placeholder="\1"></label>', body)

    # <header>...</header>
    body = re.sub(r'<header>(.*?)</header>', r'<h1>\1</h1>', body)
    body = re.sub(r'<subheader>(.*?)</subheader>', r'<h2>\1</h2>', body)

    # <img w="..." height="..." src="..." alt="..." />
    body = re.sub(
        r'<img\s+w="(.*?)"\s+height="(.*?)"\s+src="(.*?)"\s+alt="(.*?)"\s*/?>',
        r'<img width="\1" height="\2" src="\3" alt="\4">',
        body
    )

    # <btn css='...'>...</btn>
    body = re.sub(
        r'<btn(?:\s+css=[\'"](.*?)[\'"])?>(.*?)</btn>',
        lambda m: f'<button style="{format_css_inline(m.group(1))}">{m.group(2)}</button>' if m.group(1) else f'<button>{m.group(2)}</button>',
        body
    )

    # <br />
    body = re.sub(r'<br\s*/?>', r'<br>', body)

    # <list>...</list>
    body = re.sub(r'<list>(.*?)</list>', r'<ul>\1</ul>', body, flags=re.DOTALL)
    body = re.sub(r'<li>(.*?)</li>', r'<li>\1</li>', body)

    # <box>...</box>
    body = re.sub(r'<box>(.*?)</box>', r'<div class="box">\1</div>', body)

    # <footer>...</footer>
    body = re.sub(r'<footer>(.*?)</footer>', r'<footer>\1</footer>', body)

    # Remove tags handled separately
    body = re.sub(r'<title>.*?</title>', '', body, flags=re.DOTALL)
    body = re.sub(r'<css href=".*?"\s*/?>', '', body)
    body = re.sub(r'<js src=".*?"\s*/?>', '', body)
    body = re.sub(r'<css>.*?</css>', '', body, flags=re.DOTALL)

    # Final HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    {'\n    '.join(head_elements)}
</head>
<body>
{body.strip()}
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Generated: {output_file}")


# Run
convert_nh_to_html("index.nh", "index.html")
