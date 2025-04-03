import zipfile

def zip_reports(file_paths, output_name):
    with zipfile.ZipFile(output_name, 'w') as archive:
        for path in file_paths:
            archive.write(path)
    print(f"[✓] Архів створено: {output_name}")

