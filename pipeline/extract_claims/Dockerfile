FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY handler_extract_claims.py .
COPY extract_llm.py .
COPY extract_models.py .
COPY db_connection.py .

COPY . .

CMD ["handler_extract_claims.handler"]