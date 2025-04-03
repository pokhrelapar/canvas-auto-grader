import os
import pandas as pd
import requests
from loguru import logger
import sys


API_BASE_URL = "https://uta.instructure.com/api/v1"

CSV_FILE = "Grades.csv"  # File with the Canvas User IDs, Grades, and Comments

REQUIRED_COLUMNS = {"user_id", "Grades", "Comments"}

COURSE_ID = 197600  # CSE 1325
ASSIGNMENT_ID = 1746394  # Update for each P01, P02, and so on
ASSIGNMENT_NAME = 'P11'

# Retrieve the access token from the environment variable
ACCESS_TOKEN = os.getenv("CANVAS_AUTH_TOKEN")
if not ACCESS_TOKEN:
    logger.error("The CANVAS_API_ACCESS_TOKEN environment variable is not set.")
    raise ValueError("CANVAS_AUTH_TOKEN environment variable is not set.")
else:
    logger.info("Access token successfully retrieved.")


logger.add(
    "application_logs.log",
    rotation="100 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
)


# Check CSV colums for  'user_id', 'Comments' and 'Grades'


def validateColumnsFromFile(df):
    # Ensure that the CSV file has the required columns
    missingColumns = REQUIRED_COLUMNS - set(df.columns)
    if missingColumns:
        logger.error(f"Missing required columns: {', '.join(missingColumns)}")
        raise ValueError(f"Missing required columns: {', '.join(missingColumns)}")
    logger.info("CSV file contains the required columns.")


def getRequestHeaders():
    """Return the headers required for Canvas API requests."""
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}


def constructSubmisionUrl(userId):
    endpoint = f"/courses/{COURSE_ID}/assignments/{ASSIGNMENT_ID}/submissions/{userId}"
    return f"{API_BASE_URL}{endpoint}"


def validateUserId(df):
    if "user_id" not in df.columns:
        logger.error("Missing 'user_id' column in CSV file.")
        raise ValueError("Missing 'user_id' column in CSV file.")
        

    user_ids = df["user_id"]
    if user_ids.isnull().any():
        missingIndices = user_ids[user_ids.isnull()].index.tolist()
        logger.error(f"Missing user_id(s) at row(s): {missingIndices}")
        raise ValueError(f"Missing user_id(s) at row(s): {missingIndices}")


def uploadFile(userId, filePath):
    """Uploads a file and returns the file ID for attaching to a comment."""

    logger.info(f"Uploading file for User ID {userId}")

    if not os.path.exists(filePath):
        logger.error(f"File does not exist: {filePath}")
        raise FileNotFoundError(f"File does not exist: {filePath}")

    uploadUrl = f"{API_BASE_URL}/courses/{COURSE_ID}/assignments/{ASSIGNMENT_ID}/submissions/{userId}/comments/files"

    #  Initiate the file upload and get the upload URL
    payload = {
        "name": os.path.basename(filePath),
        "size": os.path.getsize(filePath),
        "content_type": "application/pdf",
    }

    try:
        # Initiate the file upload
        uploadResponse = requests.post(
            uploadUrl, data=payload, headers=getRequestHeaders()
        )
        uploadResponse.raise_for_status()
        uploadData = uploadResponse.json()
        logger.info(f"File upload started for {filePath}.")
    except requests.RequestException as e:
        logger.error(f"Faile file upload: {e}")
        raise RuntimeError(f"File upload failed: {str(e)}")

    uploadUrl = uploadData["upload_url"]
    uploadParams = uploadData["upload_params"]

    # Step 2: Upload the file to the upload_url
    try:
        with open(filePath, "rb") as file:
            files = {"file": file}
            uploadResponse = requests.post(uploadUrl, data=uploadParams, files=files)
            uploadResponse.raise_for_status()
        logger.success(f"File {filePath} successfully uploaded.")
    except requests.RequestException as e:
        logger.error(f"Failed to upload file {filePath}: {e}")
        raise RuntimeError(f"File upload failed: {str(e)}")

    # Get file ID from the response
    try:
        fileId = uploadResponse.json().get("id")

        if not fileId:
            logger.error(f"File Id not returned for {filePath}")
            raise ValueError(f"Failed to obtain file ID after upload for {filePath}")
    except ValueError as e:
        logger.error(f"Canot find fileId: {str(e)}")
        raise RuntimeError(f"File id cannot be found: {str(e)}")

    return fileId


def postGradesAndSubmissionComments():
    # Read the csv file to get the name, user_id, grade, comments, and file (if any)

    try:
        df = pd.read_csv(CSV_FILE)

        validateColumnsFromFile(df)
        validateUserId(df)

        numSubmissions = len(df)

        logger.info(f"Number of students to process: {numSubmissions}")
        submissionsPosted = 0

        for index, row in df.iterrows():
            student = row["Student"]
            userId = row["user_id"]  # Canvas Id
            finalGrade = row["Grades"]  # Grade [points, letter grade,excused]
            commentText = row.get("Comments","")  # Comments
            postFlag = row.get("post") # post flag 
            
            if pd.isna(commentText):  # Ensure NaN values are converted to an empty string
                commentText = ""
                
            if postFlag.upper() != "Y":
                logger.info(f"Skipping {student}: {userId} as post flag is 'N'.")
                continue  # Skip posting grades for this student

            
            filePath = row.get("file_path", None)  # Get the file path from the 'path' column

            # Define the API endpoint for each student
            url = constructSubmisionUrl(userId)
            logger.info(f"Setting the API endpoint as: {url}")

            # Form-data payload
            payload = {
                "comment[text_comment]": commentText,
                "submission[posted_grade]": finalGrade,
            }

            # Upload the file if the path is provided
            fileId = None
            if pd.notna(filePath) and os.path.exists(filePath):
                fileId = uploadFile(userId, filePath)
                if fileId:
                    payload["comment[file_ids][]"] = [fileId]
            else:
                if pd.isna(filePath):
                    logger.info(f"No file path provided for {student}, {userId}. Skipping file upload.")
                else:
                    logger.warning(f"No valid file found for {student}, {userId}")

            logger.info(f"Processing student: Name: {student}: UserId: {userId}")

            try:
                # Make the PUT request to api with form-data
                submissionResponse = requests.put(
                    url, data=payload, headers=getRequestHeaders()
                )

                # Check the response for each student
                if submissionResponse.status_code == 200:
                    logger.success(
                        f"Grade and comments posted for {student}: {userId}!"
                    )
                    submissionsPosted += 1

                else:
                    logger.error(
                        f"Failed to post grades and comment for {student}, {userId}. Status Code: {submissionResponse.status_code}"
                    )
                    logger.debug(f"Response: {submissionResponse.text}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {student}: {userId}: {str(e)}")
                logger.debug(f"Failed request URL: {url}")

        logger.info(f"Total submissions posted: {submissionsPosted}")
        logger.error(f"Total submissons failed: {numSubmissions - submissionsPosted}")

    except FileNotFoundError as e:
        logger.error(f"CSV file not found: {str(e)}")
        sys.exit()
    except ValueError as e:
        logger.error(f"Data validation error: {str(e)}")


if __name__ == "__main__":

    logger.info("Starting program...")

    postGradesAndSubmissionComments()

    logger.success(
        f"Submission comments and grades for {ASSIGNMENT_NAME} posted to Canvas!"
    )

    # To do: bulk upload scanned exams
