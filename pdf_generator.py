from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def generate_pdf(context, output_path):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report_template.html")
    html_out = template.render(context)
    HTML(string=html_out).write_pdf(output_path)
