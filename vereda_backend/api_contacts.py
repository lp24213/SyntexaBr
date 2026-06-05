"""
API Endpoint: /api/contacts
Recebe e processa formulário de contato da plataforma web
Salva no banco de dados e integra com email service
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database models
Base = declarative_base()

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(String, primary_key=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    empresa = Column(String(255))
    telefone = Column(String(20))
    tipo = Column(String(50), default="geral")
    assunto = Column(String(255), nullable=False)
    mensagem = Column(Text, nullable=False)
    status = Column(String(50), default="novo")
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)

# Pydantic models
class ContactCreate(BaseModel):
    nome: str
    email: EmailStr
    empresa: Optional[str] = None
    telefone: Optional[str] = None
    tipo: str = "geral"
    assunto: str
    mensagem: str

class ContactResponse(BaseModel):
    id: str
    nome: str
    email: str
    status: str
    created_at: datetime

# Database initialization
DATABASE_URL = "postgresql://user:password@localhost/syntexabr"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI Routes (adicione ao seu main.py ou app.py)
def setup_contact_routes(app):
    """
    Setup contact routes para FastAPI app
    Uso: setup_contact_routes(app)
    """
    from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
    from sqlalchemy.orm import Session
    import uuid
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    router = APIRouter(prefix="/api/contacts", tags=["contacts"])
    
    def send_contact_email(contact_data: dict):
        """Background task para enviar email"""
        try:
            sender_email = "noreply@syntexabr.com.br"
            sender_password = os.getenv("EMAIL_PASSWORD")
            recipient_email = "contato@syntexabr.com.br"
            
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[{contact_data['tipo'].upper()}] {contact_data['assunto']}"
            message["From"] = sender_email
            message["To"] = recipient_email
            message["Reply-To"] = contact_data['email']
            
            html_content = f"""
            <html>
              <body>
                <h2>Novo Contato Recebido</h2>
                <table style="width: 100%; border-collapse: collapse;">
                  <tr style="background: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Nome</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{contact_data['nome']}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Email</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{contact_data['email']}</td>
                  </tr>
                  <tr style="background: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Empresa</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{contact_data.get('empresa', 'N/A')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Telefone</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{contact_data.get('telefone', 'N/A')}</td>
                  </tr>
                  <tr style="background: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Tipo</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{contact_data['tipo']}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Assunto</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{contact_data['assunto']}</td>
                  </tr>
                </table>
                <hr />
                <h3>Mensagem:</h3>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
{contact_data['mensagem']}
                </pre>
              </body>
            </html>
            """
            
            part = MIMEText(html_content, "html")
            message.attach(part)
            
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, message.as_string())
                
        except Exception as e:
            print(f"Erro ao enviar email: {str(e)}")
    
    @router.post("/", response_model=ContactResponse)
    async def create_contact(
        contact: ContactCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
    ):
        """Criar novo contato"""
        try:
            contact_id = str(uuid.uuid4())
            
            db_contact = Contact(
                id=contact_id,
                nome=contact.nome,
                email=contact.email,
                empresa=contact.empresa,
                telefone=contact.telefone,
                tipo=contact.tipo,
                assunto=contact.assunto,
                mensagem=contact.mensagem,
                status="novo",
                created_at=datetime.utcnow()
            )
            
            db.add(db_contact)
            db.commit()
            db.refresh(db_contact)
            
            # Enviar email em background
            background_tasks.add_task(
                send_contact_email,
                {
                    "nome": contact.nome,
                    "email": contact.email,
                    "empresa": contact.empresa,
                    "telefone": contact.telefone,
                    "tipo": contact.tipo,
                    "assunto": contact.assunto,
                    "mensagem": contact.mensagem
                }
            )
            
            return ContactResponse(
                id=db_contact.id,
                nome=db_contact.nome,
                email=db_contact.email,
                status=db_contact.status,
                created_at=db_contact.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/{contact_id}", response_model=ContactResponse)
    async def get_contact(contact_id: str, db: Session = Depends(get_db)):
        """Obter contato por ID"""
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contato não encontrado")
        return contact
    
    @router.get("/", response_model=list)
    async def list_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
        """Listar contatos (admin)"""
        contacts = db.query(Contact).offset(skip).limit(limit).all()
        return contacts
    
    app.include_router(router)

# Export para usar em main.py
__all__ = ["setup_contact_routes", "Contact", "ContactCreate", "get_db"]
