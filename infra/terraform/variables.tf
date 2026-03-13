variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "healthalliance-mlops"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# RDS variables
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "healthalliance_db"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "healthalliance"
}

variable "db_password" {
  description = "PostgreSQL master password (use a secrets manager in production)"
  type        = string
  sensitive   = true
  default     = "changeme_in_production"
}

# Hybrid cloud variables
variable "on_premise_cidr" {
  description = "CIDR block of the on-premise network (institution data center)"
  type        = string
  default     = "192.168.0.0/16"
}

variable "on_premise_bgp_asn" {
  description = "BGP ASN of the on-premise VPN device"
  type        = number
  default     = 65000
}

variable "on_premise_public_ip" {
  description = "Public IP address of the on-premise VPN device (replace with actual IP)"
  type        = string
  default     = "203.0.113.1"  # RFC 5737 documentation address — replace before apply
}

# Domain / HTTPS variables
variable "domain_name" {
  description = "Registered domain name for the platform (e.g. healthalliance.example.com). Leave empty to skip ACM/Route53."
  type        = string
  default     = ""
}

# Demo cost-optimization flag
variable "demo_mode" {
  description = "When true, uses smallest instance sizes and disables multi-AZ to minimize demo costs"
  type        = bool
  default     = true
}
