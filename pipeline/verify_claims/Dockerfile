FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY handler_verify_claim.py .
COPY verify_llm.py .
COPY firecrawl_client.py .
COPY verify_models.py .

COPY . .

CMD ["handler_verify_claim.handler"]