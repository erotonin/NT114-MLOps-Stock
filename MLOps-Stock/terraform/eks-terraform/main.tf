module "vpc" {
  source       = "./modules/vpc"
  cluster_name = var.cluster_name
  cidr         = var.vpc_cidr
  azs          = var.availability_zones
}

module "eks" {
  source              = "./modules/eks"
  cluster_name        = var.cluster_name
  cluster_version     = var.cluster_version
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnets
  node_instance_types = var.node_instance_types
  node_desired_size   = var.node_desired_size
  node_min_size       = var.node_min_size
  node_max_size       = var.node_max_size
  iam_role_arn        = "arn:aws:iam::${var.aws_account_id}:role/${var.iam_role_name}"
}

module "addons" {
  source       = "./modules/addons"
  cluster_name = module.eks.cluster_name
  vpc_id       = module.vpc.vpc_id
}