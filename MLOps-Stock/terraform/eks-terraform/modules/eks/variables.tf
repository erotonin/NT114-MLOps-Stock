variable "cluster_name" {}
variable "cluster_version" {}
variable "vpc_id" {}
variable "subnet_ids" {}
variable "node_instance_types" {}
variable "node_desired_size" {}
variable "node_min_size" {}
variable "node_max_size" {}
variable "iam_role_arn" {
  type        = string
}