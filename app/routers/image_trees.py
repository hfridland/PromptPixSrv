from typing import Annotated
from sqlalchemy.exc import IntegrityError
from fastapi import File, UploadFile
from fastapi.responses import Response

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import TreeHdr, TreeBody, User
from app.dependencies import get_db, get_current_user
from app.schemas.image_trees import TreeResponse, TreeCreate, TreeUpdate

router = APIRouter(
    prefix="/image_trees",
    tags=["image_trees"]
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

MAX_IMAGE_BYTES = 10 * 1024 * 1024

def image_mime(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def find_tree(db: Session, tree_id: int, owner_id: int):
    tree = db.scalar(
        select(TreeHdr).where(
            TreeHdr.id == tree_id,
            TreeHdr.owner_id == owner_id
        )
    )
    if tree is None:
        raise HTTPException(
            status_code=404,
            detail="Tree not found"
        )
    return tree

@router.get("", response_model=list[TreeResponse])
def get_trees(db: DbSession, user: CurrentUser):
    return db.scalars(
        select(TreeHdr)
        .where(TreeHdr.owner_id == user.id)
        .order_by(TreeHdr.id.desc())
    ).all()

@router.get("/{tree_id}", response_model=TreeResponse)
def get_tree(tree_id: int, db: DbSession, user: CurrentUser):
    return find_tree(db, tree_id, user.id)

@router.post(
    "",
    response_model=TreeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_tree(
    data: TreeCreate,
    db: DbSession,
    user: CurrentUser
):
    tree = TreeHdr(
        owner_id=user.id,
        title=data.title
    )
    db.add(tree)
    db.commit()
    db.refresh(tree)
    return tree

@router.patch("/{tree_id}", response_model=TreeResponse)
def update_tree(
    tree_id: int,
    data: TreeUpdate,
    db: DbSession,
    user: CurrentUser
):
    tree = find_tree(db, tree_id, user.id)
    tree.title = data.title
    db.commit()
    db.refresh(tree)
    return tree

def delete_nodes_leaf_first(db: Session, tree_id: int, root_id: int | None = None):
    """Delete a subtree (or the entire tree) without violating the self-FK."""
    nodes = db.scalars(select(TreeBody).where(TreeBody.tree_id == tree_id)).all()
    by_parent = {}
    for node in nodes:
        by_parent.setdefault(node.parent_id, []).append(node.id)
    ids = {node.id for node in nodes}
    if root_id is not None and root_id not in ids:
        raise HTTPException(status_code=404, detail="Node not found")
    visited = set()
    order = []
    def walk(node_id):
        if node_id in visited:
            return
        visited.add(node_id)
        for child_id in by_parent.get(node_id, []):
            walk(child_id)
        order.append(node_id)
    if root_id is None:
        for node in nodes:
            walk(node.id)
    else:
        walk(root_id)
    for node_id in order:
        db.query(TreeBody).filter(TreeBody.tree_id == tree_id, TreeBody.id == node_id).delete(synchronize_session=False)


@router.delete("/{tree_id}", status_code=204)
def delete_tree(tree_id: int, db: DbSession, user: CurrentUser):
    tree = find_tree(db, tree_id, user.id)
    delete_nodes_leaf_first(db, tree_id)
    db.delete(tree)
    db.commit()


@router.delete("/{tree_id}/nodes/{node_id}", status_code=204)
def delete_node(tree_id: int, node_id: int, db: DbSession, user: CurrentUser):
    find_tree(db, tree_id, user.id)
    node = db.scalar(select(TreeBody).where(TreeBody.tree_id == tree_id, TreeBody.id == node_id))
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.parent_id is None:
        raise HTTPException(status_code=409, detail="Delete the entire tree from My Image Trees")
    delete_nodes_leaf_first(db, tree_id, node_id)
    db.commit()


@router.post("/{tree_id}/image", status_code=status.HTTP_201_CREATED)
def upload_root_image(
    tree_id: int,
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    find_tree(db, tree_id, user.id)
    existing = db.scalar(select(TreeBody.id).where(
        TreeBody.tree_id == tree_id, TreeBody.parent_id.is_(None)
    ))
    if existing is not None:
        raise HTTPException(status_code=409, detail="This tree already has an original image")

    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Maximum image size is 10 MB")
    mime = image_mime(data)
    if mime is None:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG and WebP are supported")

    node = TreeBody(tree_id=tree_id, parent_id=None, command=None, ai_model=None, image=data)
    db.add(node)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This tree already has an original image")
    db.refresh(node)
    return {"id": node.id, "tree_id": tree_id, "mime_type": mime}


@router.get("/{tree_id}/image")
def get_root_image(tree_id: int, db: DbSession, user: CurrentUser):
    find_tree(db, tree_id, user.id)
    node = db.scalar(select(TreeBody).where(
        TreeBody.tree_id == tree_id, TreeBody.parent_id.is_(None)
    ))
    if node is None:
        raise HTTPException(status_code=404, detail="No original image")
    mime = image_mime(node.image)
    if mime is None:
        raise HTTPException(status_code=415, detail="Unsupported stored image format")
    return Response(content=node.image, media_type=mime, headers={"Cache-Control": "no-store"})


@router.put("/{tree_id}/image")
def replace_root_image(
    tree_id: int,
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    find_tree(db, tree_id, user.id)
    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Maximum image size is 10 MB")
    mime = image_mime(data)
    if mime is None:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG and WebP are supported")

    node = db.scalar(select(TreeBody).where(
        TreeBody.tree_id == tree_id, TreeBody.parent_id.is_(None)
    ))
    if node is None:
        raise HTTPException(status_code=404, detail="No original image to replace")
    # A root may be replaced only while the tree has no processed nodes.
    # Check every non-root node, not only immediate children.
    descendant_id = db.scalar(
        select(TreeBody.id).where(
            TreeBody.tree_id == tree_id,
            TreeBody.id != node.id
        ).limit(1)
    )
    if descendant_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot replace the original image: this tree contains processed images"
        )

    node.image = data
    db.commit()
    return {"id": node.id, "tree_id": tree_id, "mime_type": mime}


# Tree view endpoints. Child image remains NULL until an AI provider returns a result.
class ChildCreate(BaseModel):
    ai_provider: str = Field(default="OpenAI", min_length=1, max_length=30)
    ai_model: str = Field(min_length=1, max_length=100)
    command: str = Field(min_length=1, max_length=500)


@router.get("/{tree_id}/nodes")
def get_tree_nodes(tree_id: int, db: DbSession, user: CurrentUser):
    find_tree(db, tree_id, user.id)
    nodes = db.scalars(select(TreeBody).where(TreeBody.tree_id == tree_id).order_by(TreeBody.id)).all()
    return [{"id": n.id, "tree_id": n.tree_id, "parent_id": n.parent_id,
             "ai_provider": n.ai_provider, "ai_model": n.ai_model, "command": n.command,
             "has_image": n.image is not None, "generation_status": n.generation_status, "generation_error": n.generation_error} for n in nodes]


@router.get("/{tree_id}/nodes/{node_id}/image")
def get_node_image(tree_id: int, node_id: int, db: DbSession, user: CurrentUser):
    find_tree(db, tree_id, user.id)
    node = db.scalar(select(TreeBody).where(TreeBody.id == node_id, TreeBody.tree_id == tree_id))
    if node is None or node.image is None:
        raise HTTPException(status_code=404, detail="Image not available")
    mime = image_mime(node.image)
    if mime is None:
        raise HTTPException(status_code=415, detail="Unsupported image format")
    return Response(content=node.image, media_type=mime, headers={"Cache-Control": "no-store"})


def generate_child_in_background(tree_id: int, node_id: int, source_image: bytes, command: str, model: str, provider: str):
    """Run in FastAPI's threadpool; use a NEW session, never request-scoped db."""
    import logging
    logger = logging.getLogger(__name__)
    with SessionLocal() as worker_db:
        node = worker_db.get(TreeBody, node_id)
        if node is None or node.tree_id != tree_id or node.generation_status != "pending":
            return
        node.generation_status = "processing"
        worker_db.commit()
    try:
        if provider == "Gemini":
            from app.services.gemini_images import edit_image
        else:
            from app.services.openai_images import edit_image
        output = edit_image(source_image, command, model)
        if len(output) > MAX_IMAGE_BYTES or image_mime(output) is None:
            raise ValueError("Invalid or oversized generated image")
    except Exception:
        logger.exception("Image generation failed for node %s", node_id)
        with SessionLocal() as worker_db:
            node = worker_db.get(TreeBody, node_id)
            if node is not None and node.tree_id == tree_id:
                node.generation_status = "failed"
                node.generation_error = "Generation failed. See server logs."
                worker_db.commit()
        return
    with SessionLocal() as worker_db:
        node = worker_db.get(TreeBody, node_id)
        if node is not None and node.tree_id == tree_id and node.generation_status == "processing":
            node.image = output
            node.generation_status = "completed"
            node.generation_error = None
            worker_db.commit()


@router.post("/{tree_id}/nodes/{parent_id}/children", status_code=202)
def create_child(tree_id: int, parent_id: int, data: ChildCreate, background_tasks: BackgroundTasks, db: DbSession, user: CurrentUser):
    """Persist a pending node and return immediately; image is generated after response."""
    from sqlalchemy import func
    provider = data.ai_provider.strip()
    model = data.ai_model.strip()
    command = data.command.strip()
    if not model or not command:
        raise HTTPException(status_code=422, detail="Model and command cannot be blank")
    supported = {
        "OpenAI": {"gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"},
        "Gemini": {"gemini-2.5-flash-image"},
    }
    if provider not in supported or model not in supported[provider]:
        raise HTTPException(status_code=422, detail="Unsupported provider/model combination")

    # Lock the header to serialize concurrent node creation requests.
    tree = db.scalar(select(TreeHdr).where(TreeHdr.id == tree_id, TreeHdr.owner_id == user.id).with_for_update())
    if tree is None:
        raise HTTPException(status_code=404, detail="Tree not found")
    parent = db.scalar(select(TreeBody).where(TreeBody.id == parent_id, TreeBody.tree_id == tree_id))
    if parent is None:
        raise HTTPException(status_code=404, detail="Parent node not found")
    if parent.image is None or parent.generation_status != "completed":
        raise HTTPException(status_code=409, detail="Parent image is not ready")
    count = db.scalar(select(func.count(TreeBody.id)).where(TreeBody.tree_id == tree_id))
    if count >= 20:
        raise HTTPException(status_code=409, detail="Tree already has 20 nodes")

    source_image = bytes(parent.image)
    node = TreeBody(tree_id=tree_id, parent_id=parent_id, ai_provider=provider, ai_model=model,
                    command=command, image=None, generation_status="pending")
    db.add(node)
    db.commit()
    db.refresh(node)
    background_tasks.add_task(generate_child_in_background, tree_id, node.id, source_image, command, model, provider)
    return {"id": node.id, "tree_id": tree_id, "parent_id": parent_id,
            "ai_provider": provider, "ai_model": model, "command": command, "has_image": False,
            "generation_status": "pending", "generation_error": None}
