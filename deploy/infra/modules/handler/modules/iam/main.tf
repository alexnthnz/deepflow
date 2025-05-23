resource "aws_iam_role" "lambda_exec" {
  name = "AmazonLambdaExecutionRoleForAPI_${var.lambda_function_name}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "aurora_rds_access" {
  name = "AmazonRDSAccessPolicyForAPI_${var.lambda_function_name}"
  role = aws_iam_role.lambda_exec.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["rds:DescribeDBInstances", "rds:DescribeDBClusters"]
        Effect   = "Allow"
        Resource = var.aurora_cluster_arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "elasticache_redis_access" {
  name = "AmazonElastiCacheAccessPolicyForAPI_${var.lambda_function_name}"
  role = aws_iam_role.lambda_exec.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["elasticache:DescribeCacheClusters", "elasticache:DescribeReplicationGroups"]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "s3_access" {
  name = "AmazonS3AccessPolicyForAPI_${var.lambda_function_name}"
  role = aws_iam_role.lambda_exec.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          "${var.file_s3_bucket_arn}/*",
          "${var.file_s3_bucket_arn}"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "secretsmanager_access" {
  name = "AmazonSecretsManagerAccessPolicyForAPI_${var.lambda_function_name}"
  role = aws_iam_role.lambda_exec.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["secretsmanager:GetSecretValue"]
        Effect   = "Allow"
        Resource = var.secret_arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "network_access" {
  name = "AmazonNetworkAccessPolicyForAPI_${var.lambda_function_name}"
  role = aws_iam_role.lambda_exec.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:AttachNetworkInterface",
          "ec2:CreateNetworkInterfaceAttachment",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_access" {
  name = "AmazonBedrockAccessPolicyForAPI_${var.lambda_function_name}"
  role = aws_iam_role.lambda_exec.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Action" : [
          "bedrock:ListFoundationModels"
        ]
        "Effect" : "Allow"
        "Resource" : [
          "*"
        ]
      },
      {
        Action = [
          "bedrock:InvokeModel",
          "bedrock:Converse",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}
