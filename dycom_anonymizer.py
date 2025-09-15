# dicom_anonymizer.py
import os
import shutil
import zipfile
import tempfile
import pydicom
from pydicom.errors import InvalidDicomError
import streamlit as st

# --- Helper Functions ---
def is_dicom(filepath):
    """Check if a file is a valid DICOM file."""
    try:
        pydicom.dcmread(filepath, stop_before_pixels=True)
        return True
    except InvalidDicomError:
        return False
    except Exception:
        return False

def anonymize_file(filepath, savepath, id_number):
    """Anonymize a single DICOM file."""
    try:
        ds = pydicom.dcmread(filepath)
        ds.PatientName = ''
        ds.PatientID = id_number
        ds.PatientBirthDate = ''
        ds.SeriesDate = ''
        ds.StudyID = ''
        ds.save_as(savepath)
    except Exception as e:
        st.error(f"Failed to anonymize {filepath}: {e}")

def process_folder(input_folder, output_folder):
    """Process all files in folder, anonymize DICOM files."""
    os.makedirs(output_folder, exist_ok=True)
    for root, _, files in os.walk(input_folder):
        rel_path = os.path.relpath(root, input_folder)
        out_dir = os.path.join(output_folder, rel_path)
        os.makedirs(out_dir, exist_ok=True)
        for file in files:
            in_path = os.path.join(root, file)
            out_path = os.path.join(out_dir, file)
            if is_dicom(in_path):
                shutil.copy2(in_path, out_path)
                anonymize_file(out_path, out_path)
            else:
                shutil.copy2(in_path, out_path)

# --- Streamlit UI ---
st.title("🩺 DICOM Anonymizer")
st.write("Upload a DICOM file or a ZIP of DICOM files, and download an anonymized copy.")

uploaded_file = st.file_uploader("Upload DICOM or ZIP", type=["dcm", "zip"])

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        outdir = os.path.join(tmpdir, "anon")
        os.makedirs(outdir, exist_ok=True)

        if file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(os.path.join(tmpdir, "input"))
            process_folder(os.path.join(tmpdir, "input"), outdir)
        else:
            if is_dicom(file_path):
                anonymize_file(file_path, os.path.join(outdir, uploaded_file.name))
            else:
                st.error("Uploaded file is not a valid DICOM.")
                st.stop()

        zip_path = os.path.join(tmpdir, "anonymized.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for root, _, files in os.walk(outdir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, outdir)
                    zf.write(full_path, rel_path)

        with open(zip_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Anonymized Files",
                data=f,
                file_name="anonymized.zip",
                mime="application/zip"
            )

