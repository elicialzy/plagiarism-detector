FROM public.ecr.aws/lambda/python:3.8

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./app ${LAMBDA_TASK_ROOT}

## For file upload function, comment out if not using
#CMD [ "plagiarism_detector.file_upload_1ton" ]

## For 1-1 matching function, comment out if not using
#CMD [ "plagiarism_detector.plagiarism_detector_1ton" ]

## For 1-n matching function, comment out if not using
CMD [ "plagiarism_detector.plagiarism_detector_1to1" ]

