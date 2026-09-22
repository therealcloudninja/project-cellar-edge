variable "resource_group_name" {
  type        = string
  description = "Name of the resource group these network resources are created in."
}

variable "location" {
  type        = string
  description = "Azure region for all resources in this module."
}

variable "vnet_address_space" {
  type        = list(string)
  default     = ["10.10.0.0/16"]
  description = "Address space for the VNet."
}

variable "aks_subnet_prefix" {
  type        = string
  default     = "10.10.1.0/24"
  description = "Address prefix for the AKS node subnet. With Azure CNI Overlay, pod IPs come from a separate overlay range, not this subnet — so this only needs to fit node IPs."
}

variable "pe_subnet_prefix" {
  type        = string
  default     = "10.10.2.0/24"
  description = "Address prefix for the private-endpoint subnet (e.g. for a future Storage Account or ACR private endpoint)."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to every resource in this module."
}
