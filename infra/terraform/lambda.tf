# IAM Role for Lambda execution
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "Lambda Execution Role"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

# Inline policy: allow Lambda to read from the healthcare data S3 bucket
resource "aws_iam_role_policy" "lambda_s3_read" {
  name = "${var.project_name}-lambda-s3-read"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.data.arn,
        "${aws_s3_bucket.data.arn}/*"
      ]
    }]
  })
}

# Lambda function: FHIR data processor
# Triggered by S3 ObjectCreated events; validates incoming FHIR R4 records
# and logs validation results to CloudWatch.
resource "aws_lambda_function" "fhir_processor" {
  function_name = "${var.project_name}-fhir-processor"
  role          = aws_iam_role.lambda_execution.arn
  runtime       = "python3.10"
  handler       = "index.handler"
  timeout       = 60
  memory_size   = 256

  # Inline zip: small validation function — no external zip required for demo
  filename         = data.archive_file.fhir_processor_zip.output_path
  source_code_hash = data.archive_file.fhir_processor_zip.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT  = var.environment
      PROJECT_NAME = var.project_name
    }
  }

  tags = {
    Name        = "${var.project_name}-fhir-processor"
    Environment = var.environment
  }
}

# Archive the inline Lambda source code
data "archive_file" "fhir_processor_zip" {
  type        = "zip"
  output_path = "${path.module}/fhir_processor.zip"

  source {
    content  = <<-PYTHON
import json
import boto3
import logging
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REQUIRED_FHIR_FIELDS = ["resourceType", "id", "gender", "birthDate"]

def validate_fhir_record(record):
    return all(field in record for field in REQUIRED_FHIR_FIELDS)

def handler(event, context):
    s3 = boto3.client("s3")
    results = {"processed": 0, "valid": 0, "invalid": 0}

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        logger.info(f"Processing s3://{bucket}/{key}")

        try:
            obj = s3.get_object(Bucket=bucket, Key=key)
            body = obj["Body"].read().decode("utf-8")
            data = json.loads(body)

            records = data if isinstance(data, list) else [data]
            for fhir_record in records:
                results["processed"] += 1
                if validate_fhir_record(fhir_record):
                    results["valid"] += 1
                    logger.info(f"Valid FHIR record: {fhir_record.get('id', 'unknown')}")
                else:
                    results["invalid"] += 1
                    logger.warning(f"Invalid FHIR record missing required fields")

        except Exception as e:
            logger.error(f"Error processing {key}: {str(e)}")
            raise

    logger.info(f"Summary: {results}")
    return {"statusCode": 200, "body": json.dumps(results)}
    PYTHON
    filename = "index.py"
  }
}

# Allow S3 to invoke the Lambda function
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fhir_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data.arn
}

# S3 bucket notification: trigger Lambda on any new .json file in fhir/ prefix
resource "aws_s3_bucket_notification" "fhir_trigger" {
  bucket = aws_s3_bucket.data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.fhir_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "fhir/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.s3_invoke]
}

output "lambda_fhir_processor_arn" {
  description = "ARN of the FHIR data processor Lambda function"
  value       = aws_lambda_function.fhir_processor.arn
}
