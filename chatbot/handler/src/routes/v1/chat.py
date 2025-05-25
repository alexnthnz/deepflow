import logging
import uuid
import base64

from fastapi import Depends, status, UploadFile, File, Form, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from typing import Optional, List

from services.agent.graph import Graph
from config.config import config
from config.s3 import upload_to_s3, generate_presigned_url
from repositories.chat import get_chat_repository, ChatRepository
from repositories.message import get_message_repository, MessageRepository
from repositories.file import get_file_repository, FileRepository
from repositories.tag import get_tag_repository, TagRepository
from schemas.requests.chat import ChatCreate, TagCreate
from schemas.responses.chat import ChatInDB, ChatDetailInDB, MessageInDB, TagInDB
from schemas.responses.common import CommonResponse
from database.models import SenderType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=CommonResponse)
async def list_chats(
    chat_repo: ChatRepository = Depends(get_chat_repository),
    limit: int = 50,
    offset: int = 0,
):
    try:
        # Get chats and total count
        chats = chat_repo.get_chats_by_user(limit=limit, offset=offset)
        total_chats = chat_repo.count_chats_by_user()

        # Calculate pagination metadata
        has_next = offset + limit < total_chats
        has_previous = offset > 0
        meta = {
            "pagination": {
                "total": total_chats,
                "limit": limit,
                "offset": offset,
                "current_page": (offset // limit) + 1,
                "total_pages": (total_chats + limit - 1) // limit,
                "has_next": has_next,
                "has_previous": has_previous,
                "next_offset": offset + limit if has_next else None,
                "previous_offset": max(0, offset - limit) if has_previous else None,
            }
        }

        return CommonResponse(
            message="Chats retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=[ChatInDB.from_orm(chat).dict() for chat in chats],
            error=None,
            meta=meta,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve chats",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).dict(),
        )


@router.get("/{chat_id}", response_model=CommonResponse)
async def get_chat(
    chat_id: uuid.UUID,
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    file_repo: FileRepository = Depends(get_file_repository),
    limit: int = 50,
    offset: int = 0,
):
    try:
        db_chat = chat_repo.get_chat_by_id(chat_id)
        if not db_chat:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Chat not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Chat does not exist or belongs to another user",
                ).dict(),
            )

        messages = message_repo.get_messages_by_chat(db_chat)[offset : offset + limit]
        chat_response = ChatDetailInDB.from_orm(db_chat)
        chat_response.messages = []

        for msg in messages:
            message_response = MessageInDB.from_orm(msg)
            if msg.file_id:
                db_file = file_repo.get_file_by_id(msg.file_id)
                if db_file:
                    file_key = db_file.file_url.split(
                        f"{config.AWS_S3_BUCKET}.s3.{config.AWS_REGION_NAME}.amazonaws.com/"
                    )[-1]
                    message_response.file.file_url = generate_presigned_url(
                        file_key, expires_in=3600
                    )
            chat_response.messages.append(message_response)

        return CommonResponse(
            message="Chat details retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=chat_response.dict(),
            error=None,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve chat",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).dict(),
        )


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: uuid.UUID,
    chat_repo: ChatRepository = Depends(get_chat_repository),
):
    try:
        deleted = chat_repo.delete_chat(chat_id)
        if not deleted:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Chat not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Chat does not exist or belongs to another user",
                ).dict(),
            )
        return CommonResponse(
            message="Chat deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
            data=None,
            error=None,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to delete chat",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).dict(),
        )


@router.post(
    "/{chat_id}/messages",
    response_model=CommonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message_auth(
    chat_id: uuid.UUID,
    content: Optional[str] = Form(None, max_length=1000),
    file: Optional[UploadFile] = File(None),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    file_repo: FileRepository = Depends(get_file_repository),
):
    try:
        db_chat = chat_repo.get_chat_by_id(chat_id)
        if not db_chat:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Chat not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Chat does not exist or belongs to another user",
                ).dict(),
            )

        # Handle file upload
        file_id = None
        file_url = None
        if file:
            try:
                file_url = upload_to_s3(file, folder=f"chat_{chat_id}", expires_in=3600)
                db_file = file_repo.create_file(
                    file_url=file_url,
                    file_type=file.content_type,
                    file_size=file.size,
                )
                file_id = db_file.id
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content=CommonResponse(
                        message="File upload failed",
                        status_code=e.status_code,
                        data=None,
                        error=e.detail,
                    ).dict(),
                )

        # Create user message
        db_message = message_repo.create_message(
            chat=db_chat, sender=SenderType.USER, content=content, file_id=file_id
        )

        # Call Agent and Core Services
        if content or file_id:
            try:
                message_repo.create_message(
                    chat=db_chat,
                    sender=SenderType.AGENT,
                    content=content,
                    metadata={"original_content": content},
                )
                message_repo.create_message(
                    chat=db_chat, sender=SenderType.AGENT, content=content
                )
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content=CommonResponse(
                        message="Service call failed",
                        status_code=e.status_code,
                        data=None,
                        error=e.detail,
                    ).dict(),
                )

        return CommonResponse(
            message="Message sent successfully",
            status_code=status.HTTP_201_CREATED,
            data=MessageInDB.from_orm(db_message).dict(),
            error=None,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to send message",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).dict(),
        )


