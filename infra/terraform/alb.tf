# ─────────────────────────────────────────────────────────────────────────────
# ALB Ingress Controller, ACM Certificate, Route53
#
# This file provisions:
#   1. OIDC provider for the EKS cluster (required for IRSA)
#   2. IAM role for the AWS Load Balancer Controller (IRSA)
#   3. ACM TLS certificate (DNS-validated via Route53) — FREE
#   4. Route53 hosted zone data + A/CNAME records
#
# Prerequisites:
#   • A registered domain (set var.domain_name)
#   • After terraform apply, run: bash scripts/install_alb_controller.sh
# ─────────────────────────────────────────────────────────────────────────────

# OIDC provider — lets EKS service accounts assume IAM roles (IRSA)
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# IAM Role for AWS Load Balancer Controller (IRSA)
data "aws_iam_policy_document" "alb_controller_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }
  }
}

resource "aws_iam_role" "alb_controller" {
  name               = "${var.project_name}-alb-controller"
  assume_role_policy = data.aws_iam_policy_document.alb_controller_assume.json

  tags = {
    Name = "ALB Controller IRSA Role"
  }
}

# Download the official AWS LBC policy (managed externally, attach inline)
resource "aws_iam_role_policy" "alb_controller" {
  name   = "${var.project_name}-alb-controller-policy"
  role   = aws_iam_role.alb_controller.id
  policy = file("${path.module}/alb_controller_policy.json")
}

# ─── ACM Certificate (free TLS) ───────────────────────────────────────────────
resource "aws_acm_certificate" "app" {
  count             = var.domain_name != "" ? 1 : 0
  domain_name       = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-cert"
  }
}

# ─── Route53 ─────────────────────────────────────────────────────────────────
data "aws_route53_zone" "main" {
  count        = var.domain_name != "" ? 1 : 0
  name         = var.domain_name
  private_zone = false
}

# DNS validation record for ACM certificate
resource "aws_route53_record" "cert_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.app[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main[0].zone_id
}

resource "aws_acm_certificate_validation" "app" {
  count                   = var.domain_name != "" ? 1 : 0
  certificate_arn         = aws_acm_certificate.app[0].arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# ─── Outputs ─────────────────────────────────────────────────────────────────
output "alb_controller_role_arn" {
  description = "IAM role ARN for the AWS Load Balancer Controller (use in Helm values)"
  value       = aws_iam_role.alb_controller.arn
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN — paste into k8s/ingress.yaml annotation"
  value       = var.domain_name != "" ? aws_acm_certificate.app[0].arn : "domain_name variable not set"
}

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.domain_name != "" ? data.aws_route53_zone.main[0].zone_id : "domain_name variable not set"
}
