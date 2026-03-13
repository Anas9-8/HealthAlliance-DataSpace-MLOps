terraform {
  # >= 1.3 required: for_each with deferred keys (ACM validation records) and
  # optional() in variable types both require 1.3+.
  required_version = ">= 1.3.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    # Required by data "tls_certificate" in alb.tf.
    # Must be declared here so `terraform init` downloads it.
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
  
  default_tags {
    tags = {
      Project     = "HealthAlliance-DataSpace-MLOps"
      Environment = "dev"
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
