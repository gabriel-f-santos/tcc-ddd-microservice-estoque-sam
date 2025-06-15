from src.estoque.domain.value_objects.sku import SKU
from src.estoque.domain.value_objects.unidade_medida import UnidadeMedida
from src.shared.domain.entities.base import AggregateRoot
from src.shared.domain.exceptions.base import ValidationException


class EstoqueProdutoReplication(AggregateRoot):
    """Product aggregate root."""
    
    def __init__(
        self,
        sku: SKU | str,
        nome: str,
        descricao: str,
        categoria: str,
        unidade_medida: UnidadeMedida | str,
        nivel_minimo: int = 0,
        ativo: bool = True,
        id: UUID | None = None
    ):
        super().__init__(id)
        
        # Validate and set SKU
        if isinstance(sku, str):
            sku = SKU(sku)
        self._sku = sku
        
        # Validate and set name
        if not nome or not nome.strip():
            raise ValidationException("Product name cannot be empty")
        self._nome = nome.strip()
        
        # Set description
        self._descricao = descricao.strip() if descricao else ""
        
        # Validate and set category
        if not categoria or not categoria.strip():
            raise ValidationException("Product category cannot be empty")
        self._categoria = categoria.strip()
        
        # Validate and set unit of measure
        if isinstance(unidade_medida, str):
            unidade_medida = UnidadeMedida(unidade_medida)
        self._unidade_medida = unidade_medida
        
        # Validate and set minimum level
        if nivel_minimo < 0:
            raise ValidationException("Minimum level cannot be negative")
        self._nivel_minimo = nivel_minimo
        
        # Set status
        self._ativo = ativo
    
    @property
    def sku(self) -> SKU:
        """Product SKU."""
        return self._sku
    
    @property
    def nome(self) -> str:
        """Product name."""
        return self._nome
    
    @property
    def descricao(self) -> str:
        """Product description."""
        return self._descricao
    
    @property
    def categoria(self) -> str:
        """Product category."""
        return self._categoria
    
    @property
    def unidade_medida(self) -> UnidadeMedida:
        """Product unit of measure."""
        return self._unidade_medida
    
    @property
    def nivel_minimo(self) -> int:
        """Minimum stock level."""
        return self._nivel_minimo
    
    @property
    def ativo(self) -> bool:
        """Product active status."""
        return self._ativo