@router.post(
    "/{chat_id}/tags",
    response_model=CommonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_tag(
    chat_id: uuid.UUID,
    tag: TagCreate,
    chat_repo: ChatRepository = Depends(get_chat_repository),
    tag_repo: TagRepository = Depends(get_tag_repository),
):
    try:
        db_chat = chat_repo.get_chat_by_id(chat_id)
        if not db_chat:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Chat not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Chat does not exist or belongs to another user",
                ).dict(),
            )

        db_tag = tag_repo.create_tag(tag.name)
        tag_repo.add_tag_to_chat(chat_id, db_tag.id)
        return CommonResponse(
            message="Tag added to chat successfully",
            status_code=status.HTTP_201_CREATED,
            data=TagInDB.from_orm(db_tag).dict(),
            error=None,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to add tag",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).dict(),
        )


@router.delete(
    "/{chat_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_tag(
    chat_id: uuid.UUID,
    tag_id: uuid.UUID,
    chat_repo: ChatRepository = Depends(get_chat_repository),
    tag_repo: TagRepository = Depends(get_tag_repository),
):
    try:
        db_chat = chat_repo.get_chat_by_id(chat_id)
        if not db_chat:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Chat not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Chat does not exist or belongs to another user",
                ).dict(),
            )

        db_tag = tag_repo.get_tag_by_id(tag_id)
        if not db_tag:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Tag not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Tag does not exist or belongs to another user",
                ).dict(),
            )

        tag_repo.remove_tag_from_chat(chat_id, tag_id)
        return CommonResponse(
            message="Tag removed from chat successfully",
            status_code=status.HTTP_204_NO_CONTENT,
            data=None,
            error=None,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to remove tag",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).dict(),
        )


@router.post(
    "/messages", status_code=status.HTTP_200_OK, tags=["chat"], response_model=None
)
async def send_message(
    content: Optional[str] = Form(None, max_length=3000),
    is_new_chat: Optional[bool] = Form(None),
    session_id: Optional[str] = Form(None),
    attachments: Optional[List[UploadFile]] = File(None),
    chat_repo: ChatRepository = Depends(get_chat_repository),
) -> JSONResponse:
    """
    Handle incoming messages and return the Agent's response.

    Args:
        content (Optional[str]): The user's message, max 3000 characters.
        is_new_chat (Optional[bool]): The new chat flag.
        session_id (Optional[str]): The session ID for existing chats.
        attachments (Optional[List[UploadFile]]): Optional array of file attachments.
        chat_repo (ChatRepository): Dependency to interact with the chat repository.
    Returns:
        JSONResponse: Agent's response as JSON if response_type is 'json'.
    """

    if is_new_chat not in [1, 0, "1", "0", "True", "False", "true", "false", None]:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid is_new_chat value. Use True or False."},
        )

    if is_new_chat is False and not session_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "session_id is required for existing chats."},
        )

    if is_new_chat in [1, "1", "True", True]:
        is_new_chat = True
    elif is_new_chat in [0, "0", "False", False]:
        is_new_chat = False

    if not content and not attachments:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Message content or attachments are required."},
        )

    if is_new_chat is True:
        # Initialize a new chat session
        session_id = str(uuid.uuid4())

    agent = Graph(session_id=session_id)

    try:
        # Process attachments if provided
        attachment_data = []
        if attachments:
            for file in attachments:
                if file:
                    # Read file content
                    content = await file.read()
                    # Convert file content to Base64
                    base64_content = base64.b64encode(content).decode("utf-8")
                    attachment_data.append(
                        {
                            "filename": file.filename,
                            "content_type": file.content_type,
                            "size": len(content),
                            "base64": base64_content,  # Add Base64-encoded content
                        }
                    )

        response, resources, images, title = await agent.get_message(
            content, attachments=attachment_data
        )

        if is_new_chat is True:
            chat_repo.create_chat(title=title, session_id=session_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": response,
                "session_id": session_id,
                "resources": resources,
                "images": images,
                "title": title,
            },
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to process message: {str(e)}"},
        )
