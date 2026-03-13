# ─────────────────────────────────────────────────────────────────────────────
# ALB Ingress Controller prerequisites, ACM Certificate, Route53
#
# Provisions:
#   1. OIDC identity provider for the EKS cluster (enables IRSA)
#   2. IAM role for the AWS Load Balancer Controller via IRSA
#   3. ACM TLS certificate with Route53 DNS auto-validation (free)
#   4. Route53 DNS records for the app subdomain
#
# Single-apply guarantee
# ──────────────────────
# The dependency chain is encoded entirely inside Terraform's resource graph:
#
#   aws_eks_cluster.main
#        │
#        └─► data.tls_certificate.eks          (deferred: url is "known after apply"
#                 │                              at plan time → Terraform reads this
#                 │                              data source AFTER the cluster exists)
#                 │
#                 └─► aws_iam_openid_connect_provider.eks
#                          │
#                          └─► (locals) oidc_provider_arn / oidc_issuer_host
#                                   │
#                                   └─► aws_iam_role.alb_controller
#
# No -target flags. No manual two-phase apply.
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. TLS certificate of the EKS OIDC endpoint ──────────────────────────────
#
# Why explicit depends_on here:
#   Terraform infers the dependency from `url = aws_eks_cluster.main.identity…`,
#   which defers this data source until after the cluster exists. The explicit
#   depends_on is belt-and-suspenders: it guarantees deferred evaluation even if
#   a future refactor removes the direct attribute reference from `url`.
#
# Why data "tls_certificate" at all (not a hardcoded thumbprint):
#   The SHA-1 thumbprint of the OIDC endpoint's root CA is stable per AWS region
#   but has changed historically. Fetching it dynamically ensures correctness
#   across regions and after any future AWS root CA rotation.
#
data "tls_certificate" "eks_oidc" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer

  # Belt-and-suspenders: forces Terraform to defer this data source until the
  # EKS cluster resource is created, even without the implicit reference above.
  depends_on = [aws_eks_cluster.main]
}

# ── 2. OIDC identity provider ────────────────────────────────────────────────
resource "aws_iam_openid_connect_provider" "eks" {
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks_oidc.certificates[0].sha1_fingerprint]

  tags = {
    Name = "${var.project_name}-eks-oidc-provider"
  }
}

# ── 3. Locals — pre-compute derived values to avoid inline string interpolation
#    with embedded quotes (which causes HCL parse errors in strict mode).
# ─────────────────────────────────────────────────────────────────────────────
locals {
  # Strip "https://" from the OIDC provider URL to build the IAM condition key.
  # e.g. "oidc.eks.eu-central-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E"
  oidc_issuer_host = trimprefix(aws_iam_openid_connect_provider.eks.url, "https://")
}

# ── 4. IAM assume-role policy for the ALB Controller (IRSA) ──────────────────
#
# Uses locals.oidc_issuer_host so there are no quotes-inside-quotes in the
# variable key — the previous version used:
#   "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
# which is an HCL parse error in strict mode.
#
data "aws_iam_policy_document" "alb_controller_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    # Restrict assumption to exactly the ALB controller service account.
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer_host}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    # Additional audience constraint (defence-in-depth).
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer_host}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

# ── 5. IAM role for the ALB Controller ───────────────────────────────────────
resource "aws_iam_role" "alb_controller" {
  name               = "${var.project_name}-alb-controller"
  assume_role_policy = data.aws_iam_policy_document.alb_controller_assume.json

  tags = {
    Name = "${var.project_name}-alb-controller-irsa"
  }
}

# Inline policy from the OFFICIAL AWS Load Balancer Controller v2.7.2 policy.
# Version-locked: do not change the filename to "latest".
# Source: https://github.com/kubernetes-sigs/aws-load-balancer-controller/blob/v2.7.2/docs/install/iam_policy.json
resource "aws_iam_role_policy" "alb_controller" {
  name   = "${var.project_name}-alb-controller-policy"
  role   = aws_iam_role.alb_controller.id
  policy = file("${path.module}/iam_policy_alb_controller_v2.7.2.json")
}

# ── 6. ACM certificate — conditional on var.domain_name being set ─────────────
resource "aws_acm_certificate" "app" {
  count             = var.domain_name != "" ? 1 : 0
  domain_name       = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method = "DNS"

  # Allows replacement certificate to be created before the old one is destroyed,
  # preventing downtime during certificate renewal.
  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-tls-cert"
  }
}

# ── 7. Route53 hosted zone lookup ─────────────────────────────────────────────
data "aws_route53_zone" "main" {
  count        = var.domain_name != "" ? 1 : 0
  name         = var.domain_name
  private_zone = false
}

# ── 8. DNS validation records for ACM ────────────────────────────────────────
#
# for_each note: domain_validation_options is a set whose keys are "(known after
# apply)" during the plan phase because the ACM resource uses count. Terraform
# 1.3+ handles this correctly: it plans the records as "(known after apply)" and
# creates them in the same apply once the certificate exists.
# This is why required_version = ">= 1.3.0" in main.tf is required.
#
resource "aws_route53_record" "cert_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.app[0].domain_validation_options :
    dvo.domain_name => {
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

# Waits until ACM reports the certificate as ISSUED before proceeding.
resource "aws_acm_certificate_validation" "app" {
  count                   = var.domain_name != "" ? 1 : 0
  certificate_arn         = aws_acm_certificate.app[0].arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]

  timeouts {
    create = "10m"
  }
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "alb_controller_role_arn" {
  description = "IAM role ARN for the AWS Load Balancer Controller — pass to Helm via --set serviceAccount.annotations"
  value       = aws_iam_role.alb_controller.arn
}

output "oidc_provider_arn" {
  description = "ARN of the EKS OIDC identity provider (use for additional IRSA roles)"
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN — set in k8s/ingress.yaml alb.ingress.kubernetes.io/certificate-arn annotation"
  value       = var.domain_name != "" ? aws_acm_certificate_validation.app[0].certificate_arn : "not-configured-set-domain_name-variable"
}

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.domain_name != "" ? data.aws_route53_zone.main[0].zone_id : "not-configured-set-domain_name-variable"
}
