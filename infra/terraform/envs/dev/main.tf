resource "azurerm_resource_group" "main" {
  name     = "rg-cellar-edge-dev"
  location = "eastasia"
  tags = {
    project = "cellar-edge"
    env     = "dev"
    owner   = "henry"
  }
}

module "network" {
  source = "../../modules/network"

  resource_group_name = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  tags                 = azurerm_resource_group.main.tags
}

module "aks" {
  source = "../../modules/aks"

  resource_group_name = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  aks_subnet_id         = module.network.aks_subnet_id
  tags                  = azurerm_resource_group.main.tags
}
