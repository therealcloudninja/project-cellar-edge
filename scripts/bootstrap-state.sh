#!/usr/bin/env bash
set -euo pipefail

# One-time setup: creates the resource group, storage account, and blob
# container that hold Terraform's remote state. Run once, before any
# `terraform init` in the actual infrastructure code.

LOCATION="eastasia"
STATE_RG="rg-cellar-edge-tfstate"
STORAGE_ACCOUNT="stcellaredgetfstate"
CONTAINER_NAME="tfstate"

TAGS="project=cellar-edge env=dev owner=henry"

echo "Checking storage account name availability..."
AVAILABLE=$(az storage account check-name --name "$STORAGE_ACCOUNT" --query "nameAvailable" -o tsv)

if [ "$AVAILABLE" != "true" ]; then
  echo "ERROR: '$STORAGE_ACCOUNT' is already taken globally (storage account names are unique across ALL of Azure, not just your subscription)."
  echo "Pick a different name — e.g. add a short random suffix — and re-run."
  exit 1
fi

echo "Creating resource group: $STATE_RG"
az group create \
  --name "$STATE_RG" \
  --location "$LOCATION" \
  --tags $TAGS

echo "Creating storage account: $STORAGE_ACCOUNT"
az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$STATE_RG" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --tags $TAGS

echo "Creating blob container: $CONTAINER_NAME"
ACCOUNT_KEY=$(az storage account keys list \
  --resource-group "$STATE_RG" \
  --account-name "$STORAGE_ACCOUNT" \
  --query "[0].value" -o tsv)

az storage container create \
  --name "$CONTAINER_NAME" \
  --account-name "$STORAGE_ACCOUNT" \
  --account-key "$ACCOUNT_KEY"

echo ""
echo "Done. Add this to your Terraform backend.tf:"
echo ""
echo "  resource_group_name  = \"$STATE_RG\""
echo "  storage_account_name = \"$STORAGE_ACCOUNT\""
echo "  container_name       = \"$CONTAINER_NAME\""
echo "  key                  = \"dev.terraform.tfstate\""
