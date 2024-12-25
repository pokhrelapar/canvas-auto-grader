Licensed under GNU General Public License v3.0

# Introduction
This is a Python program created to automatically post grades and submission comments from an csv file to Canvas.

This program was created to streamline grades entries and comments for 150+ students for OOP class (Fall 2024). It utlizies the officiall Canvas API to post student's grades and  comments as well as file attachments (if provided).

# API Endpoints

You can find your course id and assignment id from the Canvas link.

 https://uta.instructure.com/courses/<COURSE_ID>/assignments/<ASSIGNMENT_ID>

 A Gradebook export will give you the .csv template needed for the program as well as the CANVAS_USER_ID. CANVAS_USER_ID is different for each student.

Following are the main API end points you will need:

   1. API_BASE_URL =  "https://uta.instructure.com/api/v1"
     
   
   2. SUBMISSSION_URL = API_BASE_URL + "/submissions/<CANVAS_USER_ID>
   
   3. SUBMISSION_FILE_UPLOAD = SUBMISSSION_URL + "/comments/files"

The column file_path can be left empty if an attachment is not required. In this case, the submission will only include the grade and the comments. The data is sent as a form-data payload.

```python

payload = {
              "comment[text_comment]": commentText,
              "submission[posted_grade]": finalGrade,
            }
```   
        
# Features

The program provides detailed logs of each API request. It also provides the total number of submissions posted as well as any failures. Validation is also included to validate the Excel columns for required fields.

# Requirements

1. Canvas Auth Token : Generate New Access Token from Settings. You must have Instructor 
                      privilege.

# Dependencies
    pandas, requests, loguuru

# References

https://canvas.instructure.com/doc/api/

# Usage
 python auto-grader-cse1325
