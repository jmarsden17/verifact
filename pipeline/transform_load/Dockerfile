FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY collate_results.py .
COPY summary.py .
COPY summary_models.py .
COPY transform.py .
COPY load.py .
COPY handler_final.py .

COPY . .

CMD ["handler_final.handler"]