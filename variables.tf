variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "qr-code-449508"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-central2"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "europe-central2-a"
}

variable "cluster_name" {
  description = "GKE Cluster Name"
  type        = string
  default     = "qr-code-cluster"
}

variable "network_name" {
  description = "VPC Network Name"
  type        = string
  default     = "qr-code-vpc"
}

variable "subnet_name" {
  description = "Subnet Name"
  type        = string
  default     = "qr-code-subnet"
} 