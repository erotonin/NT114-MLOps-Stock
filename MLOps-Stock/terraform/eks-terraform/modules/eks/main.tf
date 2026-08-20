module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "18.31.2"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids
  cluster_endpoint_public_access = true
  create_iam_role = false
  iam_role_arn    = var.iam_role_arn
  enable_irsa = false
  manage_aws_auth_configmap = false

  create_kms_key              = false
  create_cloudwatch_log_group = false
  eks_managed_node_groups = {
    main = {
      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size
      instance_types = var.node_instance_types
      create_iam_role = false
      iam_role_arn    = var.iam_role_arn
    }
  }

  node_security_group_additional_rules = {
    ingress_allow_access_from_control_plane = {
      type                          = "ingress"
      protocol                      = "tcp"
      from_port                     = 9443
      to_port                       = 9443
      source_cluster_security_group = true
      description                   = "Allow access from control plane to webhook port of ALB controller"
    }
    
    ingress_vpc_all = {
      description = "Allow all traffic from VPC"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "ingress"
      cidr_blocks = ["10.0.0.0/16"]
    }

    egress_vpc_all = {
      description = "Allow all outbound traffic to VPC"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "egress"
      cidr_blocks = ["10.0.0.0/16"]
    }
  }

  cluster_addons = {
    coredns    = { most_recent = true }
    kube-proxy = { most_recent = true }
    vpc-cni    = { most_recent = true }
  }
}