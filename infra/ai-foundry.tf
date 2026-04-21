# Azure AI Foundry Project + OpenAI Deployments
resource "azurerm_cognitive_account" "openai" {
  name                  = "oai-${var.project_name}-${var.environment}"
  resource_group_name   = azurerm_resource_group.sop_rag.name
  location              = azurerm_resource_group.sop_rag.location
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "oai-${var.project_name}-${var.environment}"

  public_network_access_enabled = false

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# GPT-4.1 Deployment
resource "azurerm_cognitive_deployment" "gpt41" {
  name                 = "gpt-41"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4.1"
    version = "2025-04-14"
  }

  sku {
    name     = "Standard"
    capacity = 30
  }
}

# Embedding Model Deployment — text-embedding-3-large
resource "azurerm_cognitive_deployment" "embedding_3_large" {
  name                 = "text-embedding-3-large"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = "1"
  }

  sku {
    name     = "Standard"
    capacity = 30
  }
}

# Legacy Embedding Model (retained for backward compat)
resource "azurerm_cognitive_deployment" "ada002" {
  name                 = "text-embedding-ada-002"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-ada-002"
    version = "2"
  }

  sku {
    name     = "Standard"
    capacity = 30
  }
}

# Private Endpoint for OpenAI
resource "azurerm_private_endpoint" "openai" {
  name                = "pe-oai-${var.project_name}"
  resource_group_name = azurerm_resource_group.sop_rag.name
  location            = azurerm_resource_group.sop_rag.location
  subnet_id           = azurerm_subnet.private_endpoints.id

  private_service_connection {
    name                           = "psc-openai"
    private_connection_resource_id = azurerm_cognitive_account.openai.id
    subresource_names              = ["account"]
    is_manual_connection           = false
  }

  tags = local.tags
}

# Cosmos DB for State and Conversation History
resource "azurerm_cosmosdb_account" "state" {
  name                      = "cosmos-${var.project_name}-${var.environment}"
  resource_group_name       = azurerm_resource_group.sop_rag.name
  location                  = azurerm_resource_group.sop_rag.location
  offer_type                = "Standard"
  kind                      = "GlobalDocumentDB"
  public_network_access_enabled = false

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.sop_rag.location
    failover_priority = 0
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

resource "azurerm_cosmosdb_sql_database" "sop_rag" {
  name                = "sop-rag"
  resource_group_name = azurerm_resource_group.sop_rag.name
  account_name        = azurerm_cosmosdb_account.state.name
}

resource "azurerm_cosmosdb_sql_container" "conversations" {
  name                = "conversations"
  resource_group_name = azurerm_resource_group.sop_rag.name
  account_name        = azurerm_cosmosdb_account.state.name
  database_name       = azurerm_cosmosdb_sql_database.sop_rag.name
  partition_key_paths = ["/conversation_id"]
}

resource "azurerm_cosmosdb_sql_container" "feedback" {
  name                = "feedback"
  resource_group_name = azurerm_resource_group.sop_rag.name
  account_name        = azurerm_cosmosdb_account.state.name
  database_name       = azurerm_cosmosdb_sql_database.sop_rag.name
  partition_key_paths = ["/message_id"]
}
