resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-cellar-edge-dev"
  resource_group_name = var.resource_group_name
  location            = var.location
  dns_prefix          = "cellaredge"
  kubernetes_version  = var.kubernetes_version
  tags                = var.tags

  default_node_pool {
    name           = "system"
    node_count     = var.node_count
    vm_size        = var.node_vm_size
    vnet_subnet_id = var.aks_subnet_id
    type           = "VirtualMachineScaleSets"
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
  }
}
