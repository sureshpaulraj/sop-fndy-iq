# Azure AI Search — Hybrid Index for SOP Documents
resource "azurerm_search_service" "sop" {
  name                = "search-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.sop_rag.name
  location            = azurerm_resource_group.sop_rag.location
  sku                 = var.ai_search_sku

  public_network_access_enabled = false

  semantic_search {
    sku = "standard"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# Private Endpoint for AI Search
resource "azurerm_private_endpoint" "search" {
  name                = "pe-search-${var.project_name}"
  resource_group_name = azurerm_resource_group.sop_rag.name
  location            = azurerm_resource_group.sop_rag.location
  subnet_id           = azurerm_subnet.private_endpoints.id

  private_service_connection {
    name                           = "psc-search"
    private_connection_resource_id = azurerm_search_service.sop.id
    subresource_names              = ["searchService"]
    is_manual_connection           = false
  }

  tags = local.tags
}
