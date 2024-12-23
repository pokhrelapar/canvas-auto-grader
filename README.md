
# Introduction
This is a Python program created to automatically post grades and submission comments from an csv file to Canvas.

This program was created to streamline grades entries and comments for 150+ students. It was tedious and a time consuming to copy/paste grades and comments individually from an Excel sheet to Canvas. It utlizies the officiall Canvas API to post student's grades and  comments as well as file attachments (if provided).

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
        


# Requirements

1. Canvas Auth Token : Generate New Access Token from Settings. You must have Instructor 
                      privilege.

# Dependencies
    pandas, requests, loguuru

#References

https://canvas.instructure.com/doc/api/

#Usage
 python auto-grader-cse1325
