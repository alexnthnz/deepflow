from langchain_aws import ChatBedrockConverse

from config.config import config

llm = ChatBedrockConverse(
    model=config.AWS_BEDROCK_MODEL_ID,
    temperature=0,
    max_tokens=None,
    region_name=config.AWS_REGION,
)
