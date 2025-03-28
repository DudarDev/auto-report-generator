from gsheet import get_sheet_data
from gpt_writer import generate_summary
from pdf_generator import create_pdf

if __name__ == "__main__":
    data = get_sheet_data()
    summary = generate_summary(data)
    create_pdf(summary)
    print("📄 Звіт згенеровано!")

