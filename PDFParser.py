import streamlit as st
import json
import subprocess
import fitz
import matplotlib.pyplot as plt
import tempfile
import os
from PIL import Image
import io
import pandas as pd
# import pyautogui
from subprocess import Popen
import subprocess
import re
from PIL import Image
import pickle

# Use the full page instead of a narrow central column
st.set_page_config(layout="wide")

# st.write(st.session_state["shared"])

st.title("DrillParse - PDF")
st.write("Automate and customized pre-processing of Unstructured Data of Daily Drilling Report (DDR) in a general-manner of extraction from various DDR templates.")

# st.caption("Version Note")
st.caption("Assumption of all DDRs templates across PDF pages are consistent.")
st.divider()

st.subheader("Drilling Report Uploader",divider=True)


def pdf_to_images(file_path):
    pdf = fitz.open(file_path)
    num_pages = pdf.page_count
    images = []

    for page_number in range(num_pages):
        page = pdf.load_page(page_number)
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        images.append(image)

    return images, len(images)+1




# Create a temporary folder to store uploaded files
temp_folder = tempfile.TemporaryDirectory()

# Upload files
uploaded_files = st.file_uploader("Upload PDF file", accept_multiple_files=True)

if st.button("Reset Process"):
            
            # Delete files in the specified path
            input_folder_path = os.path.join("pdfparser", "Input")
            for file_name in os.listdir(input_folder_path):
                file_path = os.path.join(input_folder_path, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")


            # pyautogui.hotkey("ctrl", "F5")

col1,col2 = st.columns(2)

with col1:


    st.subheader("Specify Configuration Files : Local Paths",divider=True)

    input_file_path = st.text_input(r"Input folder path")
    output_file_path = st.text_input(r"Output folder path")
    exe_file_path = st.text_input("PdfParser config folder path")
    bat_file_path = st.text_input("Parser folder path (Folder path for .bat file and json file)")

            

if uploaded_files and input_file_path and output_file_path and exe_file_path and bat_file_path:

    for file in uploaded_files:

        # Check if the file has a PDF extension
        if file.name.lower().endswith('.pdf'):

            # Save the uploaded file to the temporary folder
            file_path = os.path.join(temp_folder.name, file.name)
            with open(file_path, "wb") as f:
                f.write(file.read())

        else:

            st.warning(f"Skipping file: {file.name} (not a PDF). Probably the input paths are inaccurate. Make sure therea is no trailing slash")


        st.divider()

        st.subheader("Parser Configuration",divider=True)
        
        col0 , col1, col2 = st.columns((2,1,1), gap="medium")

        with col0:
            
            # Convert the PDF to JPEG for the first page
            image, max_page_count = pdf_to_images(file_path)

            page_num = st.slider('Select Page Number to Display', 1, max_page_count-1, 1)
                
            # Check if an image is returned
            if image:

                st.image(image[page_num-1], use_column_width=True, width=300,caption=f"Page {page_num} of {file.name}")


            else:
                st.warning(f"Unable to display the first page image for {file.name}")

            # st.divider()
            

        with col1:

            st.markdown("""
            **FInder Selection Info**
            
            - **CellWithMarker:** Keyword of Activity Header
            - **CellBelowMarker:** Keyword (end-limit) of Activity Column
            - **CellBelowMarkerIgnoreEmpty:** Activity Column Number


            """)

            st.divider()


            mode = st.radio("Parser Mode",["Column Marker","Index"])

            # Start Date
            project_name = st.text_input("Project/Company Name")

            date_check = st.checkbox("Date info in table column?")

            if (date_check is False) and (mode == "Column Marker"):
                startmarker_date = st.text_input("Start Date Marker")
                date_finder = st.selectbox("Date Search Method",("CellWithMarker","CellBelowMarker","CellBelowMarkerIgnoreEmpty","FirstNonEmptyCellAfterMarker","CellWithMarkerOrFirstNonEmptyCellAfterMarker","RowsBetweenMarkers"))
                date_format = st.text_input("Date Format",value="dd/MM/yyyy")

            elif (date_check is False) and (mode == "Index"):
                startmarker_date = st.text_input("Start Date Marker")
                date_finder = st.selectbox("Date Search Method",("CellWithMarker","CellBelowMarker","CellBelowMarkerIgnoreEmpty","FirstNonEmptyCellAfterMarker","CellWithMarkerOrFirstNonEmptyCellAfterMarker","RowsBetweenMarkers"))
                date_format = st.text_input("Date Format",value="dd/MM/yyyy")

            elif date_check and (mode == "Column Marker"):
                startmarker_date1 = st.text_input("Start Date Marker")
                date_finder1 = st.selectbox("Date Search Method",("CellBelowMarker","CellWithMarker","CellBelowMarkerIgnoreEmpty","FirstNonEmptyCellAfterMarker","CellWithMarkerOrFirstNonEmptyCellAfterMarker","RowsBetweenMarkers"))
                date_format1 = st.text_input("Date Format",value="dd/MM/yyyy")

            elif date_check and (mode == "Index"):
                
                # date_finder1 = st.selectbox("Date Search Method",("CellBelowMarker","CellWithMarker","CellBelowMarkerIgnoreEmpty","FirstNonEmptyCellAfterMarker","CellWithMarkerOrFirstNonEmptyCellAfterMarker","RowsBetweenMarkers"))
                date_format1 = st.text_input("Date Format")
                date_index = st.text_input("Start Date Index (Integer)")


            # Borehole
            startmarker_borehole = st.text_input("Borehole Marker")
            borehole_finder = st.text_input("Borehole Finder",value="CellWithMarker")

            # DDR Table
            startmarker_table = st.text_input("DDR Table Start Marker")
            endmarker_table = st.text_input("DDR Table End Marker")
            table_finder = st.text_input("Table Finder",value="RowsBetweenMarkers")

        with col2:

            st.markdown("""
            **FInder Selection Info**
            - **FirstNonEmptyCellAfterMarker:** Header box for Date Cell (if any)
            - **CellWithMarkerOrFirstNonEmptyCellAfterMarker:** Keyword of Activity Code Column
            - **RowsBetweenMarkers:** Activity Code Column Number""")      

            st.divider()      

            ### Table columns detail

            if mode == "Column Marker":

                # time column
                startmarker_time = st.text_input("Start Time Marker")
                # time_regex = st.text_input("Start Time Regular Expression (if required)")

                # # Split the input into key and value using ":" as the delimiter
                # key, value = time_regex.split(": ", 1) if ": " in time_regex  else (time_regex , "")

                time_format = st.text_input("Time Format",value="HH:mm")

                # Check if the input is a list
                if isinstance(time_format, list):
                    # Strip each element in the list
                    time_format = [format.strip() for format in time_format]


                # time column
                startmarker_duration = st.text_input("Duration Marker")
                duration_sep = st.text_input("Duration Seperator (Eg: 1.5 hrs --> '.')")

            

                # Phase column
                startmarker_phase = st.text_input("Phase Marker")

                # Task column
                startmarker_task = st.text_input("Task Marker")

                # Activity column
                startmarker_activity = st.text_input("Activity Marker")

                # Code column
                startmarker_code = st.text_input("Code Marker")

                # Multi-line comments column
                startmarker_comment = st.text_input("Comment Marker")

            elif mode == "Index":

                # time column
                starttime_index = 0
                starttime_index = st.text_input("Start Time Index (Integer)")
                

                # time_regex = st.text_input("Start Time Regular Expression (if required)")

                # # Split the input into key and value using ":" as the delimiter
                # key, value = time_regex.split(": ", 1) if ": " in time_regex  else (time_regex , "")

                time_format = st.text_input("Time Format")

                # Split the input into a list
                time_format = [format.strip() for format in time_format.split(',')]

                # time column
                duration_index = 0
                duration_index = st.text_input("Duration Index (Integer)")
                duration_sep = st.text_input("Duration Seperator (Eg: 1.5 hrs --> '.')")

            

                # Phase column
                phase_index = 0
                phase_index = st.text_input("Phase Index (Integer)")
                

                # Task column
                task_index = 0
                task_index = st.text_input("Task Index (Integer)")
                

                # Activity column
                activity_index = 0
                activity_index = st.text_input("Activity Index (Integer)")
                

                # Code column
                code_index = 0
                code_index = st.text_input("Code Index (Integer)")
                

                # Code column
                enddepth_index = 0
                enddepth_index = st.text_input("End Depth Index (Integer)")
                

                # Multi-line comments column
                comment_index = 0
                comment_index = st.text_input("Comment Index (Integer)")
                
                
                
                starttime_index = int(starttime_index)
                duration_index = int(duration_index)
                phase_index = int(phase_index)
                task_index = int(task_index)
                activity_index = int(activity_index)
                code_index = int(code_index)
                enddepth_index = int(enddepth_index)
                comment_index = int(comment_index)
            

        

   

            

        st.divider()

        if 'clicked' not in st.session_state:
            st.session_state.clicked = False
        
        def click_button():
            st.session_state.clicked = True

        st.button("Parse PDF",on_click=click_button)

        if st.session_state.clicked:

            if (date_check is False) and (mode == "Column Marker"):
                # Create a dictionary with user inputs
                json_data = {
                                "InputBlocks": [
                                    {
                                    "Type": "Date",
                                    "Name": "ReportDate",
                                    "StartMarker": startmarker_date,
                                    "SearchMethod": date_finder,
                                    "Formats": [date_format]
                                    },
                                    {
                                    "Type": "Text",
                                    "Name": "BoreholeName",
                                    "StartMarker": startmarker_borehole,
                                    "SearchMethod": borehole_finder
                                    },
                                    {
                                    "Type": "Table",
                                    "Name": "DDR",
                                    "StartMarker": startmarker_table,
                                    "EndMarker": endmarker_table,
                                    "SearchMethod": table_finder,

                                    "TableColumns": [
                                        {
                                        "Name": "StartTime",
                                        "Type": "Time",
                                        "IsKeyColumn": True,
                                        "DefaultValue": "",	
                                        "Formats": time_format,
                                        "StartMarker": startmarker_time,
                                        "AddDayIfZero":True,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Duration",
                                        "Type": "Hours",
                                        "StartMarker": startmarker_duration,
                                        "DecimalSeparator": duration_sep,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Phase",
                                        "Type": "Text",
                                        "StartMarker": startmarker_phase,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Task",
                                        "Type": "Text",
                                        "StartMarker": startmarker_task,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Activity",
                                        "Type": "Text",
                                        "StartMarker": startmarker_activity,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Code",
                                        "Type": "Text",
                                        "StartMarker": startmarker_code,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Comments",
                                        "Type": "Multiline",
                                        "StartMarker": startmarker_comment,
                                        "IsObligatory": True
                                        }
                                    ]
                                    }
                                ],
                                "OutputTable": {
                                    "Columns": [
                                    {
                                        "Name": "BoreholeName",
                                        "HeaderText": "Borehole",
                                        "SourceBlocks": ["BoreholeName"]
                                    },
                                    {
                                        "Name": "DailyCost",
                                        "HeaderText": "Daily Cost",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Phase",
                                        "HeaderText": "Phase",
                                        "SourceBlocks": ["DDR.Phase"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "BoreholeSection",
                                        "HeaderText": "Borehole Section",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "StartDate",
                                        "HeaderText": "Start Time",
                                        "SourceBlocks": ["ReportDate", "DDR.ReportDate"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "EndDate",
                                        "HeaderText": "End Time",
                                        "Format": None,
                                        "SourceBlocks": ["ReportDate", "DDR.StartTime", "DDR.Duration"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Duration",
                                        "HeaderText": "Duration(h)",
                                        "SourceBlocks": ["DDR.Duration"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "StartDepth",
                                        "HeaderText": "Start Depth(m)",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "EndDepth",
                                        "HeaderText": "End Depth(m)",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Code",
                                        "HeaderText": "Operation Code",
                                        "Mode": "Cell"
                                    },
                                            {
                                        "Name": "ActivityCode",
                                        "HeaderText": "Activity Code",
                                        "SourceBlocks": ["DDR.Activity"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "SubCode",
                                        "HeaderText": "Sub Code",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Planned",
                                        "HeaderText": "Planned",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "TimeType",
                                        "HeaderText": "Time Classification",
                                        "Mode": "Cell",
                                        "SourceBlocks": ["DDR.Code"],
                                        "ReplaceValues": {
                                        "^P.*$": "Productive"
                                        },
                                        "DefaultValue": "Non-Productive"		
                                    },
                                    {
                                        "Name": "NPTReason",
                                        "HeaderText": "NPT Reason",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "NPTVendor",
                                        "HeaderText": "NPT Vendor",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Comments",
                                        "HeaderText": "Comments",
                                        "SourceBlocks": ["DDR.Comments"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "TranslatedComments",
                                        "HeaderText": "Translated Comments",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Perforation",
                                        "HeaderText": "Perforation",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "AdditionalCode",
                                        "HeaderText": "Additional Code",
                                        "Mode": "Cell"
                                    }
                                    ]
                                }
                                }
            


            elif date_check and (mode == "Column Marker"):

                # Create a dictionary with user inputs
                json_data = {
                                "InputBlocks": [
                                    
                                    {
                                    "Type": "Text",
                                    "Name": "BoreholeName",
                                    "StartMarker": startmarker_borehole,
                                    "SearchMethod": borehole_finder
                                    },
                                    {
                                    "Type": "Table",
                                    "Name": "DDR",
                                    "StartMarker": startmarker_table,
                                    "EndMarker": endmarker_table,
                                    "SearchMethod": table_finder,

                                    "TableColumns": [
                                        {
                                        "Type": "Date",
                                        "Name": "ReportDate",
                                        "StartMarker": startmarker_date1,
                                        "SearchMethod": date_finder1,
                                        "Formats": [date_format1]
                                        },
                                        {
                                        "Name": "StartTime",
                                        "Type": "Time",
                                        "IsKeyColumn": True,
                                        "DefaultValue": "",	
                                        "Formats": time_format,
                                        "StartMarker": startmarker_time,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Duration",
                                        "Type": "Hours",
                                        "StartMarker": startmarker_duration,
                                        "DecimalSeparator": duration_sep,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Phase",
                                        "Type": "Text",
                                        "StartMarker": startmarker_phase,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Task",
                                        "Type": "Text",
                                        "StartMarker": startmarker_task,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Activity",
                                        "Type": "Text",
                                        "StartMarker": startmarker_activity,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Code",
                                        "Type": "Text",
                                        "StartMarker": startmarker_code,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Comments",
                                        "Type": "Multiline",
                                        "StartMarker": startmarker_comment,
                                        "IsObligatory": True
                                        }
                                    ]
                                    }
                                ],
                                "OutputTable": {
                                    "Columns": [
                                    {
                                        "Name": "BoreholeName",
                                        "HeaderText": "Borehole",
                                        "SourceBlocks": ["BoreholeName"]
                                    },
                                    {
                                        "Name": "DailyCost",
                                        "HeaderText": "Daily Cost",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Phase",
                                        "HeaderText": "Phase",
                                        "SourceBlocks": ["DDR.Phase"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "BoreholeSection",
                                        "HeaderText": "Borehole Section",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "StartDate",
                                        "HeaderText": "Start Time",
                                        "SourceBlocks": ["DDR.ReportDate", "DDR.StartTime"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "EndDate",
                                        "HeaderText": "End Time",
                                        "Format": None,
                                        "SourceBlocks": ["DDR.ReportDate", "DDR.StartTime"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Duration",
                                        "HeaderText": "Duration(h)",
                                        "SourceBlocks": ["DDR.Duration"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "StartDepth",
                                        "HeaderText": "Start Depth(m)",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "EndDepth",
                                        "HeaderText": "End Depth(m)",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Code",
                                        "HeaderText": "Operation Code",
                                        "Mode": "Cell"
                                    },
                                            {
                                        "Name": "ActivityCode",
                                        "HeaderText": "Activity Code",
                                        "SourceBlocks": ["DDR.Activity"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "SubCode",
                                        "HeaderText": "Sub Code",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Planned",
                                        "HeaderText": "Planned",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "TimeType",
                                        "HeaderText": "Time Classification",
                                        "Mode": "Cell",
                                        "SourceBlocks": ["DDR.Code"],
                                        "ReplaceValues": {
                                        "^P.*$": "Productive"
                                        },
                                        "DefaultValue": "Non-Productive"		
                                    },
                                    {
                                        "Name": "NPTReason",
                                        "HeaderText": "NPT Reason",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "NPTVendor",
                                        "HeaderText": "NPT Vendor",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Comments",
                                        "HeaderText": "Comments",
                                        "SourceBlocks": ["DDR.Comments"],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "TranslatedComments",
                                        "HeaderText": "Translated Comments",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Perforation",
                                        "HeaderText": "Perforation",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "AdditionalCode",
                                        "HeaderText": "Additional Code",
                                        "Mode": "Cell"
                                    }
                                    ]
                                }
                                }

            elif (date_check is False) and (mode == "Index"):

                json_data = {
                                "InputBlocks": [
                                    {
                                    "Type": "Date",
                                    "Name": "ReportDate",
                                    "StartMarker": startmarker_date,
                                    "SearchMethod": date_finder,
                                    "Formats": [date_format]
                                    },
                                    {
                                    "Type": "Text",
                                    "Name": "BoreholeName",
                                    "StartMarker": startmarker_borehole,
                                    "SearchMethod": borehole_finder,
                                    "DefaultValue": ""
                                    },
                                    {
                                    "Type": "Table",
                                    "Name": "DDR",
                                    "StartMarker": startmarker_table,
                                    "EndMarker": endmarker_table,
                                    "SearchMethod": table_finder,
                                    "TableColumns": [
                                        {
                                        "Name": "StartTime",
                                        "Type": "Time",
                                        "IsKeyColumn": True,
                                        "DefaultValue": "",
                                        "Formats": time_format,
                                        "AddDayIfZero": True,
                                        "Index": starttime_index,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Duration",
                                        "Type": "Hours",
                                        "Index": duration_index,
                                        "DecimalSeparator": duration_sep,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Phase",
                                        "Type": "Text",
                                        "Index": phase_index,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Task",
                                        "Type": "Multiline",
                                        "Index": task_index,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Activity",
                                        "Type": "Text",
                                        "Index": activity_index,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Code",
                                        "Type": "Text",
                                        "Index": code_index,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "EndDepth",
                                        "Type": "Text",
                                        "Index": enddepth_index,
                                        "IsObligatory": True
                                        },
                                        {
                                        "Name": "Comments",
                                        "Type": "Multiline",
                                        "Index": comment_index,
                                        "IsObligatory": True
                                        }
                                    ]
                                    }
                                ],
                                "OutputTable": {
                                    "Columns": [
                                    {
                                        "Name": "BoreholeName",
                                        "HeaderText": "Borehole",
                                        "SourceBlocks": [
                                        "BoreholeName"
                                        ]
                                    },
                                    {
                                        "Name": "DailyCost",
                                        "HeaderText": "Daily Cost",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Phase",
                                        "HeaderText": "Phase",
                                        "SourceBlocks": [
                                        "DDR.Phase"
                                        ],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "BoreholeSection",
                                        "HeaderText": "Borehole Section",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "StartDate",
                                        "HeaderText": "Start Time",
                                        "SourceBlocks": [
                                        "ReportDate","DDR.StartTime"
                                        ],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "EndDate",
                                        "HeaderText": "End Time",
                                        "SourceBlocks": [
                                        "ReportDate",
                                        "DDR.StartTime",
                                        "DDR.Duration"
                                        ],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Duration",
                                        "HeaderText": "Duration(h)",
                                        "SourceBlocks": [
                                        "DDR.Duration"
                                        ],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "StartDepth",
                                        "HeaderText": "Start Depth(m)",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "EndDepth",
                                        "HeaderText": "End Depth(m)",
                                        "SourceBlocks": [
                                        "DDR.EndDepth"
                                        ],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Code",
                                        "HeaderText": "Operation Code",
                                        "SourceBlocks": [
                                        "DDR.Task"
                                        ],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "ActivityCode",
                                        "HeaderText": "Activity Code",
                                        "SourceBlocks": [
                                        "DDR.Activity"
                                        ],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "SubCode",
                                        "HeaderText": "Sub Code",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Planned",
                                        "HeaderText": "Planned",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "TimeType",
                                        "HeaderText": "Time Classification",
                                        "Mode": "Cell",
                                        "SourceBlocks": [
                                        "DDR.Code"
                                        ],
                                        "ReplaceValues": {
                                        "^P.*$": "Productive"
                                        },
                                        "DefaultValue": "Non-Productive"
                                    },
                                    {
                                        "Name": "NPTReason",
                                        "HeaderText": "NPT Reason",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "NPTVendor",
                                        "HeaderText": "NPT Vendor",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Comments",
                                        "HeaderText": "Comments",
                                        "SourceBlocks": [
                                        "DDR.Comments"
                                        ],
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "TranslatedComments",
                                        "HeaderText": "Translated Comments",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "Perforation",
                                        "HeaderText": "Perforation",
                                        "Mode": "Cell"
                                    },
                                    {
                                        "Name": "AdditionalCode",
                                        "HeaderText": "Additional Code",
                                        "Mode": "Cell"
                                    }
                                    ]
                                }
                                }



            # Convert sets to lists in the JSON data
            def convert_sets_to_lists(obj):
                if isinstance(obj, set):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {key: convert_sets_to_lists(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_sets_to_lists(item) for item in obj]
                else:
                    return obj

            json_data_serializable = convert_sets_to_lists(json_data)

            # Specify the full path for the JSON file
            json_file_path = os.path.join(bat_file_path, f"{project_name}.json")

            # Write to JSON file
            with open(fr"{json_file_path}", "w") as json_file:
                json.dump(json_data_serializable, json_file, indent=2)
            
            

            


            bat_content = f"""{exe_file_path}\PdfParser.exe -s={json_file_path} -i={input_file_path} -o={output_file_path} -p\npause"""


            bat_file_path1 = os.path.join(fr"{bat_file_path}",f"{project_name}.bat")

            with open(bat_file_path1, "w") as bat_file:
                    bat_file.write(bat_content)


            def run_batch_file(file_path):
                Popen(file_path,creationflags=subprocess.CREATE_NEW_CONSOLE)

            run_batch_file(bat_file_path1)

            # subprocess.run([f"pdfparser/PdfParser/Parser/{project_name}.bat"])
                    
            excel_path = os.path.join(output_file_path,"output.xlsx")
            # final_df = pd.read_excel(f"{excel_path}")
            

            # Visualize pdf page bbox
            # Check if the file has a json extension
            for file1 in os.listdir(output_file_path):

                if file1.endswith('.json'):
                    
                    json_output = os.path.join(output_file_path, file1)

                    # Get a list of all files in the directory
                    all_files = os.listdir(input_file_path)

                    # Filter for PDF files
                    pdf_files = [file for file in all_files if file.lower().endswith('.pdf')]

                    pdf_name = pdf_files[0].replace('.json', '.pdf')
                    pdf_path = os.path.join(input_file_path, pdf_name)
                    output_folder = output_file_path
                    

                    print("zahid")

                    
                    # Check if the Excel file exists
                    if os.path.exists(excel_path):
                        try:
                            # Attempt to read the Excel file
                            final_df = pd.read_excel(excel_path)

                            # Continue with your existing code using final_df...
                            st.subheader("Extraction Output Display",divider=True)

                            # Display the DataFrame with highlighting empty cells
                            st.data_editor(final_df,height=900,num_rows="dynamic")

                            st.success("PDF Parsed Successfully !")

                        except Exception as e:
                            st.error(f"An error occurred while reading the Excel file: {e}")
                            st.info("Running viz_bbox.py as a fallback...")

                           

                            # Run viz_bbox.py script
                            subprocess.run(["python", "viz_bbox.py", pdf_path, json_output, output_folder,str(page_num)])

                            # Display the generated image
                            image_path = os.path.join(output_file_path,f"page_{page_num}.jpg")
                            image_path = image_path.replace("\\", "\\\\")  # Replace single backslashes with double backslashes
                            image = Image.open(image_path)

                            st.image(image, caption=f"Page {page_num}")

                    else:
                        st.error(f"The Excel file does not exist: {excel_path}")

                        

                        # Run viz_bbox.py script
                        subprocess.run(["python", "viz_bbox.py", pdf_path, json_output, output_folder,str(page_num)])

                        # Display the generated image
                        image_path = os.path.join(output_file_path,f"page_{page_num}.jpg")
                        # image_path = image_path.replace("\\", "\\\\")  # Replace single backslashes with double backslashes
                        image = Image.open(image_path)

                        st.divider()

                        st.subheader("View Page Bounding Boxes",divider=True)

                        st.image(image, caption=f"Page {page_num}",width=800)
                        
                        






            



            







        



