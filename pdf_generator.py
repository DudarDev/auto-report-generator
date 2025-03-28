from jinja2 import Template
from weasyprint import HTML

def create_pdf(summary):
    with open("templates/report_template.html") as f:
        html_content = Template(f.read()).render(summary=summary)
    HTML(string=html_content).write_pdf("report.pdf")