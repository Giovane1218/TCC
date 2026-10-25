from pydantic import BaseModel, Field, ConfigDict, EmailStr


class UsuarioRequest(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    email: EmailStr = Field(min_length=3, max_length=80)
    password: str = Field(min_length=12)
    registro_profissional: str = Field(max_length=20)
    cargo: str = Field(max_length=100)
    uf_registro: str = Field(min_length=2, max_length=2)


class UsuarioUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    email: EmailStr = Field(min_length=3, max_length=80)
    registro_profissional: str = Field(max_length=20)
    cargo: str = Field(max_length=100)
    uf_registro: str = Field(min_length=2, max_length=2)
    ativo: bool


class UsuarioResponse(BaseModel):
    username: str
    email: EmailStr
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


class UsuarioDetalhadoResponse(BaseModel):
    username: str
    email: EmailStr
    registro_profissional: str
    cargo: str
    uf_registro: str
    ativo: bool
    nivel_acesso: int

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
