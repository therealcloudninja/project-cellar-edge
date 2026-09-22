terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-cellar-edge-tfstate"
    storage_account_name = "stcellaredgetfstate"
    container_name        = "tfstate"
    key                   = "dev.terraform.tfstate"
  }
}
