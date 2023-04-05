FROM public.ecr.aws/lambda/python:3.8

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY ./app ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
## For 1-1 matching function, comment out if not using
CMD [ "plagiarism_detector.plagiarism_detector_1ton" ]

## For 1-n matching function, comment out if not using
#CMD [ "plagiarism_detector.plagiarism_detector_1to1" ]

