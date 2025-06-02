# src/inventory/infrastructure/models/estoque_model.py
"""SQLAlchemy model for EstoqueProduto."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.shared.infrastructure.database.connection import Base


class EstoqueModel(Base):
    """SQLAlchemy model for EstoqueProduto entity."""
    
    __tablename__ = "estoque_produtos"
    __table_args__ = {"schema": "inventory"}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    produto_id = Column(PGUUID(as_uuid=True), ForeignKey("inventory.produtos.id"), unique=True, nullable=False, index=True)
    quantidade_atual = Column(Integer, nullable=False, default=0)
    quantidade_reservada = Column(Integer, nullable=False, default=0)
    nivel_minimo = Column(Integer, nullable=False, default=0)
    unidade_medida = Column(String(10), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<EstoqueModel(id={self.id}, produto_id={self.produto_id}, quantidade={self.quantidade_atual})>"
