module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.cidr

  azs             = var.azs
  private_subnets = [for k, v in var.azs : cidrsubnet(var.cidr, 8, k)]
  public_subnets  = [for k, v in var.azs : cidrsubnet(var.cidr, 8, k + 4)]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true

  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }
}