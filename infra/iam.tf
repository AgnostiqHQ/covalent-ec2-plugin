# Copyright 2021 Agnostiq Inc.
#
# This file is part of Covalent.
#
# Licensed under the GNU Affero General Public License 3.0 (the "License").
# A copy of the License may be obtained with this software package or at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html
#
# Use of this file is prohibited except in compliance with the License. Any
# modifications or derivative works of this file must retain this copyright
# notice, and modified files must contain a notice indicating that they have
# been altered from the originals.
#
# Covalent is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
#
# Relief from the License may be granted by purchasing a commercial license.

data "aws_iam_policy_document" "s3_access_document" {
  depends_on = [
    aws_s3_bucket.s3_bucket
  ]

  statement {
    actions = [
      "s3:ListBucket",
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject"
    ]

    resources = [
      "${aws_s3_bucket.s3_bucket[0].arn}",
      "${aws_s3_bucket.s3_bucket[0].arn}/*"
    ]
  }

  count = var.aws_s3_bucket == "" ? 1 : 0
}

resource "aws_iam_policy" "s3_access_policy" {
  depends_on = [
    aws_s3_bucket.s3_bucket
  ]

  name   = "CovalentSvcS3Access"
  path   = "/"
  policy = data.aws_iam_policy_document.s3_access_document[0].json
  count  = var.aws_s3_bucket == "" ? 1 : 0
}

resource "aws_iam_role" "covalent_iam_role" {
  name = "covalent-svc-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    "Terraform" = "true"
  }
}

resource "aws_iam_role_policy_attachment" "s3_iam_policy_attachment" {
  policy_arn = aws_iam_policy.s3_access_policy[0].arn
  role       = aws_iam_role.covalent_iam_role.name
  count      = var.aws_s3_bucket == "" ? 1 : 0
}