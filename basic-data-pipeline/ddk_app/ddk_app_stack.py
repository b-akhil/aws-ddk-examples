from typing import Any

from aws_cdk.aws_lambda import Code, LayerVersion
from aws_ddk_core.base import BaseStack
from aws_ddk_core.pipelines import DataPipeline
from aws_ddk_core.resources import S3Factory
from aws_ddk_core.stages import KinesisToS3Stage, SqsToLambdaStage
from constructs import Construct


class DdkApplicationStack(BaseStack):
    def __init__(
        self, scope: Construct, id: str, environment_id: str, **kwargs: Any
    ) -> None:
        super().__init__(scope, id, environment_id, **kwargs)

        # The code that defines your stack goes here. For example:
        ddk_bucket = S3Factory.bucket(
            self,
            "ddk-bucket",
            environment_id,
            event_bridge_enabled=True,
        )

        firehose_s3_stage = KinesisToS3Stage(
            self,
            "ddk-firehose-s3",
            environment_id=environment_id,
            bucket=ddk_bucket,
            data_output_prefix="raw/",
        )
        sqs_lambda_stage = SqsToLambdaStage(
            scope=self,
            id="ddk-sqs-lambda",
            environment_id=environment_id,
            code=Code.from_asset("./lambda"),
            handler="index.lambda_handler",
            layers=[
                LayerVersion.from_layer_version_arn(
                    self,
                    "ddk-lambda-layer-wrangler",
                    f"arn:aws:lambda:{self.region}:336392948345:layer:AWSDataWrangler-Python39:2",
                )
            ]
        )
        ddk_bucket.grant_read_write(sqs_lambda_stage.function)

        (
            DataPipeline(scope=self, id="ddk-pipeline")
            .add_stage(firehose_s3_stage)
            .add_stage(sqs_lambda_stage)
        )
