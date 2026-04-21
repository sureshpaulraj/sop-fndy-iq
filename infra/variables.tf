variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "sop-rag"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
}

variable "ai_search_sku" {
  description = "Azure AI Search SKU"
  type        = string
  default     = "standard"
}

variable "openai_model_version" {
  description = "Azure OpenAI model version"
  type        = string
  default     = "gpt-41"
}

variable "vnet_address_space" {
  description = "VNet address space for AI Landing Zone spoke"
  type        = string
  default     = "10.1.0.0/16"
}
