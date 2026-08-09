variable "env_name" {
  description = "Environment name"
  default     = "dev"
}

# # 1. The Schedule (Rate of 1 minute is the standard AWS minimum)
# resource "aws_cloudwatch_event_rule" "every_minute" {
#   name                = "every-minute-rule"
#   schedule_expression = "rate(1 minute)"
# }

# # 2. The Target (Linking Rule to Lambda)
# resource "aws_cloudwatch_event_target" "run_scraper_on_schedule" {
#   rule      = aws_cloudwatch_event_rule.every_minute.name
#   target_id = "book_scraper_function"
#   arn       = aws_lambda_function.book_scraper_function.arn
# }

# # 3. Permission (Allowing the trigger to work)
# resource "aws_lambda_permission" "allow_eventbridge" {
#   statement_id  = "AllowExecutionFromEventBridge"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.book_scraper_function.function_name
#   principal     = "events.amazonaws.com"
#   source_arn    = aws_cloudwatch_event_rule.every_minute.arn
# }

resource "aws_lambda_function" "book_scraper_function" {
  function_name = "book-scraper-${var.env_name}"
  timeout       = 900 # seconds
  image_uri     = "localhost:4566/book-scraper:${var.env_name}"
  package_type  = "Image"

  role = aws_iam_role.book_scraper_function_role.arn

  environment {
    variables = {
      ENVIRONMENT = var.env_name
      SCREENSHOT_BUCKET =aws_s3_bucket.screenshot_bucket.id
    }
  }
}

resource "aws_iam_role" "book_scraper_function_role" {
  name = "book-scraper-${var.env_name}"

  assume_role_policy = jsonencode({
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

# 4. S3 Bucket for Screenshots
resource "aws_s3_bucket" "screenshot_bucket" {
  bucket        = "book-scraper-screenshots-${var.env_name}"
  force_destroy = true # Allows easy cleanup locally
}

# 5. Give Lambda permission to write to S3 & write logs
resource "aws_iam_role_policy" "lambda_s3_and_logs" {
  name = "lambda-s3-and-logs-policy"
  role = aws_iam_role.book_scraper_function_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.screenshot_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}