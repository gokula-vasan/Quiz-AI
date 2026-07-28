from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.database import get_database
from app.auth.dependencies import get_current_user
from app.models.document import DocumentDB, DocumentResponse
from app.utils.document_parser import parse_pdf
from datetime import datetime
from bson import ObjectId

from app.utils.document_parser import parse_pdf, parse_pptx, parse_docx, parse_txt

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    filename_lower = file.filename.lower()
    allowed_extensions = (".pdf", ".pptx", ".docx", ".txt")
    if not filename_lower.endswith(allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, PPTX, DOCX, and TXT documents are supported."
        )
    
    try:
        file_bytes = await file.read()
        
        if filename_lower.endswith(".pdf"):
            text_content = parse_pdf(file_bytes)
            error_detail = "No text could be extracted from this PDF. Please verify that it contains readable text."
        elif filename_lower.endswith(".pptx"):
            text_content = parse_pptx(file_bytes)
            error_detail = "No text could be extracted from this PowerPoint presentation."
        elif filename_lower.endswith(".docx"):
            text_content = parse_docx(file_bytes)
            error_detail = "No text could be extracted from this Word document."
        else:
            text_content = parse_txt(file_bytes)
            error_detail = "No text content found in this text notes file."

            
        if not text_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
            
        db = get_database()
        
        doc_db = DocumentDB(
            user_id=str(current_user["_id"]),
            filename=file.filename,
            content_type=file.content_type,
            text_content=text_content,
            uploaded_at=datetime.utcnow()
        )
        
        doc_dict = doc_db.model_dump(by_alias=True)
        if doc_dict.get("_id") is None:
            doc_dict.pop("_id", None)
            
        result = await db.documents.insert_one(doc_dict)
        doc_id = str(result.inserted_id)
        
        # Trigger content analysis immediately so concepts are available
        from app.agents.orchestrator import analyze_content_node
        await analyze_content_node({
            "document_text": text_content,
            "document_id": doc_id,
            "user_id": str(current_user["_id"])
        })
        
        # Fetch the updated document with analyzed concepts
        updated_doc = await db.documents.find_one({"_id": result.inserted_id})
        return DocumentResponse.model_validate(updated_doc)
        
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during file upload: {str(e)}"
        )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.documents.find({"user_id": str(current_user["_id"])}).sort("uploaded_at", -1)
    documents = await cursor.to_list(length=100)
    return [DocumentResponse.model_validate(doc) for doc in documents]

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    if not ObjectId.is_valid(doc_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format.")
        
    result = await db.documents.delete_one({
        "_id": ObjectId(doc_id),
        "user_id": str(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )
        
    # Also delete associated quizzes
    await db.quizzes.delete_many({"document_id": doc_id})
    return
