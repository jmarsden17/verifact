FROM public.ecr.aws/lambda/python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY collate_results.py .
COPY summary.py .
COPY summary_models.py .
COPY transform.py .
COPY load.py .
COPY handler_final.py .

CMD ["handler_final.handler"]