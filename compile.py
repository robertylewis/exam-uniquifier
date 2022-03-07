import sys
import os
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path
import csv

DEFAULT_OUTPUT_DIR = Path("out")
DEFAULT_STUDENTS_CSV = Path("students.csv")
DEFAULT_BODY_TEX = Path("body.tex")
DEFAULT_TEMPLATE_TEX = Path("template.tex")
TMP_DIR = Path("/dev/")

def prompt_yn(base_prompt: str, continue_prompt: str) -> bool:
    print(base_prompt, end=" ")
    while True:
        print(continue_prompt, end=" ")
        response = input().lower().strip()
        if response == "y":
            return True
        elif response == "n":
            return False

def check_output_dir(output_directory: Path) -> bool:
    # Warn if output directory already exists
    if os.path.exists(output_directory):
        return prompt_yn(f"{output_directory} already exists.", "Overwrite (y/n)?")
    return True

def create_output_dir(output_directory: Path):
    # Delete existing directory/file, if present
    if os.path.isdir(output_directory):
        shutil.rmtree(output_directory)
    elif os.path.isfile(output_directory):
        os.remove(output_directory)

    # Create new directory
    os.mkdir(output_directory)

def check_file(file_description: str, file_path: Path, expected_extension: str) -> bool:
    # Ensure file exists
    if not os.path.exists(file_path):
        print(f"{file_description} file does not exist: {file_path}")
        return False

    # Warn if file suffix doesn't match
    if file_path.suffix != expected_extension:
        return prompt_yn(f"{file_description} file ({file_path}) does not have {expected_extension} extension.", "Continue (y/n)?")

    return True

def compile_exams(output_directory: Path, students_csv_path: Path, body_tex_path: Path, template_tex_path: Path):
    # Check provided files exist and warn on incorrect extension
    if not check_file("Students csv", students_csv_path, ".csv"):
        return
    if not check_file("Body LaTeX", body_tex_path, ".tex"):
        return
    if not check_file("Teplate LaTeX", template_tex_path, ".tex"):
        return

    # Check for output directory and warn on overwrite
    if not check_output_dir(output_directory):
        return
    create_output_dir(output_directory)

    # Load the template file into string
    with open(template_tex_path) as template_tex:
        template = template_tex.read()

    # Create temporary directory for running pdflatex, and open csv reader for student data
    with tempfile.TemporaryDirectory() as dirpath, open(students_csv_path, newline="") as students_csv:
        # Create path names
        dirpath = Path(dirpath)
        student_template_tex_path = dirpath / "template.tex"
        student_template_pdf_path = dirpath / "template.pdf"

        # Copy the body.tex file into the temporary directory
        student_body_tex_path = shutil.copy(body_tex_path, dirpath)

        # Read off the header line of csv
        students_csv.readline()

        # Iterate over students in csv file
        for row in csv.reader(students_csv):
            # Read data from row
            (name, banner_id, bit0, bit1, bit2) = row

            # Replace placeholders in template
            student_template = template \
                .replace("##banner_id##", banner_id) \
                .replace("##bit0##", "true" if bit0 == "1" else "false") \
                .replace("##bit1##", "true" if bit1 == "1" else "false") \
                .replace("##bit2##", "true" if bit2 == "1" else "false")

            # Write filled in template to temporary directory
            with open(student_template_tex_path, "w") as f:
                f.write(student_template)

            # Compile the latex into a pdf
            subprocess.run(["pdflatex", student_template_tex_path], cwd=dirpath, check=True, \
                            stdout=subprocess.DEVNULL, \
                            stderr=subprocess.STDOUT)

            # Copy output pdf into out directory
            shutil.copy(student_template_pdf_path, output_directory / f"{banner_id}.pdf")


def main():
    parser = argparse.ArgumentParser(description="Generate distinct exams.")
    parser.add_argument("--output", "-o", dest="output_directory",
                        type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="Directory to place generated pdfs.")
    parser.add_argument("--students", "-s", dest="students_csv",
                        type=Path, default=DEFAULT_STUDENTS_CSV,
                        help="CSV with columns [Name, Banner ID, bit0, bit1, bit2]")
    parser.add_argument("--body", "-b", dest="body_tex",
                        type=Path, default=DEFAULT_BODY_TEX,
                        help="LaTeX file containing body of exam.")
    parser.add_argument("--template", "-t", dest="template_tex",
                        type=Path, default=DEFAULT_TEMPLATE_TEX,
                        help="LaTeX file containing template for customizing exam.")

    args = parser.parse_args()

    compile_exams(args.output_directory, args.students_csv, args.body_tex, args.template_tex)

if __name__ == "__main__":
    main()