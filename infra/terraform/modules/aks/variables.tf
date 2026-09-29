variable "resource_group_name" {
  type        = string
  description = "Resource group the AKS cluster is created in."
}

variable "location" {
  type        = string
  description = "Azure region for the cluster."
}

variable "aks_subnet_id" {
  type        = string
  description = "ID of the subnet (from the network module) that AKS nodes are placed into."
}

variable "node_vm_size" {
  type        = string
  default     = "Standard_B2s_v2"
  description = "VM size for the system node pool. Chosen on Day 8 after weighing workload needs, vendor guidance, and cost."
}

variable "node_count" {
  type        = number
  default     = 1
  description = "Number of nodes in the system pool. 1 for a dev/demo cluster torn down weekly; increase for any redundancy requirement."
}

variable "kubernetes_version" {
  type        = string
  default     = null
  description = "AKS Kubernetes version. Leave null to let Azure pick its current default stable version."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the cluster."
}
