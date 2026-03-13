# S3 Bucket for Healthcare Data
resource "aws_s3_bucket" "data" {
  bucket = "${var.project_name}-healthcare-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "Healthcare Data Storage"
    DataClass   = "confidential"
    Compliance  = "GDPR-HIPAA"
  }
}

# Enable versioning for data bucket
resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption for data bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access for data bucket
resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for MLflow Artifacts
resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "${var.project_name}-mlflow-artifacts-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "MLflow Artifacts Storage"
  }
}

# Enable versioning for MLflow bucket
resource "aws_s3_bucket_versioning" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption for MLflow bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
