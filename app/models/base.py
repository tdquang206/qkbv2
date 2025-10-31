from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
# Classname: số ít
# Table name: viết thường

class Drugs(Base):
    __tablename__ = "drugs"
    id = Column(Integer, primary_key=True, index=True)
    drug_sku = Column(String, unique=True, nullable=False)
    drug_name = Column(String, unique=True, nullable=False)
    drug_sell_price = Column(Float)
    drug_purchase_price = Column(Float)
    drug_stock = Column(Integer)
    deleted = Column(Boolean, default=False)

    # backref to see all purchases of this drug
    drugs_purchase_history = relationship("DrugsPurchase", back_populates="drug")
    

class DrugsPurchase(Base):
    __tablename__ = "drugs_purchase"
    id = Column(Integer, primary_key=True, index=True)
    drug_id =  Column(Integer, ForeignKey("drugs.id"))
    drug_purchase_quantities = Column(Integer, nullable=False)
    drug_purchase_subcost = Column(Integer, nullable=False)
    drug_purchase_order_date = Column(DateTime, nullable=False)
    drug_purchase_paid_status=Column(Boolean, nullable=False)
    drug_purchase_paid_date=Column(DateTime, nullable=True)
    drug_purchase_note=Column(String, nullable=True)

    drug = relationship("Drugs", back_populates="drugs_purchase_history")