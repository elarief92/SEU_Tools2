import pandas as pd
import requests
# instructions:
# 1. install pandas and requests
# 2. run the script
# 3. the output will be saved to the output_data.xlsx file
# 4. the input file is the input_data.xlsx file
# 5. the output file is the output_data.xlsx file
# 6. the input file is the input_data.xlsx file

# --- CONFIGURATION ---
INPUT_FILE = "./input_data.xlsx"
OUTPUT_FILE = "./output_data.xlsx"
API_URL = "https://apim-dev.seu.edu.sa/GetExamResult/v2"  


# --- FUNCTION TO CALL API ---
def fetch_exam_data( ssn):
    payload = {
        "NationalID": ssn,
        "ExamCode": "04",
        "ExamSpecialtyCode": "01",
        "InquiryDate": "2023-06-16"
    }
    try:
        response = requests.post(API_URL, json=payload,  timeout=10)
        response.raise_for_status()
        data = response.json()

        result_object = data.get("Envelope", {}) \
                            .get("Body", {}) \
                            .get("GetExamResultResponse", {}) \
                            .get("GetExamResultResult", {}) \
                            .get("getExamResultResponseDetailObject", {})

        exam_date = result_object.get("ExamDate")
        exam_result = result_object.get("ExamResult", {}).get("ExamResult")
        
        return exam_date, exam_result
       
    except Exception as e:
        print(f"API call failed for {ssn}: {e}")
        return None, None

# --- MAIN SCRIPT ---
def process_excel(input_file, output_file):
    df = pd.read_excel(input_file)

    # Ensure required columns exist
    required_cols = ["REQUEST_ID", "NAME", "SSN", "DOB"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    for index, row in df.iterrows():
        name = row["NAME"]
        ssn = row["SSN"]
        dob = row["DOB"]
        request_id = row["REQUEST_ID"]

        exam_date_2, exam_mark_2 = fetch_exam_data(ssn)

        df.at[index, "EXAM_DATE_2"] = exam_date_2
        df.at[index, "EXAM_MARK_2"] = exam_mark_2
        if  ((df.at[index, "EXAM_DATE_1"] != exam_date_2) or (exam_date_2 is None)) \
        or ((df.at[index, "EXAM_MARK_1"] != exam_mark_2) or (exam_mark_2 is None)):
           
            df.at[index, "VALID"] = "NO"
        else:
            df.at[index, "VALID"] = "YES"

    # Save to new Excel file
    df.to_excel(output_file, index=False)
    print(f"Done. Output saved to {output_file}")

# --- RUN ---
if __name__ == "__main__":
    process_excel(INPUT_FILE, OUTPUT_FILE)
