variable "cluster_name" {}
variable "cidr" { default = "10.0.0.0/16" }
variable "azs" { type = list(string) }