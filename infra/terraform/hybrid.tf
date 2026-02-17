# Hybrid Cloud Configuration
# Connects the AWS VPC to on-premise infrastructure (DKFZ, UKHD, EMBL data centers)
# where institution-local MinIO/NFS storage resides.
#
# Usage:
#   1. Set on_premise_public_ip to the static IP of your on-premise VPN device
#   2. Set on_premise_cidr to the private CIDR of the on-premise network
#   3. Configure the on-premise router with the aws_vpn_connection tunnel details
#   4. Update DVC remote and MinIO endpoint to point to on-premise storage

# VPN Gateway (AWS side of the hybrid connection)
resource "aws_vpn_gateway" "main" {
  vpc_id          = aws_vpc.main.id
  amazon_side_asn = 64512

  tags = {
    Name        = "${var.project_name}-vpn-gw"
    Environment = var.environment
  }
}

# Customer Gateway (represents the on-premise VPN device)
resource "aws_customer_gateway" "onprem" {
  bgp_asn    = var.on_premise_bgp_asn
  ip_address = var.on_premise_public_ip  # Replace with actual on-premise public IP
  type       = "ipsec.1"

  tags = {
    Name = "${var.project_name}-customer-gw"
  }
}

# VPN Connection (IPSec tunnel between AWS and on-premise)
resource "aws_vpn_connection" "main" {
  vpn_gateway_id      = aws_vpn_gateway.main.id
  customer_gateway_id = aws_customer_gateway.onprem.id
  type                = "ipsec.1"
  static_routes_only  = false  # BGP-based dynamic routing

  tags = {
    Name        = "${var.project_name}-vpn-connection"
    Environment = var.environment
  }
}

# Propagate VPN routes to private route table
resource "aws_vpn_gateway_route_propagation" "private" {
  vpn_gateway_id = aws_vpn_gateway.main.id
  route_table_id = aws_route_table.private.id
}

output "vpn_connection_id" {
  description = "VPN connection ID for hybrid cloud tunnel"
  value       = aws_vpn_connection.main.id
}

output "vpn_tunnel1_address" {
  description = "Outside IP address of VPN tunnel 1 (configure on on-premise router)"
  value       = aws_vpn_connection.main.tunnel1_address
}

output "vpn_tunnel2_address" {
  description = "Outside IP address of VPN tunnel 2 (failover tunnel)"
  value       = aws_vpn_connection.main.tunnel2_address
}
