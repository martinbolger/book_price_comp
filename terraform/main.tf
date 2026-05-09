# 1. Define the Provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-2" # You can change this to your preferred region
}

# 2. Create the VPC (The Network)
# We use a module here because a "manual" VPC involves 10+ resources.
# This is the "Industry Standard" way to do it.
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "arbitrage-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-2a", "us-east-2b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.10.0/24", "10.0.11.0/24"]

  enable_nat_gateway = true # Necessary if your scraper needs to talk to the internet
  single_nat_gateway = true # Saves money for development
}

# 3. Create the ECR Repository (The Image Storage)
resource "aws_ecr_repository" "app_repo" {
  name                 = "technical-arbitrage-scraper"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true # Good practice to check for vulnerabilities
  }
}

# 4. Outputs
# This prints the important info to your terminal after you run it
output "ecr_repository_url" {
  value = aws_ecr_repository.app_repo.repository_url
}